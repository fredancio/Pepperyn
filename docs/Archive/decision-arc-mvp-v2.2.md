# MVP Decision Arc Integration Plan — VERSION 2.2 (SPÉCIFICATION DE RÉFÉRENCE)

**Statut :** APPROUVÉ — RÉFÉRENCE GELÉE  
**Date d'approbation :** 2026-07-18  
**Tag Git :** `decision-arc-mvp-design-approved`  
**Branch d'implémentation :** `release-1/wp4c-commercial-offer-alignment`

> Ce document est la spécification de référence pour le premier Arc Décisionnel Pepperyn.
> Il est gelé. Les modifications futures doivent provenir de l'expérience utilisateur, de bugs,
> ou de données réelles — jamais de l'élégance théorique.

---

## Chaîne canonique

```
Situation     → DecisionKernel dk-1
                EXPLICITEMENT RÉFÉRENCÉ via origin_analysis_id (NON DUPLIQUÉ)
                Validé à la création : kernel + fingerprint présents ou refus de création

Recommendation → Proposition Pepperyn
                 Snapshotée dans recommendation_text (IMMUTABLE)
                 Référencée via recommendation_id + origin_analysis_id

Intention     → Intention utilisateur
                decision_feedback.status = 'planned'
                arc.status = 'intention'

Decision      → Choix confirmé (explicit) OU inféré de l'exécution (inferred_from_execution)
                decision_text — NULL jusqu'à confirmation, IMMUTABLE une fois écrit
                decision_confirmed_at — date à laquelle Pepperyn l'a appris (≠ date réelle de décision)
                decision_confirmation_source — 'explicit' | 'inferred_from_execution' | NULL

Execution     → Mise en œuvre observée
                arc.execution_status, execution_notes

Consequences  → Observations ultérieures reliées par l'utilisateur
                arc_analysis_links (confirmed_by_user = TRUE)

Learning      → Apprentissage validé
                learning_text, learning_confirmed = TRUE, arc.status = 'closed'
```

**Principe non négociable :**
> Recommendation connue + Execution connue ≠ Decision documentée.
> Un Arc ne peut être CLOSED que si l'utilisateur a formulé la décision réelle
> (prospectivement ou rétrospectivement).

---

## Machine à états

```
INTENTION           → arc naît sur feedback status='planned'
    │ check-in done/partially_done
    ↓
EXECUTION           ← DECISION (état non atteignable en MVP sans UI dédiée)
    │ user confirme lien depuis arc_analysis_links candidate
    ↓
CONSEQUENCES_LINKED
    │ IA génère learning automatiquement
    ↓
LEARNING_PROPOSED
    │ user valide + decision_text confirmé (sinon bloqué)
    ↓
CLOSED              ← terminal, immuable, trigger bloque tout UPDATE

Depuis tout état sauf CLOSED → ABANDONED (action explicite)
```

**Note MVP :** L'état DECISION est dans le schéma mais non atteignable en MVP (pas d'UI de confirmation explicite). Les arcs MVP passent directement INTENTION → EXECUTION via le check-in. L'état DECISION sera activé dans une version ultérieure.

**Règle de fermeture :** `decision_text IS NOT NULL` est requis pour CLOSED.
Si `decision_text` est NULL au moment de valider le learning, Pepperyn demande :
"Pour mémoire, quelle décision aviez-vous finalement prise ?" (pré-rempli avec `recommendation_text`).

---

## Schéma SQL

### Table `decision_arcs`

```sql
CREATE TABLE public.decision_arcs (
  id                          UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- CONTEXTE (IMMUTABLE)
  company_id                  UUID REFERENCES companies(id)  ON DELETE CASCADE NOT NULL,
  entity_id                   UUID REFERENCES entities(id)   ON DELETE SET NULL,

  -- ORIGINE (IMMUTABLE après création)
  origin_analysis_id          UUID REFERENCES analyses(id)   ON DELETE SET NULL NOT NULL,
  decision_fingerprint        TEXT NOT NULL,
  recommendation_id           TEXT NOT NULL,
  decision_source             TEXT NOT NULL
    CHECK (decision_source IN ('plan_action_haute', 'plan_action')),
  UNIQUE (origin_analysis_id, recommendation_id),

  -- RECOMMENDATION (IMMUTABLE — snapshot Pepperyn)
  recommendation_text         TEXT NOT NULL,

  -- DECISION (IMMUTABLE une fois écrit)
  decision_text               TEXT,             -- NULL jusqu'à confirmation
  decision_notes              TEXT,             -- reformulation libre utilisateur
  decision_confirmed_at       TIMESTAMPTZ,      -- quand Pepperyn l'a appris (≠ date réelle)
  decision_confirmation_source TEXT
    CHECK (decision_confirmation_source IN ('explicit', 'inferred_from_execution')),
  -- NULL à INTENTION
  -- 'inferred_from_execution' : check-in done/partially_done
  -- 'explicit' : confirmation intentionnelle (prospective ou rétrospective)

  -- ÉTAT (forward-only sauf ABANDONED)
  status                      TEXT NOT NULL DEFAULT 'intention'
    CHECK (status IN ('intention', 'decision', 'execution',
                      'consequences_linked', 'learning_proposed', 'closed', 'abandoned')),

  -- EXÉCUTION (MUTABLE jusqu'à consequences_linked)
  execution_status            TEXT NOT NULL DEFAULT 'not_started'
    CHECK (execution_status IN ('not_started', 'in_progress', 'partial', 'complete')),
  execution_notes             TEXT,
  execution_updated_at        TIMESTAMPTZ,

  -- LEARNING (MUTABLE jusqu'à closed)
  learning_text               TEXT,
  learning_confirmed          BOOLEAN NOT NULL DEFAULT FALSE,
  learning_modified           BOOLEAN NOT NULL DEFAULT FALSE,

  -- TIMESTAMPS
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  closed_at                   TIMESTAMPTZ,      -- IMMUTABLE une fois écrit
  abandoned_at                TIMESTAMPTZ,
  abandoned_reason            TEXT
);
```

### Table `arc_analysis_links`

```sql
CREATE TABLE public.arc_analysis_links (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  arc_id                UUID REFERENCES decision_arcs(id) ON DELETE CASCADE NOT NULL,
  analysis_id           UUID REFERENCES analyses(id)      ON DELETE CASCADE NOT NULL,
  link_type             TEXT NOT NULL
    CHECK (link_type IN ('origin', 'consequence_candidate',
                         'consequence_confirmed', 'consequence_rejected', 'context')),
  -- Causalité max niveau 3 : "est survenu après" / "est corrélé à" — JAMAIS "a causé"
  link_hypothesis       TEXT,
  confirmed_by_user     BOOLEAN,  -- NULL = pending, TRUE = confirmé, FALSE = rejeté
  user_rejection_reason TEXT,
  linked_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at           TIMESTAMPTZ,
  UNIQUE (arc_id, analysis_id)
);
```

### Trigger immutabilité

```sql
CREATE OR REPLACE FUNCTION arc_immutability_guard()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status = 'closed' THEN
    RAISE EXCEPTION 'Arc % is CLOSED and immutable.', OLD.id;
  END IF;
  IF OLD.decision_text IS NOT NULL AND NEW.decision_text IS DISTINCT FROM OLD.decision_text THEN
    RAISE EXCEPTION 'decision_text is immutable once written on arc %.', OLD.id;
  END IF;
  IF OLD.decision_confirmed_at IS NOT NULL AND NEW.decision_confirmed_at IS DISTINCT FROM OLD.decision_confirmed_at THEN
    RAISE EXCEPTION 'decision_confirmed_at is immutable once written on arc %.', OLD.id;
  END IF;
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## Classification d'immuabilité

| Champ | Règle |
|-------|-------|
| `origin_analysis_id`, `decision_fingerprint`, `recommendation_id`, `decision_source`, `created_at` | IMMUTABLE |
| `recommendation_text` | IMMUTABLE |
| `decision_text` | IMMUTABLE une fois écrit (trigger) |
| `decision_confirmed_at` | IMMUTABLE une fois écrit (trigger) |
| `closed_at` | IMMUTABLE une fois écrit |
| `status` | Forward-only (sauf ABANDONED) |
| `decision_notes`, `execution_notes`, `learning_text` | MUTABLE jusqu'aux seuils respectifs |
| `arc_analysis_links` (confirmed) | APPEND-ONLY |
| Tout champ après `status = 'closed'` | SEALED (trigger) |

---

## Source de vérité unique pour la création d'arc

Backend seul crée les arcs. Frontend lit le résultat.

```
PUT /api/decision-feedback { status: 'planned', ... }
  → decision_memory.py : upsert_feedback()
    → [hook non-bloquant] arc_service.create_arc_from_feedback()
      → vérifie decision_kernel + decision_fingerprint sur origin_analysis
      → INSERT decision_arcs (UNIQUE constraint = idempotent)
  → réponse : { success: true, arc_created: bool, arc_id: str|null, arc_status: str|null }
```

---

## Hiérarchie causale (niveau max : 3)

| Niveau | Affirmation | Pepperyn |
|--------|-------------|----------|
| 1 | Observation factuelle | ✅ |
| 2 | Association temporelle ("est survenu après") | ✅ |
| 3 | Hypothèse de lien ("pourrait être lié à") | ✅ |
| 4 | Lien confirmé par l'utilisateur | ✅ (après confirmation) |
| 5 | Causalité démontrée | ❌ Hors périmètre |

Templates `link_hypothesis` autorisés :
- "Depuis votre décision de X, une nouvelle analyse montre Y"
- "Ces évolutions sont survenues après votre décision"
- "Une corrélation temporelle existe entre votre décision et cette évolution"

Interdits : "a causé", "grâce à votre action", "est la conséquence de"

---

## Fichiers — Liste complète

### Créés (8)

| Fichier | Contenu |
|---------|---------|
| `backend/migrations/v16_decision_arcs.sql` | Tables + trigger + indexes |
| `backend/models/decision_arc.py` | Pydantic models |
| `backend/services/arc_service.py` | Service complet |
| `backend/routers/arcs.py` | Endpoints arc |
| `backend/tests/test_arc_service.py` | Tests unitaires |
| `frontend/lib/arc-api.ts` | Fonctions API frontend |
| `frontend/components/chat/ArcConsequencePrompt.tsx` | Carte conséquence + learning |
| `frontend/components/chat/ArcLearningCard.tsx` | Carte learning standalone |

### Modifiés (6)

| Fichier | Modification |
|---------|-------------|
| `backend/models/schemas.py` | Ajouter `arc_consequence_candidates` à `AnalyzeResponse` |
| `backend/routers/decision_memory.py` | Hook arc création + retour arc_created/arc_id |
| `backend/routers/analyze.py` | Conséquence detection post-_save_to_db |
| `backend/main.py` | Enregistrer arc router |
| `frontend/lib/api.ts` | Étendre retour `submitDecisionFeedback` |
| `frontend/components/chat/FeedbackCard.tsx` | Lire arc_created + afficher "Décision tracée ✓" |
| `frontend/components/chat/ChatContainer.tsx` | Injecter arc_consequence_prompt message |

---

## Ce qui n'est PAS dans ce MVP

- Tableau de bord des arcs
- Capital Décisionnel calculé (OBJ-3)
- Liens entre arcs (INV-5)
- ACR / AQS calculés (M-1, M-2)
- Notifications automatiques
- Causalité démontrée (niveau 5)
- Modification d'un arc CLOSED
- Suppression d'arc
- État DECISION atteignable (sans UI dédiée)

---

## Règle de gel

À partir de ce document, les modifications de l'architecture Arc doivent provenir de :
- Retour utilisateur réel
- Bug confirmé en production
- Données d'usage démontrant un problème

**Pas de modifications par élégance théorique.**
