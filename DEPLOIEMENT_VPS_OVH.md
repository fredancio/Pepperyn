# Guide de déploiement Pepperyn — VPS OVH

## ⚡ Remplacement de la maquette existante

Tu as déjà quelque chose en ligne sur le VPS. Voici comment le remplacer proprement **sans casser le DNS ni le SSL déjà en place**.

### 1. Identifier ce qui tourne actuellement

```bash
ssh ubuntu@<IP_VPS>

# Voir les processus actifs
pm2 list            # si l'ancienne app tourne avec pm2
docker ps           # si l'ancienne app tourne en Docker
systemctl list-units --type=service | grep -E "nginx|node|python|gunicorn"
```

### 2. Sauvegarder la config Nginx existante (au cas où)

```bash
sudo cp -r /etc/nginx/sites-available /etc/nginx/sites-available.backup
sudo cp -r /etc/nginx/sites-enabled  /etc/nginx/sites-enabled.backup
```

### 3. Arrêter l'ancienne application

```bash
# Si pm2 :
pm2 stop all && pm2 delete all

# Si Docker Compose (ancienne version) :
cd /chemin/ancienne/app && docker compose down

# Si service systemd :
sudo systemctl stop <nom-du-service>
sudo systemctl disable <nom-du-service>
```

### 4. Déplacer/supprimer l'ancien code

```bash
# Archiver (conseillé) plutôt que supprimer directement
sudo mv /var/www/html /var/www/html.old
# ou
sudo mv /opt/ancienne-app /opt/ancienne-app.backup
```

### 5. Continuer avec l'Étape 3 du guide ci-dessous

Le SSL Let's Encrypt déjà en place sera **réutilisé** — Certbot ne demandera rien si les domaines sont identiques. Si la config Nginx existante couvre déjà `pepperyn.com`, remplace son contenu par celui de l'Étape 5 plutôt que d'en créer un nouveau.

---

## Architecture cible

```
Internet
   │
   ▼
[OVH VPS — pepperyn.com]
   │
   ├── Nginx (port 80/443 — SSL Let's Encrypt gratuit)
   │     ├── pepperyn.com        → Next.js frontend (port 3000)
   │     └── api.pepperyn.com    → FastAPI backend  (port 8000)
   │
   ├── Docker Compose
   │     ├── frontend   (Next.js)
   │     └── backend    (FastAPI + Python)
   │
   └── Supabase (cloud — déjà en place)
```

**Coût mensuel estimé :**
- VPS OVH Starter (2 vCPU / 4 Go RAM) : ~6–7 €/mois — largement suffisant pour la bêta
- SSL Let's Encrypt : gratuit
- Supabase Free tier : gratuit (500 Mo, 50 000 users)
- **Total bêta : ~6–7 €/mois**

---

## Étape 1 — Préparer le VPS OVH

Connecte-toi en SSH à ton VPS :

```bash
ssh ubuntu@<IP_DE_TON_VPS>
```

Installe Docker et Docker Compose :

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Vérification
docker --version
docker compose version
```

Installe Nginx et Certbot :

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

---

## Étape 2 — Configurer le DNS chez OVH

Dans ton espace client OVH → Domaines → pepperyn.com → Zone DNS, ajoute/modifie :

| Type | Sous-domaine | Cible           | TTL  |
|------|--------------|-----------------|------|
| A    | (vide)       | `<IP_VPS>`      | 3600 |
| A    | www          | `<IP_VPS>`      | 3600 |
| A    | api          | `<IP_VPS>`      | 3600 |

> Attends 5–30 minutes que le DNS se propage avant de continuer.

---

## Étape 3 — Déployer le code sur le VPS

Sur ton VPS, clone ou copie le projet :

```bash
mkdir -p /opt/pepperyn
cd /opt/pepperyn

# Option A : depuis GitHub (recommandé)
git clone https://github.com/<ton-repo>/pepperyn.git .

# Option B : copier depuis ton PC local (si pas encore sur GitHub)
# Depuis ton Mac/PC, dans le dossier Pepperyn :
# rsync -avz --exclude node_modules --exclude __pycache__ \
#   ./ ubuntu@<IP_VPS>:/opt/pepperyn/
```

---

## Étape 4 — Créer les fichiers Docker

### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour reportlab et pdfplumber
RUN apt-get update && apt-get install -y \
    gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Les variables d'environnement publiques sont nécessaires au build
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY

RUN npm run build

# ── Image de production ──
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

> **Important** : pour activer le mode `standalone` de Next.js, ajoute ceci dans `frontend/next.config.js` :
> ```js
> /** @type {import('next').NextConfig} */
> const nextConfig = {
>   output: 'standalone',
> }
> module.exports = nextConfig
> ```

### `docker-compose.yml` (à la racine de `/opt/pepperyn`)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: pepperyn-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - JWT_GUEST_SECRET=${JWT_GUEST_SECRET}
      - MAX_FILE_SIZE_MB=5
    env_file:
      - .env

  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: https://api.pepperyn.com
        NEXT_PUBLIC_SUPABASE_URL: ${NEXT_PUBLIC_SUPABASE_URL}
        NEXT_PUBLIC_SUPABASE_ANON_KEY: ${NEXT_PUBLIC_SUPABASE_ANON_KEY}
    container_name: pepperyn-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### `.env` (à la racine, **ne jamais committer ce fichier**)

```env
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Supabase
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJh...   # clé service_role (secrète)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJh...   # clé anon (publique)

# Auth
JWT_GUEST_SECRET=une_chaine_aleatoire_tres_longue_et_secrete
```

> **Ajoute `.env` dans ton `.gitignore`** si ce n'est pas déjà le cas.

---

## Étape 5 — Configurer Nginx

Crée le fichier de configuration :

```bash
sudo nano /etc/nginx/sites-available/pepperyn
```

Contenu :

```nginx
# ── Frontend (pepperyn.com) ──────────────────────────────────────────
server {
    server_name pepperyn.com www.pepperyn.com;
    listen 80;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}

# ── Backend API (api.pepperyn.com) ───────────────────────────────────
server {
    server_name api.pepperyn.com;
    listen 80;

    # Timeout élevé car l'analyse IA peut prendre 90+ secondes
    proxy_read_timeout 180s;
    proxy_connect_timeout 180s;
    proxy_send_timeout 180s;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # CORS — déjà géré par FastAPI, mais par sécurité :
        add_header Access-Control-Allow-Origin "https://pepperyn.com" always;
        add_header Access-Control-Allow-Origin "https://www.pepperyn.com" always;
    }
}
```

Active la config et teste :

```bash
sudo ln -s /etc/nginx/sites-available/pepperyn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Étape 6 — Activer le SSL (HTTPS gratuit)

```bash
sudo certbot --nginx -d pepperyn.com -d www.pepperyn.com -d api.pepperyn.com
```

Certbot modifie automatiquement la config Nginx pour rediriger HTTP → HTTPS et renouvelle le certificat automatiquement tous les 90 jours.

---

## Étape 7 — Lancer Pepperyn

```bash
cd /opt/pepperyn

# Premier lancement (build des images Docker)
docker compose up -d --build

# Vérifier que tout tourne
docker compose ps
docker compose logs -f
```

Pepperyn est maintenant accessible sur **https://pepperyn.com**.

---

## Étape 8 — Mettre à jour Supabase

Dans les paramètres Supabase → Authentication → URL Configuration :

- **Site URL** : `https://pepperyn.com`
- **Redirect URLs** : `https://pepperyn.com/**`

Et dans les variables d'environnement de ton app, s'assurer que `NEXT_PUBLIC_API_URL` pointe bien vers `https://api.pepperyn.com`.

---

## Commandes utiles au quotidien

```bash
# Déployer une nouvelle version
cd /opt/pepperyn
git pull
docker compose up -d --build

# Voir les logs en temps réel
docker compose logs -f backend
docker compose logs -f frontend

# Redémarrer un service
docker compose restart backend

# Arrêter tout
docker compose down
```

---

## Évolution vers Pro et Premium — aucun changement d'architecture requis

L'architecture actuelle est **déjà prête** pour les versions payantes. Voici pourquoi et comment :

### Ce qui est déjà en place
- **Champ `plan`** sur la table `companies` : `free | pro | premium | enterprise`
- **`UsageService`** : limites déjà configurées par plan (3 analyses en free, 30 en pro, illimité en premium)
- **Auth Supabase** : gestion des utilisateurs, emails de confirmation, sessions
- **Architecture modulaire** : ajouter une fonctionnalité = ajouter un service backend + une route

### Ce qu'il faudra ajouter pour le paid

**1. Paiement (Stripe) :**
```
/backend/services/stripe_service.py   ← nouveau
/backend/routers/billing.py           ← nouveau
/frontend/app/billing/page.tsx        ← nouveau
```
Stripe webhook met à jour le champ `plan` dans Supabase automatiquement.

**2. Fonctionnalités Pro/Premium :**
Chaque nouvelle fonctionnalité vérifie simplement le plan :
```python
if plan not in ["pro", "premium", "enterprise"]:
    raise HTTPException(402, "Fonctionnalité réservée au plan Pro")
```
Le frontend masque ou grise les boutons selon le plan, sans toucher à l'infra.

**3. Scalabilité :**
Quand la charge augmente, tu as deux options sans changer le code :
- **VPS plus puissant** chez OVH (upgrade en 1 clic)
- **Répartir** : frontend sur Vercel, backend sur un VPS dédié

### Roadmap technique suggérée

| Phase | Action | Coût infra |
|-------|--------|-----------|
| Bêta (maintenant) | VPS OVH 4 Go | ~7 €/mois |
| Lancement Pro | Ajouter Stripe, upgrade VPS 8 Go | ~15 €/mois |
| Croissance | Séparer frontend (Vercel) + VPS 16 Go | ~30 €/mois |
| Scale | Load balancer OVH + 2 VPS | ~60 €/mois |

---

## Checklist avant mise en ligne

- [ ] DNS OVH configuré (A record → IP VPS)
- [ ] Fichier `.env` rempli avec toutes les clés
- [ ] `next.config.js` avec `output: 'standalone'`
- [ ] `docker compose up -d --build` sans erreur
- [ ] SSL actif (HTTPS vert sur pepperyn.com)
- [ ] Supabase → Site URL mis à jour vers pepperyn.com
- [ ] Migration SQL v4 exécutée dans Supabase (`v4_export_format.sql`)
- [ ] Test de bout en bout : inscription → analyse → export
