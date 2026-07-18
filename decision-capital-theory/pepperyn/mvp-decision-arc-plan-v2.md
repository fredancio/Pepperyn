# MVP Decision Arc Integration Plan — VERSION 2

**Statut :** EN ATTENTE DE VALIDATION  
**Date :** 2026-07-18  
**Branch :** `release-1/wp4c-commercial-offer-alignment`  
**Auteur :** Plan co-produit F. Anciaux / assistant  

> Ce plan corrige 10 points architecturaux identifiés dans V1.  
> **Aucun code ne sera écrit avant validation explicite.**

---

## Corrections apportées vs V1 (résumé)

| Point | V1 | V2 |
|-------|----|----|
| C1 | Machine à états sans DECISION ni EXECUTION | 7 états préservant S→D→E→C→L |
| C2 | Recommandation confondue avec Décision | Frontière explicite Action ≠ Décision ≠ Exécution |
| C3 | Refuser un lien → ABANDONED | Refuser un lien = link rejeté, arc reste ouvert |
| C4 | Deux chemins de création arc (backend + frontend) | Backend seul crée l'arc, frontend lit le résultat |
| C5 | `except Exception: pass` | Logging structuré + reconstruction par backfill |
| C6 | Pas de classification d'immuabilité | IMMUTABLE / MUTABLE / APPEND-ONLY définis |
| C7 | Modèle mono-ligne pour conséquences multiples | `arc_analysis_links` corrigé pour N conséquences |
| C8 | Causalité implicite | Hiérarchie causale explicite à 5 niveaux |
| C9 | `ArcConsequencePrompt.tsx` manquant du minimum | Liste corrigée : 8 créés + 5 modifiés |
| C10 | Sections partielles | Sections A–G complètes ci-dessous |

---

## Section A — Confirmation architecturale (base de travail validée)

### Pipeline principal (ne sera pas modifié)

```
POST /api/analyze
  └── _stream_analysis_response()
        └── _run_analysis_pipeline()
              ├── parse → anonymize → memory → LLM pipeline → deanonymize
              ├── build_executive_decision_model()   ← override EDM
              ├── _save_to_db()                       ← insère dans `analyses`
              │     decision_kernel JSONB stocké ici (WP5C, immuable)
              └── save_analysis_memory()              ← mémoire financière + comportementale
```

**Règle cardinale :** L'Arc Décisionnel est un système *additif*. Aucune étape du pipeline ci-dessus ne sera modifiée pour lui. L'arc se greffe en hooks post-pipeline, sans jamais bloquer la réponse principale.

### Tables existantes concernées (lecture seule pour l'Arc)

| Table | Usage par l'Arc |
|-------|----------------|
| `analyses` | `origin_analysis_id`, `decision_fingerprint` (lecture) |
| `decision_feedback` | Source de vérité pour la détection d'INTENTION |
| `financial_metrics` | Détection de conséquences candidates |
| `company_profile` | Contexte pour le prompt de learning |

### Points d'injection identifiés

| Moment | Fichier | Action Arc |
|--------|---------|-----------|
| Feedback "planned" | `decision_memory.py` — fin de `save_feedback()` | Créer l'arc (si pas déjà créé) |
| Résultat d'analyse N+1 | `analyze.py` — fin de `_save_to_db()` | Détecter conséquences candidates |
| Confirmation conséquence | Nouvel endpoint `POST /api/arcs/{id}/consequence` | Faire avancer l'arc |
| Validation learning | Nouvel endpoint `POST /api/arcs/{id}/learning` | Fermer l'arc |

---

## Section B — Machine à états corrigée (C1)

### Les 7 états

```
INTENTION           (arc naît ici — "Je vais appliquer")
    │ check-in done / partially_done  OU  bouton "Confirmer ma décision"
    ▼
DECISION            (décision formalisée — decision_confirmed_at écrit, IMMUABLE)
    │ execution_status passe de 'not_started' à autre chose
    ▼
EXECUTION           (actions en cours ou terminées)
    │ Pepperyn détecte un candidat → user confirme le lien
    ▼
CONSEQUENCES_LINKED (au moins 1 lien confirmé par l'utilisateur)
    │ IA génère le learning
    ▼
LEARNING_PROPOSED   (learning proposé, en attente validation)
    │ user valide (confirme ou corrige)
    ▼
CLOSED              (arc scellé — RIEN ne peut plus changer)

Depuis tout état sauf CLOSED → ABANDONED (sur action explicite de l'utilisateur)
```

### Règles de transition

**INTENTION → DECISION**  
Déclencheur : le check-in (RecommendationCheckIn) retourne `done` ou `partially_done`,  
OU l'utilisateur clique un bouton "Confirmer cette décision" futur.  
Action : écrire `decision_confirmed_at = now()`. Ce champ devient immuable.

**DECISION → EXECUTION** (peut être simultané avec le précédent)  
Déclencheur : `execution_status != 'not_started'`.  
Pour MVP : la transition INTENTION→DECISION et DECISION→EXECUTION peuvent être franchies en un seul geste utilisateur (check-in "done" = décidé + exécuté).  
La distinction conceptuelle est préservée dans les données (`decision_confirmed_at` ≠ `execution_updated_at`), même si l'UX les compresse.

**EXECUTION → CONSEQUENCES_LINKED**  
Déclencheur : l'utilisateur confirme un `arc_analysis_links` en `link_status = 'confirmed'`.  
Condition : au moins 1 lien confirmé doit exister.  
Note : des liens peuvent être *rejetés* sans changer l'état de l'arc (cf. C3 ci-dessous).

**CONSEQUENCES_LINKED → LEARNING_PROPOSED**  
Déclencheur : `arc_service.propose_learning()` appelé automatiquement post-confirmation du lien.

**LEARNING_PROPOSED → CLOSED**  
Déclencheur : `POST /api/arcs/{id}/learning` avec `{"action": "validate"}`.  
Action : écrire `closed_at = now()`, `status = 'closed'`.  
RIEN ne peut modifier l'arc après cela. Le trigger Supabase bloque toute UPDATE sur arc CLOSED.

**Tout état → ABANDONED**  
Déclencheur : action explicite utilisateur.  
`abandoned_at` et `abandoned_reason` sont écrits. Irréversible.

### Ce que la machine à états préserve de la DCT

| DCT | État Arc | Champ de preuve |
|-----|----------|----------------|
| S — Situation | implicite | `origin_analysis_id` |
| D — Décision | DECISION | `decision_confirmed_at`, `decision_text` |
| E — Exécution | EXECUTION | `execution_status`, `execution_notes` |
| C — Conséquences | CONSEQUENCES_LINKED | `arc_analysis_links` (liens confirmés) |
| L — Learning | CLOSED | `learning_text`, `learning_confirmed` |

---

## Section C — Schéma base de données corrigé (C6, C7, C8)

### Table principale : `decision_arcs`

```sql
CREATE TABLE public.decision_arcs (
  id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- ── CONTEXTE (IMMUTABLE) ────────────────────────────────────────────────
  company_id              UUID REFERENCES companies(id)  ON DELETE CASCADE NOT NULL,
  entity_id               UUID REFERENCES entities(id)   ON DELETE SET NULL,

  -- ── ORIGINE (IMMUTABLE après création) ──────────────────────────────────
  -- Lien vers l'analyse qui a produit la recommandation à l'origine de l'arc
  origin_analysis_id      UUID REFERENCES analyses(id)   ON DELETE SET NULL NOT NULL,
  decision_fingerprint    TEXT NOT NULL,
  -- Lien logique (non FK) vers decision_feedback.recommendation_id
  recommendation_id       TEXT NOT NULL,
  decision_source         TEXT NOT NULL  -- 'plan_action_haute' | 'plan_action'
    CHECK (decision_source IN ('plan_action_haute', 'plan_action')),
  decision_index          INTEGER NOT NULL,
  -- Contrainte d'idempotence : un seul arc par (analyse, recommandation)
  UNIQUE (origin_analysis_id, recommendation_id),

  -- ── DÉCISION (IMMUTABLE une fois le statut 'decision' atteint) ──────────
  decision_text           TEXT NOT NULL,    -- texte de la recommandation d'origine
  decision_notes          TEXT,             -- formulation propre à l'utilisateur
  decision_confirmed_at   TIMESTAMPTZ,      -- NULL tant qu'en INTENTION

  -- ── ÉTAT (forward-only, sauf vers ABANDONED) ────────────────────────────
  status                  TEXT NOT NULL DEFAULT 'intention'
    CHECK (status IN (
      'intention', 'decision', 'execution',
      'consequences_linked', 'learning_proposed', 'closed', 'abandoned'
    )),

  -- ── EXÉCUTION (MUTABLE jusqu'à CONSEQUENCES_LINKED) ────────────────────
  execution_status        TEXT NOT NULL DEFAULT 'not_started'
    CHECK (execution_status IN ('not_started', 'in_progress', 'partial', 'complete')),
  execution_notes         TEXT,
  execution_updated_at    TIMESTAMPTZ,

  -- ── LEARNING (MUTABLE jusqu'à CLOSED) ──────────────────────────────────
  learning_text           TEXT,
  learning_confirmed      BOOLEAN NOT NULL DEFAULT FALSE,
  learning_modified       BOOLEAN NOT NULL DEFAULT FALSE,  -- user a corrigé le texte IA

  -- ── TIMESTAMPS ──────────────────────────────────────────────────────────
  created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at               TIMESTAMPTZ,     -- immuable une fois écrit
  abandoned_at            TIMESTAMPTZ,
  abandoned_reason        TEXT
);
```

### Table des liens : `arc_analysis_links` (C7 — conséquences multiples)

```sql
CREATE TABLE public.arc_analysis_links (
  id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  arc_id                  UUID REFERENCES decision_arcs(id) ON DELETE CASCADE NOT NULL,
  analysis_id             UUID REFERENCES analyses(id)      ON DELETE CASCADE NOT NULL,

  -- ── TYPE ET STATUT ──────────────────────────────────────────────────────
  link_type               TEXT NOT NULL
    CHECK (link_type IN ('origin', 'consequence_candidate', 'consequence_confirmed',
                         'consequence_rejected', 'context')),

  -- ── CAUSALITÉ (C8) ──────────────────────────────────────────────────────
  -- Pepperyn ne peut affirmer QUE des associations temporelles ou corrélations.
  -- "causé par" est hors périmètre MVP. Le texte ci-dessous l'explicite.
  link_hypothesis         TEXT,   -- "Observé après votre décision de X — évolution Y"
  -- Ce champ contient JAMAIS "a causé" — seulement "est survenu après" / "est corrélé à"

  -- ── CONFIRMATION UTILISATEUR ────────────────────────────────────────────
  -- NULL = en attente de review | TRUE = confirmé | FALSE = rejeté
  confirmed_by_user       BOOLEAN,
  user_rejection_reason   TEXT,    -- optionnel, libre

  -- ── TIMESTAMPS ──────────────────────────────────────────────────────────
  linked_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at             TIMESTAMPTZ,

  -- Un arc ne peut avoir qu'un seul lien par analyse (origin OU consequence)
  UNIQUE (arc_id, analysis_id)
);
```

### Classification d'immuabilité (C6)

| Champ | Règle | Raison |
|-------|-------|--------|
| `origin_analysis_id` | **IMMUTABLE** | Contexte de naissance de l'arc |
| `decision_fingerprint` | **IMMUTABLE** | Empreinte de la situation |
| `recommendation_id` | **IMMUTABLE** | Lien vers la source |
| `decision_source`, `decision_index` | **IMMUTABLE** | Position dans le plan |
| `created_at` | **IMMUTABLE** | Audit trail |
| `decision_text` | **IMMUTABLE dès `decision` atteint** | La décision ne peut pas être réécrite rétrospectivement |
| `decision_confirmed_at` | **IMMUTABLE une fois écrit** | Horodatage décisionnel (DCT INV-2) |
| `closed_at` | **IMMUTABLE une fois écrit** | Fermeture définitive |
| `decision_notes` | **MUTABLE jusqu'à `decision`** | L'utilisateur peut reformuler |
| `execution_status` | **MUTABLE jusqu'à `consequences_linked`** | L'exécution peut évoluer |
| `execution_notes` | **MUTABLE jusqu'à `consequences_linked`** | Notes libres |
| `learning_text` | **MUTABLE jusqu'à `closed`** | L'utilisateur peut corriger |
| `status` | **Forward-only** (sauf ABANDONED) | DCT INV-3 : monotonicité |
| `arc_analysis_links` (confirmed) | **APPEND-ONLY** | Un lien confirmé ne disparaît pas |
| Tout champ après `closed` | **SEALED — aucune UPDATE** | Arc fermé = Capital figé |

**Implémentation de l'immuabilité :** trigger Postgres `before update` sur `decision_arcs` bloquant toute modification si `status = 'closed'`. Pas besoin de RLS côté application.

---

## Section D — Source de vérité unique pour la création d'arc (C4)

### Le problème V1

V1 proposait deux chemins parallèles :
1. `decision_memory.py` crée l'arc côté backend
2. `FeedbackCard.tsx` appelle `createArc()` côté frontend

Ces deux chemins créaient une race condition et une responsabilité floue.

### La règle V2 : **Backend seul, frontend lit**

```
FeedbackCard.tsx
  └── PUT /api/decision-memory/feedback  { recommendation_id, status: "planned", ... }
        └── decision_memory.py : save_feedback()
              ├── upsert decision_feedback  ✓
              └── [HOOK NON-BLOQUANT] arc_service.create_arc_from_feedback()
                    ├── vérifie UNIQUE(origin_analysis_id, recommendation_id) — idempotent
                    ├── insère dans decision_arcs
                    └── retourne { arc_created, arc_id, arc_status }
              
              RÉPONSE API :
              {
                "success": true,
                "feedback_id": "...",
                "arc_created": true,        ← ajouté en V2
                "arc_id": "uuid-...",       ← null si échec ou déjà existant
                "arc_status": "intention"   ← null si arc_created = false
              }

FeedbackCard.tsx reçoit la réponse
  └── if (arc_created) → affiche inline "Décision tracée ✓" (pas de composant séparé)
```

**Idempotence garantie par :** `UNIQUE (origin_analysis_id, recommendation_id)` avec `ON CONFLICT DO NOTHING` dans `arc_service.create_arc_from_feedback()`. Appeler cette fonction deux fois pour la même recommandation est sans effet.

**Conséquence :** `FeedbackCard.tsx` n'appelle JAMAIS `createArc()`. Il lit `response.arc_id` et l'utilise si présent.

---

## Section E — Observabilité et récupération (C5)

### Logging structuré

Remplace `except Exception: pass` dans le hook non-bloquant :

```python
# Dans decision_memory.py, après upsert decision_feedback réussi
try:
    arc_result = arc_service.create_arc_from_feedback(
        company_id=company_id,
        origin_analysis_id=report_id,
        recommendation_id=recommendation_id,
        decision_source=source,
        decision_index=index,
        decision_text=action_text,
    )
    arc_created = arc_result.get("created", False)
    arc_id = arc_result.get("arc_id")
except Exception as e:
    logger.error(
        "[ARC] Échec création arc — "
        "company_id=%s report_id=%s recommendation_id=%s : %s",
        company_id, report_id, recommendation_id, e,
        exc_info=True
    )
    arc_created = False
    arc_id = None
    # L'arc peut être reconstruit par backfill. Voir arc_service.backfill_missing_arcs().
```

### Reconstruction par backfill (replay)

`arc_service.backfill_missing_arcs(company_id)` identifie les lignes de `decision_feedback` avec `status = 'planned'` sans arc correspondant et les crée. Idempotent.

Appelable via endpoint admin : `POST /api/admin/arcs/backfill?company_id=xxx`  
(accessible seulement par superadmin Supabase RLS — non exposé en production publique)

Vérification des gaps : `GET /api/admin/arcs/integrity` retourne le count de feedbacks "planned" sans arc — sert de monitoring.

---

## Section F — Frontière conceptuelle : Action ≠ Décision ≠ Exécution (C2)

### Définitions opérationnelles dans Pepperyn

| Terme | Origine | Table | Ce que c'est |
|-------|---------|-------|-------------|
| **Recommandation** | LLM Pepperyn | `plan_action` / `plan_action_haute` | Une suggestion générée — pas encore une décision |
| **Intention** | Feedback "planned" | `decision_feedback.status` | L'utilisateur envisage d'appliquer — pas encore une décision |
| **Décision** | État `decision` de l'arc | `decision_arcs.status = 'decision'` | L'utilisateur a confirmé son engagement — irréversible dans l'arc |
| **Exécution** | Feedback check-in | `decision_arcs.execution_status` | Ce qui a été mis en oeuvre |

### Ce que l'arc stocke dans `decision_text`

`decision_text` est initialisé avec le texte de la recommandation Pepperyn (verbatim). L'utilisateur peut le reformuler dans `decision_notes` s'il veut exprimer sa décision dans ses propres termes. Ces deux champs coexistent : la recommandation d'origine est toujours tracée.

### L'arc n'est PAS une copie du plan d'action

L'arc référence le plan d'action via `recommendation_id` et `decision_index`. Il ne le duplique pas. Si l'utilisateur veut savoir "quel était le texte exact de la recommandation", il remonte à `origin_analysis_id → analyses.analyse_json.plan_action[decision_index]`.

---

## Section G — Refus de lien conséquence (C3)

### Le problème V1

V1 disait : si l'utilisateur refuse le lien entre une conséquence observée et son arc → arc passe à ABANDONED.

C'est faux. Refuser un lien est une information, pas un abandon.

### Le comportement correct

```
Analyse N+1 disponible
  └── arc_service.detect_consequence_candidates(arc_id, new_analysis_id)
        └── si signal détecté → insère arc_analysis_links avec
              link_type = 'consequence_candidate'
              confirmed_by_user = NULL   (en attente)
              link_hypothesis = "Votre marge a évolué de X% depuis votre décision de Y"

ArcConsequencePrompt.tsx présente le candidat

  Utilisateur clique "Oui, c'est lié"
    └── link_type → 'consequence_confirmed', confirmed_by_user = TRUE
    └── arc.status → CONSEQUENCES_LINKED  ← avance

  Utilisateur clique "Non, pas lié"
    └── link_type → 'consequence_rejected', confirmed_by_user = FALSE
    └── arc.status reste EXECUTION  ← ne change PAS
    └── Une nouvelle analyse peut produire un autre candidat plus tard
```

Un arc ne passe jamais à ABANDONED automatiquement. C'est une action volontaire de l'utilisateur avec une raison explicite.

### Copie UI interdite (C8 — causalité)

Les templates de `link_hypothesis` utilisables :

✅ **AUTORISÉ**  
- "Observé après votre décision : votre marge brute a progressé de +3,2%"
- "Depuis votre décision du [date], votre CA a évolué de X à Y"
- "Une corrélation temporelle existe entre votre décision et cette évolution"

❌ **INTERDIT**  
- "Votre décision a causé..."
- "Grâce à votre action, ..."
- "Ce résultat est la conséquence de..."

### Hiérarchie causale dans le code (C8)

Pepperyn peut affirmer, au maximum, le niveau 3 de la hiérarchie suivante :

| Niveau | Affirmation | Dans Pepperyn |
|--------|-------------|---------------|
| 1 | Observation factuelle | ✅ Toujours autorisé |
| 2 | Association temporelle | ✅ Autorisé — "est survenu après" |
| 3 | Hypothèse de lien | ✅ Autorisé — "pourrait être lié à" |
| 4 | Lien confirmé par l'utilisateur | ✅ Autorisé après confirmation |
| 5 | Causalité démontrée | ❌ Hors périmètre MVP |

Le champ `link_hypothesis` stocke uniquement des niveaux 1–3.  
Après confirmation utilisateur, `link_type = 'consequence_confirmed'` — c'est le niveau 4.  
Le niveau 5 n'existe pas dans Pepperyn.

---

## Section H — Liste de fichiers minimum corrigée (C9)

V1 était incohérent : il décrivait un cycle complet tout en listant un minimum qui ne permettait pas de fermer l'arc.

La liste suivante est le **strict minimum pour fermer un arc réel de bout en bout** (US-01 à US-05) :

### Fichiers à CRÉER (8)

| # | Fichier | Contenu | US couverte |
|---|---------|---------|-------------|
| 1 | `backend/migrations/v16_decision_arcs.sql` | Tables `decision_arcs` + `arc_analysis_links` + index + trigger CLOSED | Toutes |
| 2 | `backend/models/decision_arc.py` | Pydantic models : `DecisionArc`, `ArcAnalysisLink`, `ArcCreateResult`, `ArcConsequenceRequest`, `ArcLearningRequest` | Toutes |
| 3 | `backend/services/arc_service.py` | `create_arc_from_feedback()`, `detect_consequence_candidates()`, `confirm_consequence_link()`, `propose_learning()`, `validate_learning()`, `backfill_missing_arcs()` | Toutes |
| 4 | `backend/routers/arcs.py` | `GET /api/arcs/{id}`, `POST /api/arcs/{id}/consequence`, `POST /api/arcs/{id}/learning`, `GET /api/admin/arcs/integrity` | US-03 à US-05 |
| 5 | `backend/tests/test_arc_service.py` | Tests unitaires `arc_service` (mock Supabase) | Régression |
| 6 | `frontend/lib/arc-api.ts` | `confirmConsequenceLink()`, `validateLearning()` — uniquement ces deux appels | US-04, US-05 |
| 7 | `frontend/components/chat/ArcConsequencePrompt.tsx` | Carte "Pepperyn observe une corrélation temporelle — la relier à votre décision ?" | US-04 |
| 8 | `frontend/components/chat/ArcLearningCard.tsx` | Carte "Voici ce que cet arc nous apprend — valider ou corriger" | US-05 |

**Nota :** Pas de `ArcCreatedToast.tsx` séparé. Le feedback de création (`arc_created = true`) est affiché inline dans `FeedbackCard.tsx` (ajout d'une ligne conditionnelle).

### Fichiers à MODIFIER (5)

| # | Fichier | Modification | Portée |
|---|---------|-------------|--------|
| 9 | `backend/routers/decision_memory.py` | Dans `save_feedback()` : hook arc post-upsert + retourner `arc_created`, `arc_id`, `arc_status` dans la réponse | US-01 |
| 10 | `backend/routers/analyze.py` | Fin de `_save_to_db()` : appeler `arc_service.detect_consequence_candidates()` pour tous les arcs EXECUTION de la company | US-03 |
| 11 | `backend/main.py` | `app.include_router(arcs_router)` | Infrastructure |
| 12 | `frontend/components/chat/FeedbackCard.tsx` | Lire `response.arc_id` après soumission feedback. Afficher "Décision tracée ✓" si `arc_created`. Stocker `arc_id` dans le state. | US-01, US-02 |
| 13 | `frontend/components/chat/ChatContainer.tsx` | Dans `proceedWithUpload()` : si `result.arc_consequence_candidates?.length > 0`, injecter un message `content_type='arc_consequence_prompt'` (même pattern que `feedback_request` L296-302) | US-04 |

**Total : 8 créés + 5 modifiés = 13 fichiers.**

---

## Section I — Tests et régression

### Tests unitaires à écrire (`test_arc_service.py`)

```python
# Arc de bout en bout
def test_create_arc_from_feedback_creates_row()
def test_create_arc_idempotent_on_duplicate()         # UNIQUE constraint
def test_arc_status_progression_forward_only()
def test_closed_arc_cannot_be_updated()               # trigger test
def test_reject_consequence_does_not_abandon_arc()    # C3
def test_backfill_creates_missing_arcs()              # C5

# Causalité (C8)
def test_link_hypothesis_does_not_contain_causal_language()
```

### Tests de régression pipeline existant

- `POST /api/analyze` sans aucun arc ouvert → comportement identique à aujourd'hui
- `PUT /api/decision-memory/feedback` avec `status='rejected'` → pas d'arc créé
- `PUT /api/decision-memory/feedback` avec `status='planned'` → arc créé, réponse enrichie
- Exception dans `arc_service` → feedback sauvé quand même, réponse retournée sans `arc_id`

### Validation additive (principe cardinal)

Avant chaque commit : lancer le pipeline analyse complet sur une fixture existante et vérifier que `AnalysisResult` est identique à avant l'introduction de l'arc. Les deux doivent être strictement indépendants.

---

## Section J — Commits atomiques

Ordre d'implémentation (quand validation accordée) :

| # | Commit | Fichiers | Réversible si |
|---|--------|---------|---------------|
| 1 | `feat(arc): migration v16 — decision_arcs + arc_analysis_links` | migration SQL | Drop tables |
| 2 | `feat(arc): modèles Pydantic DecisionArc` | `models/decision_arc.py` | Suppr. fichier |
| 3 | `feat(arc): arc_service — création + backfill + conséquences + learning` | `services/arc_service.py` | Suppr. fichier |
| 4 | `feat(arc): router /api/arcs + enregistrement dans main.py` | `routers/arcs.py`, `main.py` | Retirer include_router |
| 5 | `test(arc): tests unitaires arc_service` | `tests/test_arc_service.py` | Suppr. fichier |
| 6 | `feat(arc): hook création arc dans decision_memory.py` | `routers/decision_memory.py` | Retirer les 15 lignes ajoutées |
| 7 | `feat(arc): détection conséquences candidates dans analyze.py` | `routers/analyze.py` | Retirer les 10 lignes ajoutées |
| 8 | `feat(arc): API frontend arc-api.ts` | `frontend/lib/arc-api.ts` | Suppr. fichier |
| 9 | `feat(arc): ArcConsequencePrompt + ArcLearningCard` | 2 composants | Suppr. fichiers |
| 10 | `feat(arc): FeedbackCard lit arc_id + ChatContainer injecte prompt conséquence` | `FeedbackCard.tsx`, `ChatContainer.tsx` | Retirer conditionnels |

Chaque commit est déployable indépendamment. L'arc est invisible à l'utilisateur tant que les hooks frontend (commits 9 et 10) ne sont pas en place.

---

## Section K — Ce qui n'est PAS dans ce MVP

Pour éviter toute dérive :

| Hors périmètre | Raison |
|----------------|--------|
| Tableau de bord des arcs | Post-MVP — valeur dépend du volume d'arcs |
| Capital Décisionnel calculé (OBJ-3) | Nécessite plusieurs arcs fermés en production |
| Liens entre arcs (INV-5) | Post-MVP — dépend de la quantité d'arcs |
| ACR / AQS calculés (M-1, M-2) | Post-MVP — nécessite base d'arcs |
| Notification automatique "ton arc a une conséquence" | Post-MVP — email ou push |
| Causalité démontrée (niveau 5) | Hors périmètre définitif pour cette version |
| Modification d'un arc CLOSED | Impossible par design (immuabilité) |
| Suppression d'un arc | Hors périmètre — les arcs sont des actifs, pas des brouillons |

---

## Checklist de validation avant implémentation

- [ ] La machine à états préserve bien S→D→E→C→L (Section B)
- [ ] `decision_confirmed_at` est bien immuable une fois écrit (Section C, trigger)
- [ ] Aucun chemin frontend ne crée un arc directement (Section D)
- [ ] Le refus d'un lien conséquence ne change pas le statut de l'arc (Section G)
- [ ] `link_hypothesis` ne contient jamais de langage causal (Section G, C8)
- [ ] `ArcConsequencePrompt.tsx` est dans la liste minimale (Section H, #7)
- [ ] Le pipeline principal (`POST /api/analyze`) n'est jamais bloqué par un échec arc (Section E)

---

**En attente de validation explicite avant toute écriture de code.**
