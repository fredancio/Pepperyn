# CRM Pepperyn — Setup Aitable

## Ce que tu vas obtenir

Un CRM en temps réel avec deux tables :
- **Users CRM** — une fiche par utilisateur, mise à jour automatiquement
- **Analyses** — une ligne par analyse lancée

Toutes les données arrivent automatiquement depuis Pepperyn, sans aucune action manuelle.

---

## Étape 1 — Récupérer ton token API Aitable

1. Connecte-toi sur [aitable.ai](https://aitable.ai)
2. Clique sur ton avatar (en haut à droite) → **Paramètres développeur** (ou Developer Settings)
3. Crée un nouveau **Personal Access Token**
4. Copie-le — tu en auras besoin pour le `.env`

---

## Étape 2 — Créer l'espace de travail Pepperyn CRM

1. Dans Aitable, crée un nouvel espace (ou utilise un existant)
2. Crée une **base** appelée `Pepperyn CRM`
3. À l'intérieur, crée **2 datasheets** (onglets) :
   - `Users CRM`
   - `Analyses`

---

## Étape 3 — Créer les colonnes de chaque table

### Table `Users CRM`

| Nom de la colonne (exact) | Type Aitable | Notes |
|---------------------------|--------------|-------|
| `Email` | Texte | **Colonne principale** |
| `Prénom` | Texte | |
| `Industrie` | Texte | |
| `Business Model` | Texte | produits / services / mixte / autre |
| `Plan` | Texte | free / pro / premium |
| `Date inscription` | Date/Heure | |
| `Nb analyses` | Nombre | Incrémenté automatiquement |
| `Dernière analyse` | Date/Heure | |
| `Exports utilisés` | Texte | excel / pdf / pptx |
| `Statut` | Texte | Nouveau → Actif |

> ⚠️ Les noms doivent être écrits **exactement comme indiqué** (accents inclus).

### Table `Analyses`

| Nom de la colonne (exact) | Type Aitable | Notes |
|---------------------------|--------------|-------|
| `Email utilisateur` | Texte | **Colonne principale** |
| `Date` | Date/Heure | |
| `Type document` | Texte | COMPTE_RESULTAT, BUDGET... |
| `Score confiance (%)` | Nombre | 0–100 |
| `Nb alertes` | Nombre | |
| `Nb problèmes critiques` | Nombre | |
| `Nb actions plan` | Nombre | |
| `Format export` | Texte | excel / pdf / pptx |
| `Mode analyse` | Texte | quick / complete |
| `Durée (ms)` | Nombre | |
| `Score rentabilité` | Nombre | /10 |
| `Score risque` | Nombre | /10 |
| `Score structure` | Nombre | /10 |

---

## Étape 4 — Récupérer les IDs des datasheets

Pour chaque table, l'ID est visible dans l'URL quand tu l'ouvres :

```
https://aitable.ai/workbench/dst_XXXXXXXXXXXXXXXXXX/...
                              ^^^^^^^^^^^^^^^^^^^
                              C'est ton Datasheet ID (commence par "dst")
```

Note les 2 IDs :
- `Users CRM` → `dst_XXXXXXXX`
- `Analyses`  → `dst_YYYYYYYY`

---

## Étape 5 — Ajouter les variables dans le `.env`

Dans le fichier `.env` de ton backend (sur le VPS, à `/opt/pepperyn/.env`) :

```env
# ── Aitable CRM ──────────────────────────────────────────────────────
AITABLE_API_TOKEN=pat_XXXXXXXXXXXXXXXXXXXXX
AITABLE_USERS_DST_ID=dst_XXXXXXXXXXXXXXXXXX
AITABLE_ANALYSES_DST_ID=dst_YYYYYYYYYYYYYY

# ── Webhook secret (invente une chaîne aléatoire) ────────────────────
WEBHOOK_SECRET=pepperyn_wh_xxxxxxxxxxxxxxxxxx
```

---

## Étape 6 — Configurer le Webhook Supabase (nouveaux users)

Ce webhook appelle Pepperyn quand un nouvel utilisateur s'inscrit, pour créer sa fiche CRM immédiatement.

1. Dans Supabase → **Database** → **Webhooks** → **Create a new webhook**
2. Configure :
   - **Name** : `new-user-to-crm`
   - **Table** : `profiles`
   - **Events** : `INSERT` uniquement
   - **Type** : HTTP Request
   - **URL** : `https://api.pepperyn.com/api/webhooks/new-user`
   - **Method** : `POST`
   - **Headers** : ajoute `x-webhook-secret` = la valeur de ton `WEBHOOK_SECRET`
3. Clique **Confirm**

---

## Étape 7 — Redémarrer le backend

```bash
cd /opt/pepperyn
docker compose restart backend
```

Ou si le backend est lancé en local :
```bash
# Arrêter et relancer uvicorn
```

---

## Vérification

### Test du webhook (depuis ton terminal)

```bash
curl -X POST https://api.pepperyn.com/api/webhooks/new-user \
  -H "Content-Type: application/json" \
  -H "x-webhook-secret: pepperyn_wh_xxxxxxxxxxxxxxxxxx" \
  -d '{
    "type": "INSERT",
    "table": "profiles",
    "record": {
      "email": "test@pepperyn.com",
      "prenom": "Test",
      "industry": "SaaS",
      "business_model": "services",
      "created_at": "2024-01-01T10:00:00Z"
    }
  }'
```

→ Tu dois voir une nouvelle ligne apparaître dans la table `Users CRM` d'Aitable.

### Test via une vraie analyse

Lance une analyse dans Pepperyn — après quelques secondes, une ligne doit apparaître dans `Analyses` et le compteur `Nb analyses` du user doit s'incrémenter.

---

## Vue CRM recommandée dans Aitable

Pour avoir un vrai tableau de bord, crée ces **vues filtrées** dans `Users CRM` :

| Vue | Filtre | Utilité |
|-----|--------|---------|
| **Nouveaux** | Statut = Nouveau | Users récents à contacter |
| **Actifs** | Nb analyses ≥ 1 | Users qui utilisent vraiment le produit |
| **Pro** | Plan = pro | Users payants |
| **Inactifs** | Dernière analyse > 14j | Relance possible |

Et dans `Analyses`, crée un **graphique** (Chart) sur `Date` pour voir l'évolution du volume d'analyses dans le temps.

---

## Architecture du flux de données

```
Nouvel utilisateur s'inscrit
      │
      ▼
Supabase INSERT sur profiles
      │
      ▼ (Database Webhook)
POST /api/webhooks/new-user
      │
      ▼
crm_service.upsert_user()
      │
      ▼
Aitable "Users CRM" — nouvelle fiche

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User lance une analyse
      │
      ▼
Claude analyse le fichier
      │
      ▼
analyze.py → crm_service.log_analysis()
      │
      ├──▶ Aitable "Analyses" — nouvelle ligne
      │
      └──▶ Aitable "Users CRM" — Nb analyses +1
                                  Dernière analyse = now
                                  Statut = Actif
```
