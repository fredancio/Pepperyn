# Pepperyn — Backend MVP (Supabase + Claude)

## 🎯 OBJECTIF

Créer un système :
- analyse financière fiable
- mémoire utilisateur
- amélioration continue

---

## 🧱 STACK

- Supabase (Postgres + Auth)
- Vercel (API routes)
- Claude API (modèle principal)

---

## 🗄️ DATABASE

### users
- id
- email

---

### businesses
- id
- user_id
- name
- industry
- business_model

---

### analyses
- id
- business_id
- date
- revenue
- costs
- margin
- raw_data (json)

---

### insights
- id
- analysis_id
- type (issue | opportunity | trend)
- content
- severity

---

### actions
- id
- business_id
- description
- status

---

### metrics_history
- id
- business_id
- date
- revenue
- costs
- margin

---

## PIPELINE

1. Upload fichier
2. Parsing → JSON structuré
3. Récupération mémoire (historique)
4. Appel Claude
5. Scoring
6. Sauvegarde
7. Retour frontend

---

## 🧠 PROMPT CLAUDE

SYSTEM :

Tu es un expert en finance d’entreprise opérationnelle (Stratégie, budget, repérer et analyser toutes les marges dans le P&L, analyse financière, contrôle de gestion, comptabilité… etc.)
Ton rôle est d’aider à prendre des décisions, pas d’expliquer.
Tu travailles uniquement à partir des données fournies.
Tu n’inventes jamais d’informations.
Si une donnée est manquante ou incertaine, tu le signales explicitement.
Tu dois produire une analyse :
- structurée
- concise
- orientée action
Tu respectes STRICTEMENT le format demandé.

---

USER :

Contexte entreprise :
{industry} / {business_model}

Données actuelles :
{JSON}

Historique :
{previous analyses}

Actions :
{user actions}

Analyse en tenant compte de l’évolution.

---

FORMAT :

# RÉSUMÉ EXÉCUTIF
(max 5 lignes)

# DIAGNOSTIC
- Revenus
- Coûts
- Marges

# PROBLÈMES CRITIQUES
(max 3)

# OPPORTUNITÉS
(max 3)

# PLAN D’ACTION

# SCORES
- Rentabilité
- Risque
- Structure

# DÉCISION

---

## 🧪 SCORING AUTOMATIQUE

Critères :
- clarté
- actionnabilité
- pertinence
- crédibilité

Score moyen :

if < 7 → regenerate

---

## 🧠 MÉMOIRE

À chaque analyse :

- sauvegarder metrics
- sauvegarder insights
- enrichir historique

---

## 🔥 FEATURE CLÉ

Comparaison automatique :

“Votre marge commerciale a diminué de 4% depuis la dernière analyse”

---

## ⚠️ RÈGLES CRITIQUES

- jamais d’hallucination
- toujours basé sur données
- output court

---

## 💣 OBJECTIF PRODUIT

Créer un copilote financier :

- comprend le passé
- analyse le présent
- guide les décisions
