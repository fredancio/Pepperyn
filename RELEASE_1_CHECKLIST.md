# PEPPERYN — RELEASE 1.0 CHECKLIST
**Checklist d'implémentation et de validation**  
**Date :** 13 juillet 2026  
**Référence :** PEPPERYN_DECISIONS_V1.md + RELEASE_1_0_PLAN.md + TERMINOLOGY.md  
**Statut :** WP0 / WP0.5 / WP0.75 / FINAL PREPARATION terminés — **Contrat de développement figé. Prêt pour WP1A.**

> **Règle absolue :** Ne commencer aucun WP sans validation explicite du WP précédent.  
> **Règle absolue :** Aucun commit sans tests qui passent.  
> **Règle absolue :** Aucune modification Stripe / Supabase / base de données sans confirmation.

---

## RÉSUMÉ D'AVANCEMENT

| WP | Intitulé | Statut | Validé |
|---|---|---|---|
| WP0 | Business Rules Freeze | ✅ Terminé | ✅ Validé |
| WP0.5 | Business Rules Finalization | ✅ Terminé | ✅ Validé |
| WP0.75 | Final Business Rules Freeze | ✅ Terminé | ✅ Validé |
| WP0.FINAL | Final Preparation — Contrat figé | ✅ Terminé | ✅ **Validé — Prêt pour WP1A** |
| WP1A | Product Catalog | ✅ Terminé | ✅ Validé — commit `b651a7c` |
| WP1B | Billing Migration | ✅ Terminé | ⏳ En attente validation |
| WP1B.1 | Webhook Hardening | ✅ Terminé | ⏳ En attente validation |
| WP1B.2 | Diagnostic idempotence | ✅ Terminé | ⏳ En attente validation |
| WP1B.3 | Idempotence webhook — correctif | 🚫 **BLOQUANT avant prod** | — |
| WP1C | Usage Migration | 🔲 À démarrer | — |
| WP2 | Backend Quota Fix | 🔲 À démarrer | — |
| WP3 | Stripe Configuration | 🔲 À démarrer | — |
| WP4 | Parcours SCALE + CreditsModal | 🔲 À démarrer | — |
| WP5 | Frontend Alignment | 🔲 À démarrer | — |
| WP6 | Legacy Plan Cleanup | 🔲 À démarrer | — |
| WP7 | ~~Chat History Truncation~~ | 🚫 **REPOUSSÉ** | ❌ Remplacé par R1.1 CMO |
| WP8 | ~~Export Cache Persistence~~ | ✅ **DÉCIDÉ** | ✅ Régénération à la demande |
| WP9 | PIN Rate Limiter Persistence | 🔲 À démarrer | — |
| WP10 | Admin Dashboard Cleanup | 🔲 À démarrer | — |

---

## WP0.FINAL — CONTRAT DE DÉVELOPPEMENT FIGÉ ✅

**Documents produits :**
- [x] `PEPPERYN_BUSINESS_RULES_V1_FINAL.md` — Contrat fonctionnel complet (version finale)
- [x] `PEPPERYN_DECISIONS_V1.md` — Résumé exécutif et référence technique (version finale)
- [x] `ADR_001_PRODUCT_CATALOG.md` — Architecture Decision Record WP1A
- [x] `TERMINOLOGY.md` — Glossaire officiel (termes obligatoires dans le code, la doc, le marketing)
- [x] `RELEASE_1_CHECKLIST.md` — Ce document (mis à jour)

**RÈGLES MÉTIER OFFICIELLES — NON NÉGOCIABLES**

### Plans et quotas

| Plan | Analyses/mois | Interactions/mois | Entités | Prix |
|---|---|---|---|---|
| FREE | 1 | 3 | 1 | 0 € |
| PRO | 30 | 75 | 10 | 149 €/mois |
| SCALE | 100 | 500 | Illimité | 349 €/mois |

Le chat illimité est **définitivement rejeté**. Cette décision ne sera plus jamais remise en question.

### Règle sur les interactions (contractuelle)

- Il n'existe **aucune limite d'interactions par analyse**
- Le quota est **uniquement mensuel**
- Les moyennes statistiques (≈2,5/analyse PRO, ≈5/analyse SCALE) sont des **exemples d'usage**, jamais des règles métier
- Le code **ne devra jamais** implémenter une limite d'interactions par analyse
- Cette règle s'applique à FREE, PRO et SCALE

### Règles sur les Executive Capacity Packs

- Ajoutent **uniquement des analyses**
- N'ajoutent **jamais** d'interactions chat
- Ne modifient **jamais** le quota mensuel de chat
- Ne changent **jamais** le plan
- Ne modifient **jamais** la date de renouvellement Stripe
- **Ordre de consommation :** Les analyses bonus sont consommées **EN PREMIER**, puis le quota mensuel de l'abonnement
- Au renouvellement mensuel : le quota mensuel est recrédité à plein ; les analyses bonus déjà consommées restent consommées ; les analyses bonus non consommées restent disponibles
- À l'annulation : analyses bonus suspendues (inutilisables en FREE), conservées en base, réactivées à la re-souscription

### Autres décisions figées

- [x] Entités PRO = 10 max, SCALE = illimité
- [x] Upgrade PRO→SCALE = Billing Portal Stripe (Release 1.0)
- [x] Paiement échoué = email Resend, accès maintenu pendant retry Stripe (7j)
- [x] Crédits bonus = suspendus à l'annulation, jamais supprimés
- [x] Migration legacy = PLAN_LIMITS seulement, pas de SQL
- [x] WP7 repoussé → Conversation Memory Optimization (Release 1.1)
- [x] WP8 remplacé → Régénération à la demande (pas de cache Supabase Storage)

---

## WP1A — PRODUCT CATALOG

**Objectif :** Créer `backend/config/product_catalog.py` comme seule source de vérité.  
**Référence :** ADR_001_PRODUCT_CATALOG.md

**✅ WP1A IMPLÉMENTÉ — 13 juillet 2026 — branche `release-1/wp1a-product-catalog`**

**Fichiers créés :**
- [x] `backend/config/product_catalog.py` — Source canonique unique (types, constantes, fonctions)
- [x] `backend/tests/test_product_catalog.py` — 95 tests, 20 cas couverts

**Interface publique exposée :**
```
Types    : PlanLimits, ExecutiveCapacityPack, PlanDisplay
Listes   : COMMERCIAL_PLAN_IDS, EXECUTIVE_CAPACITY_PACK_IDS
Constantes: PLAN_LIMITS, PLAN_PRICES, EXECUTIVE_CAPACITY_PACKS,
            STRIPE_PRICE_IDS, PLAN_DISPLAY_NAMES,
            LEGACY_PLAN_ALIASES, LEGACY_INTERNAL_PLANS
Fonctions: get_plan(), get_commercial_plans(),
           get_executive_capacity_pack(), validate_stripe_price_ids()
```

**Résultat des tests :** `95 passed in 0.15s` — aucun échec  
**Contrôle syntaxe :** `python -m py_compile` → OK  
**Import sans Stripe :** OK (module importable sans variables d'environnement)

**IMPORTANT — Aucun consommateur migré en WP1A :**
- `usage_service.py` : PAS modifié en WP1A — sera migré en WP1C
- `billing_service.py` : PAS modifié en WP1A — migré en WP1B ✅
- `billing.py` : PAS modifié en WP1A — migré en WP1B ✅
- Frontend : PAS modifié — sera aligné en WP1D/WP5
- Comportement produit en WP1A : INCHANGÉ

**Refactorisations :**
- [x] `billing_service.py` : importer EXECUTIVE_CAPACITY_PACKS depuis product_catalog (WP1B)
- [x] `billing.py` : importer depuis product_catalog + exposer `GET /api/billing/plans` (WP1B)
- [ ] `usage_service.py` : importer PLAN_LIMITS depuis product_catalog (WP1C)

**Validation WP1A :**
- [x] Tests unitaires passent (95/95)
- [x] `python -m pytest tests/test_product_catalog.py -v` → 95 passed
- [x] `GET /api/billing/plans` retourne les valeurs correctes — validé en WP1B ✅
- [x] `billing_service.py` ne contient plus ADDON_QUANTITIES ni STRIPE_PRICE_IDS locaux

**Dépendances :** WP0.75 validé.  
**Durée estimée :** 2–3h.  
**Ordre :** Premier WP à exécuter.

---

## WP1B — BILLING MIGRATION

**Objectif :** Migrer `billing.py` et `billing_service.py` pour lire exclusivement depuis `product_catalog.py`.

**✅ WP1B IMPLÉMENTÉ — 13 juillet 2026 — branche `release-1/wp1b-billing-migration`**

**Modifications apportées :**

### `backend/services/billing_service.py`
- [x] `STRIPE_PRICE_IDS` dict local **supprimé** — Price IDs lus via `os.environ` ou `pack.stripe_price_id`
- [x] `ADDON_QUANTITIES` dict local **supprimé** — quantités lues depuis `EXECUTIVE_CAPACITY_PACKS`
- [x] Import de `get_executive_capacity_pack`, `validate_stripe_price_ids` depuis `product_catalog`
- [x] `is_configured()` : utilise `validate_stripe_price_ids()` du catalog
- [x] `create_checkout_session()` : validation explicite FREE/POWER/ENTERPRISE/inconnu + messages d'erreur précis
- [x] `process_webhook_event()` : quantité bonus via `pack.analyses_added` (Starter=10, Growth=20, Scale=80)

### `backend/routers/billing.py`
- [x] `PLANS_CATALOGUE` dict **supprimé** (128 lignes de constantes obsolètes)
- [x] Import de `get_commercial_plans`, `EXECUTIVE_CAPACITY_PACKS`, `EXECUTIVE_CAPACITY_PACK_IDS`
- [x] `_build_plans_catalogue()` : construit le catalogue dynamiquement depuis `product_catalog`
- [x] `GET /api/billing/plans` : retourne `_build_plans_catalogue()` (valeurs correctes)
- [x] POWER absent du catalogue public
- [x] `CheckoutRequest` : `"power"` retiré du commentaire de type

### Nouveaux fichiers
- [x] `backend/tests/test_billing_migration.py` — **38 tests, 38 passing, 0.48s**
- [x] `KNOWN_TEST_FAILURES.md` — 4 échecs pré-existants documentés (PPTX/EDM, hors scope)

**Résultat des tests :**
```
test_billing_migration.py  : 38 passed in 0.48s
test_product_catalog.py    : 95 passed (inchangé)
test_rule_00*.py           : 4 failed (pré-existants, inchangés)
TOTAL                      : 111 passed, 4 failed (pré-existants uniquement)
```

**Contrat de réponse `GET /api/billing/plans` :**
```json
{
  "success": true,
  "data": {
    "plans": [
      {"id": "free",  "price_eur": 0,   "analyses_per_month": 1,   "chat_monthly_cap": 3,   ...},
      {"id": "pro",   "price_eur": 149, "analyses_per_month": 30,  "chat_monthly_cap": 75,  ...},
      {"id": "scale", "price_eur": 349, "analyses_per_month": 100, "chat_monthly_cap": 500, ...}
    ],
    "executive_capacity_packs": [
      {"id": "addon_starter", "analyses_added": 10, "price_eur": 39,  ...},
      {"id": "addon_growth",  "analyses_added": 20, "price_eur": 79,  ...},
      {"id": "addon_scale",   "analyses_added": 80, "price_eur": 239, ...}
    ],
    "addons": [...]   // alias de executive_capacity_packs, supprimé en WP5
  }
}
```

**Évolutions du contrat vs PLANS_CATALOGUE :**
- `interactions_per_analysis` → `chat_monthly_cap` (quota mensuel global, sémantique correcte)
- `price_cents` ajouté (valeur canonique)
- `label`, `max_entities` ajoutés
- Champs marketing supprimés : `subtitle`, `highlighted`, `color`, `features`, `cta`
- POWER supprimé du catalogue public
- Mise à jour frontend prévue en WP5

**Validation WP1B :**
- [x] `billing_service.py` : 0 constante commerciale locale
- [x] `billing.py` : 0 constante commerciale locale
- [x] `GET /api/billing/plans` : PRO=149€/30 analyses, SCALE=349€/100 analyses
- [x] Checkout FREE → ValueError explicite
- [x] Checkout POWER → ValueError explicite
- [x] Webhook Starter → 10 analyses, Growth → 20, Scale Capacity Pack → 80
- [x] Tests 38/38 passent
- [x] Aucune régression WP1A (95 tests inchangés)
- [x] Aucune régression pre-existing (4 échecs = baseline)

---

## WP1B.2 — DIAGNOSTIC IDEMPOTENCE WEBHOOK

**Objectif :** Vérifier si un même événement Stripe peut être traité plusieurs fois.

**✅ WP1B.2 TERMINÉ — 13 juillet 2026**

### Trace du traitement webhook (fichiers et lignes)

```
Stripe (POST)
 └─ POST /api/billing/webhook
     └─ billing.py : stripe_webhook() [ligne ~235]
         └─ payload = await request.body()
         └─ billing_service.process_webhook_event(payload, stripe_signature)
             └─ billing_service.py : stripe.Webhook.construct_event() [ligne 166]
                 → vérifie la signature — rejette si invalide
             └─ event["type"] lu [ligne 172] — event["id"] JAMAIS LU
             └─ metadata.company_id, metadata.plan_or_addon extraits [lignes 184-185]
             └─ retourne dict {action, company_id, ...}
         └─ billing.py : dispatch sur action [lignes 251-284]
             → "update_plan" : sb.from_("companies").update({plan}) [ligne 262]
             → "add_bonus"   : usage_service.add_bonus_analyses(company_id, qty) [ligne 271]
                 └─ usage_service.py : add_bonus_analyses() [ligne 169]
                     └─ current_bonus = SELECT bonus_analyses  [READ]
                     └─ UPDATE SET bonus_analyses = current_bonus + qty  [WRITE]
```

### Résultats du diagnostic

| Mécanisme | Présent ? | Détail |
|---|---|---|
| Lecture de `event["id"]` Stripe | ❌ NON | `event["type"]` lu, `event["id"]` ignoré |
| Table `stripe_processed_events` | ❌ NON | Aucune migration, aucune table |
| Contrainte UNIQUE sur event_id | ❌ NON | Aucune |
| Check `checkout.session.id` | ❌ NON | Lu uniquement pour le log |
| Protection dans `add_bonus_analyses` | ❌ NON | READ-THEN-WRITE sans garde |
| Upsert idempotent côté DB | ❌ NON | UPDATE simple (pas ON CONFLICT) |

### Verdict par type d'événement

| Événement | Doublon possible ? | Mécanisme | Risque |
|---|---|---|---|
| PRO activation | ✅ Idempotent | `UPDATE companies SET plan='pro'` (SET, pas INCREMENT) | Faible |
| SCALE activation | ✅ Idempotent | `UPDATE companies SET plan='scale'` (SET, pas INCREMENT) | Faible |
| Starter Capacity Pack | ❌ **Double crédit** | `bonus_analyses += 10` deux fois = +20 | **ÉLEVÉ** |
| Growth Capacity Pack | ❌ **Double crédit** | `bonus_analyses += 20` deux fois = +40 | **ÉLEVÉ** |
| Scale Capacity Pack | ❌ **Double crédit** | `bonus_analyses += 80` deux fois = +160 | **ÉLEVÉ** |
| downgrade_free | ✅ Idempotent | `UPDATE companies SET plan='free'` (SET) | Faible |

### Scénarios de double livraison Stripe

Stripe **retente automatiquement** un webhook quand le serveur retourne non-2xx.
Après WP1B.1, les erreurs d'intégrité (pack inconnu, metadata vides) retournent HTTP 400.
Un scénario de double crédit réel peut se produire si :
1. Le serveur traite correctement le webhook (crédite les analyses)
2. La réponse HTTP 200 est perdue (timeout réseau, crash post-traitement)
3. Stripe rejoue le webhook → deuxième crédit

Il existe aussi un risque de livraison dupliquée côté Stripe même sans erreur (rare mais documenté).

### Tests ajoutés (7 tests diagnostics — WP1B.2)

| Test | Vérifie | Résultat |
|---|---|---|
| IDP-01 | `event["id"]` n'est jamais lu | ✅ PASS — confirme l'absence de dédup |
| IDP-02 | PRO : même event deux fois → même dict | ✅ PASS — idempotent par accident |
| IDP-03 | SCALE : même event deux fois → même dict | ✅ PASS — idempotent par accident |
| IDP-04 | addon_starter : même event deux fois → add_bonus x2 | ✅ PASS — vulnérabilité confirmée |
| IDP-05 | 3 packs : même event deux fois → add_bonus x2 | ✅ PASS — vulnérabilité confirmée |
| IDP-06 | `add_bonus_analyses` : READ-THEN-WRITE non atomique | ✅ PASS — confirme le risque |
| IDP-07 | Aucune table `stripe_processed_events` en migration | ✅ PASS — protection absente |

**Tests totaux après WP1B.2 : 48/48 passing** (+ 95/95 WP1A — baseline inchangée)

### Réponses aux questions WP1B.2

1. **Les activations PRO et SCALE sont-elles idempotentes ?** ✅ OUI — par nature de l'opération SQL (SET).
2. **Les achats d'Executive Capacity Packs sont-ils idempotents ?** ❌ NON — `bonus_analyses += qty` est un INCREMENT.
3. **Un événement Stripe dupliqué peut-il ajouter deux fois les Analyses ?** ❌ OUI — confirmé.
4. **Une protection existe-t-elle déjà ?** ❌ NON — aucun mécanisme à aucun niveau.
5. **L'idempotence est-elle bloquante avant le lancement commercial ?** ❌ **OUI — BLOQUANT**.

---

## WP1B.3 — IDEMPOTENCE WEBHOOK (correctif) 🚫 BLOQUANT AVANT PROD

**Objectif :** Garantir qu'un même événement Stripe Executive Capacity Pack
ne crédite jamais deux fois les Analyses, quelle que soit la cause
(retry Stripe, livraison dupliquée, crash post-traitement).

**Condition :** NE PAS COMMENCER avant validation explicite de WP1B.2.

**Statut :** 🔲 À démarrer — **BLOQUANT avant tout test Stripe réel et avant lancement commercial**

**Contraintes :**
- Ne pas implémenter de solution improvisée
- Aucune migration sans validation explicite
- Aucun push sans validation

### Solution proposée : registre persistant par `event.id` Stripe

**Principe** : avant tout traitement d'un webhook `checkout.session.completed`,
vérifier si `event["id"]` a déjà été traité. Si oui → retourner HTTP 200
immédiatement sans écriture (acquittement Stripe, pas de retry).

**Migration requise (`v10_stripe_processed_events.sql`) :**
```sql
CREATE TABLE IF NOT EXISTS public.stripe_processed_events (
    stripe_event_id  TEXT        NOT NULL,
    processed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type       TEXT        NOT NULL,
    company_id       TEXT,
    action           TEXT,
    PRIMARY KEY (stripe_event_id)
);
-- Nettoyage automatique après 90 jours (politique Stripe)
-- (à implémenter via pg_cron ou fonction Supabase)
COMMENT ON TABLE public.stripe_processed_events
  IS 'Registre des événements Stripe traités — garantit l''idempotence des webhooks.';
```

**Modification `billing.py` (route handler webhook) :**
```python
# 1. Lire event_id AVANT tout traitement
stripe_event_id = result.get("stripe_event_id")  # propagé par process_webhook_event
if stripe_event_id:
    # 2. Tenter l'insertion — UNIQUE violation = déjà traité
    try:
        sb.from_("stripe_processed_events").insert({
            "stripe_event_id": stripe_event_id,
            "event_type":      result.get("event_type", ""),
            "company_id":      result.get("company_id", ""),
            "action":          result.get("action", ""),
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            logger.warning(f"[WEBHOOK IDEMPOTENCE] Événement déjà traité : {stripe_event_id}")
            return {"received": True, "action": "duplicate_skipped"}
        raise
# 3. Seulement si INSERT réussi → effectuer l'écriture métier
```

**Modification `billing_service.process_webhook_event()` :**
```python
# Propager event["id"] dans le dict de retour
return {
    "action":          "add_bonus",
    "stripe_event_id": event["id"],   # ← ajout
    "event_type":      etype,         # ← ajout
    ...
}
```

**Tests à ajouter (WP1B.3) :**
- `test_idp_pro_same_event_twice_no_double_effect` — PRO → idempotent (confirmé)
- `test_idp_scale_same_event_twice_no_double_effect` — SCALE → idempotent (confirmé)
- `test_idp_starter_same_event_twice_credited_once` — Starter → +10 une seule fois
- `test_idp_growth_same_event_twice_credited_once` — Growth → +20 une seule fois
- `test_idp_scale_pack_same_event_twice_credited_once` — Scale Capacity Pack → +80 une seule fois

**Durée estimée :** 2–4h (migration + modification handler + 5 tests)

**Dépendances :** WP1B.2 validé. Migration Supabase + validation explicite requises.

---

## WP2 — BACKEND QUOTA FIX

**Objectif :** Éliminer les bugs de production actifs sur les quotas.

**Note :** Si WP1 est complété correctement, la plupart de ces bugs sont déjà corrigés par le refactoring d'import. Ce WP vérifie et corrige les résiduels.

**Bugs à corriger :**

| Fichier | Variable | Valeur actuelle | Valeur cible | Couvert par WP1 |
|---|---|---|---|---|
| usage_service.py | PLAN_LIMITS["pro"]["analyses"] | 15 | 30 | ✅ si refacto WP1 |
| usage_service.py | PLAN_LIMITS["scale"]["analyses"] | 250 | 100 | ✅ si refacto WP1 |
| usage_service.py | PLAN_LIMITS["pro"]["chat_monthly_cap"] | 300 | 75 | ✅ si refacto WP1 |
| usage_service.py | PLAN_LIMITS["scale"]["chat_monthly_cap"] | None | 500 | ✅ si refacto WP1 |
| billing_service.py | ADDON_QUANTITIES["addon_growth"] | 50 | 20 | ✅ si refacto WP1 |
| billing_service.py | ADDON_QUANTITIES["addon_scale"] | 200 | 80 | ✅ si refacto WP1 |

**Tests à valider :**
- [ ] Usage PRO : 30 analyses disponibles, pas 15
- [ ] Usage SCALE : 100 analyses disponibles, pas 250
- [ ] Chat PRO : 75 messages/mois, pas 300
- [ ] Chat SCALE : 500 messages/mois, pas None/illimité
- [ ] Addon growth : +20 crédits, pas +50
- [ ] Addon scale : +80 crédits, pas +200

**Dépendances :** WP1 terminé.  
**Durée estimée :** 1–2h (surtout tests + vérification staging).

---

## WP3 — STRIPE CONFIGURATION

**Objectif :** Créer tous les produits Stripe manquants et connecter les variables d'environnement Railway.

**Produits Stripe à créer ou vérifier :**

| Produit | Type | Prix | Variable env Railway | Statut |
|---|---|---|---|---|
| PRO | subscription | 149 €/mois | `STRIPE_PRICE_PRO` | ⚠️ Existe mais à confirmer |
| SCALE | subscription | 349 €/mois | `STRIPE_PRICE_SCALE` | 🔲 À créer |
| Starter Capacity Pack | payment | 39 € | `STRIPE_PRICE_ADDON_STARTER` | 🔲 À créer |
| Growth Capacity Pack | payment | 79 € | `STRIPE_PRICE_ADDON_GROWTH` | 🔲 À créer |
| Scale Capacity Pack | payment | 239 € | `STRIPE_PRICE_ADDON_SCALE` | 🔲 À créer |

**Actions :**
- [ ] Créer SCALE subscription (349€/mois) dans Stripe Dashboard
- [ ] Créer Starter Capacity Pack (39€ one-time) dans Stripe Dashboard
- [ ] Créer Growth Capacity Pack (79€ one-time) dans Stripe Dashboard
- [ ] Créer Scale Capacity Pack (239€ one-time) dans Stripe Dashboard
- [ ] Ajouter toutes les variables `STRIPE_PRICE_*` dans Railway (env vars)
- [ ] Archiver dans Stripe : POWER (129€), ancien PRO (59€), anciens addons (19/69/199€)
- [ ] Vérifier le webhook Stripe : endpoint URL + secret `STRIPE_WEBHOOK_SECRET`

**Validation :**
- [ ] Checkout PRO (149€) fonctionne en mode test
- [ ] Checkout SCALE (349€) fonctionne en mode test
- [ ] Achat Starter Pack (39€) fonctionne en mode test
- [ ] Webhook déclenche correctement l'activation du plan
- [ ] `/api/billing/plans` retourne tous les stripe_price_id non-null

**Dépendances :** WP0.75 validé (prix officiels).  
**Durée estimée :** 2–3h.  
**⚠️ Cette action modifie Stripe. Validation explicite requise avant exécution.**

---

## WP4 — PARCOURS SCALE + CREDITSMODAL

**Objectif :** Créer le parcours self-service SCALE et corriger la CreditsModal.

**À créer :**
- [ ] `frontend/app/checkout/scale/page.tsx` (identique à /checkout/pro, adapté pour SCALE)
- [ ] Adapter `frontend/app/register/page.tsx` : détecter `plan=scale` en plus de `plan=pro`
- [ ] Mettre à jour `emailRedirectTo` pour SCALE : `/auth/callback?next=/checkout/scale`

**À corriger :**
- [ ] `CreditsModal.tsx` : remplacer `mailto:` par Stripe Checkout (`POST /api/billing/checkout { plan_or_addon: 'addon_*' }`)
- [ ] `CreditsModal.tsx` : afficher les 3 packs avec prix et crédits depuis `GET /api/billing/plans` (pas en hardcode)
- [ ] `CreditsModal.tsx` : afficher la règle "Les crédits n'expirent pas. Ils s'ajoutent à votre quota mensuel."
- [ ] `CreditsModal.tsx` : afficher que les packs n'ajoutent pas d'interactions chat

**À créer (/billing/success) :**
- [ ] Mécanisme de polling (2s × max 15 tentatives)
- [ ] Affichage "⏳ Activation en cours..."
- [ ] Sur plan confirmé : "✅ Plan activé !" → redirect /app/chat après 3s
- [ ] Sur timeout : message "Paiement confirmé, activation sous quelques minutes"

**Validation :**
- [ ] /register?plan=scale → /checkout/scale → Stripe → webhook → plan='scale'
- [ ] CreditsModal → Stripe → webhook → bonus_analyses crédités
- [ ] Polling fonctionne : plan change pendant le polling → redirect correct
- [ ] Timeout : message affiché sans redirect

**Dépendances :** WP3 (Stripe SCALE créé).  
**Durée estimée :** 3–4h.

---

## WP5 — FRONTEND ALIGNMENT

**Objectif :** Aligner toutes les valeurs commerciales hardcodées dans le frontend.

**Fichiers à modifier :**

| Fichier | Ce qui change |
|---|---|
| `featureGate.ts` | 8× "15 analyses / mois" → "30 analyses / mois" |
| `FaqSection.tsx` | Quotas (15→30, illimité→500) + email info@finflate.com → contact@pepperyn.com |
| `PricingSection.tsx` ou équivalent | Vérifier tous les affichages de prix et quotas |
| `pricingConstants.ts` (si existant) | Alimenter depuis GET /api/billing/plans |
| Toute page de tarification | PRO=149€, SCALE=349€ (pas 59€, pas 129€) |

**Validation :**
- [ ] Grep de "15 analyses" → 0 résultat
- [ ] Grep de "59€" ou "59 €" → 0 résultat (hors historique)
- [ ] Grep de "129€" ou "129 €" → 0 résultat (hors commentaires)
- [ ] Grep de "info@finflate" → 0 résultat
- [ ] Grep de "illimité" dans le contexte du chat → vérifié (500 affiché à la place)
- [ ] Page /pricing affiche FREE=0€/1 analyse, PRO=149€/30 analyses/75 chat, SCALE=349€/100 analyses/500 chat

**Dépendances :** WP1 (GET /api/billing/plans disponible).  
**Durée estimée :** 2–3h.

---

## WP6 — LEGACY PLAN CLEANUP

**Objectif :** Supprimer les plans legacy de l'interface publique (tout en les conservant en DB pour compat).

**Actions :**
- [ ] Supprimer POWER et ENTERPRISE de `PLANS_CATALOGUE` dans `billing.py` (via WP1)
- [ ] Vérifier que `/api/billing/plans` ne retourne que FREE, PRO, SCALE
- [ ] Vérifier que `featureGate.ts` n'expose pas POWER ou ENTERPRISE comme plans sélectionnables
- [ ] Supabase : vérifier la CHECK constraint `plan IN (...)` — si elle bloque PRO ou SCALE, rédiger une migration SQL (à valider séparément)

**Note sur la CHECK constraint Supabase :**
La constraint actuelle est `plan IN ('free', 'standard', 'standard_beta', 'premium')`. Elle peut bloquer les webhooks Stripe qui tentent de mettre `plan='pro'` ou `plan='scale'`. À vérifier impérativement en staging.

Migration SQL potentielle (à valider) :
```sql
ALTER TABLE companies 
DROP CONSTRAINT IF EXISTS companies_plan_check;

ALTER TABLE companies 
ADD CONSTRAINT companies_plan_check 
CHECK (plan IN ('free', 'pro', 'scale', 'standard', 'standard_beta', 'premium', 'power', 'enterprise'));
```

**⚠️ Cette migration SQL doit être validée explicitement avant exécution.**

**Validation :**
- [ ] Webhook `checkout.session.completed` avec plan='pro' → succès (pas de violation de constraint)
- [ ] Webhook `checkout.session.completed` avec plan='scale' → succès
- [ ] `/api/billing/plans` retourne uniquement 3 plans (FREE, PRO, SCALE)

**Dépendances :** WP1, WP3.  
**Durée estimée :** 1–2h.

---

## WP7 — 🚫 REPOUSSÉ — CONVERSATION MEMORY OPTIMIZATION (Release 1.1)

**Décision :** WP7 (Chat History Truncation) est **retiré du périmètre de la Release 1.0**.

### Justification

La truncation par sliding window ("envoyer au LLM les N derniers messages") est une optimisation des coûts superficielle qui entre en conflit avec l'investissement architectural central de Pepperyn.

**Problème 1 — Cohérence de la mémoire persistante.** Pepperyn construit une mémoire financière par entité (métriques × 6 dernières analyses, profil évolutif, tendances). Cette mémoire est conçue pour être injectée dans le contexte de chaque conversation. Un tronquage des N derniers messages détruirait le début de la conversation où le contexte crucial a été établi (persona financier, objectifs déclarés, contraintes exprimées).

**Problème 2 — UX dégradée sans avertissement.** Un utilisateur qui pose une question au message 31 en référence au message 2 obtiendrait une réponse incohérente sans comprendre pourquoi. Le tronquage serait silencieux, créant de la confusion.

**Problème 3 — Mauvaise stratégie d'optimisation.** Le coût chat est Haiku (≈0,001€/message). Le vrai coût à maîtriser est le nombre de tokens en contexte sur les analyses (Opus). WP7 s'attaque au mauvais problème.

**Problème 4 — Conflits avec la roadmap.** La roadmap R1.1 prévoit des agents IA, du RAG financier, et des MCPs ERP. Ces fonctionnalités nécessitent un contexte de conversation long et cohérent. Une architecture de tronquage introduite en R1.0 devrait être défaite en R1.1.

### Alternative recommandée — Conversation Memory Optimization (R1.1)

Au lieu d'une truncation mécanique, implémenter en Release 1.1 une stratégie de **résumé sémantique intelligent** :
- Si la conversation dépasse N messages, générer un résumé Haiku des échanges précédents
- Injecter ce résumé comme contexte compressé plutôt que les messages bruts
- Conserver l'intégralité de l'historique en DB (jamais de suppression)
- Coût : 1 appel Haiku supplémentaire pour la compression ≈ 0,001€

Cette stratégie préserve la cohérence sémantique que la truncation détruirait.

**Statut :** ❌ Retiré de Release 1.0 → 📋 Backlog Release 1.1 : "Conversation Memory Optimization"

---

## WP8 — ✅ DÉCISION : RÉGÉNÉRATION À LA DEMANDE (Release 1.0)

**Décision :** WP8 dans sa forme originale (cache Supabase Storage) est **remplacé** par une stratégie de régénération à la demande.

### Analyse de viabilité de la régénération

Les exports Pepperyn (PDF, PowerPoint, Excel) sont générés à partir :
- Du JSON de l'analyse, persisté intégralement dans Supabase Postgres
- Des templates de mise en forme (`excel_layout.py`, `pdf_layout.py`, `pptx_layout.py`)
- D'aucun appel LLM — uniquement du formatage de données

**Conclusion :** La régénération est entièrement déterministe et ne nécessite aucun appel LLM. Les données sources étant intégralement persistées, chaque export peut être régénéré à tout moment à partir de l'analyse stockée. La stratégie de régénération à la demande est viable et architecturalement préférable pour la Release 1.0.

### Décision architecturale

**Release 1.0 :**
- Supprimer le cache mémoire Python actuel (ou le laisser en place — il ne pose pas de problème critique en R1.0 puisque la régénération est instantanée si le cache est vide)
- Chaque requête de téléchargement régénère l'export depuis le JSON d'analyse en Supabase
- Coût : quelques millisecondes de CPU par génération, aucun appel LLM, aucun appel Anthropic
- Pas de Supabase Storage, pas de bucket, pas de TTL, pas de cron de nettoyage

**Release 1.1 (si performance insuffisante) :**
- Mesurer le temps de génération réel en production
- Si > 3 secondes pour les exports Excel complexes → envisager Supabase Storage avec TTL 30 jours
- Décision conditionnelle basée sur les métriques de production

### Actions Release 1.0

- [ ] Vérifier que le JSON de l'analyse contient toutes les données nécessaires à la régénération
- [ ] S'assurer que les routes d'export (`/download/excel`, `/download/pdf`, `/download/pptx`) n'ont pas de dépendance au cache mémoire qui bloquerait après restart
- [ ] Tester : redémarrage Railway → export toujours téléchargeable (régénération depuis DB)

**Dépendances :** WP1A (pour la cohérence des données).  
**Durée estimée :** 30 min (vérification + suppression du cache si nécessaire).

---

## WP9 — PIN RATE LIMITER PERSISTENCE

**Objectif :** Migrer le rate limiter sur les tentatives PIN du cache mémoire vers un stockage persistant.

**Problème actuel :** Le rate limiter est en mémoire Python (Railway). Un redémarrage Railway remet à zéro tous les compteurs, permettant une attaque brute-force entre chaque redémarrage.

**Options :**
- A. Redis (recommandé) : TTL natif, atomicité, peu de code
- B. Supabase (table `pin_attempts`) : plus simple si pas de Redis, légèrement plus lent

**Actions (option B — Supabase, pas de Redis requis) :**
- [ ] Créer table `pin_attempts` : `(company_id, email, attempt_count, first_attempt_at, blocked_until)`
- [ ] Modifier `auth.py` : lecture/écriture de `pin_attempts` au lieu du dict mémoire
- [ ] Règle : 5 tentatives en 15 minutes → blocage 1 heure
- [ ] Nettoyer les tentatives anciennes (cron ou trigger)

**Validation :**
- [ ] 5 tentatives PIN incorrectes → "Trop de tentatives. Réessayez dans 1 heure."
- [ ] Redémarrage Railway → le blocage est maintenu
- [ ] Tentative valide après 1 heure → débloqué

**Dépendances :** Aucune (WP indépendant).  
**⚠️ Si option B : nécessite une migration SQL. À valider explicitement.**  
**Durée estimée :** 2–3h.

---

## WP10 — ADMIN DASHBOARD CLEANUP

**Objectif :** Nettoyer le dashboard superadmin des références aux plans supprimés.

**Actions :**
- [ ] Supprimer les colonnes / filtres POWER et ENTERPRISE de l'interface superadmin
- [ ] Vérifier que les stats agrégées affichent correctement FREE / PRO / SCALE (+ legacy groupés)
- [ ] Vérifier que le superadmin ne peut toujours pas accéder au contenu des analyses

**Validation :**
- [ ] Dashboard superadmin : seuls FREE, PRO, SCALE apparaissent dans les filtres de plan
- [ ] Stats correctes : distribution des plans reflète les comptes réels

**Dépendances :** WP1 (PLAN_DISPLAY correctement défini).  
**Durée estimée :** 1h.

---

## CRITÈRES DE RELEASE 1.0

La Release 1.0 est prête quand TOUS les items suivants sont vérifiés :

### Fonctionnel

- [ ] Inscription FREE → accès /app/chat → 1 analyse disponible → 3 interactions chat disponibles (mensuel)
- [ ] Inscription PRO → /checkout/pro → Stripe → webhook → plan='pro' → 30 analyses / 75 chat / 10 entités
- [ ] Inscription SCALE → /checkout/scale → Stripe → webhook → plan='scale' → 100 analyses / 500 chat / entités illimitées
- [ ] Achat Starter Pack (39€) → **+10 analyses bonus** (chat inchangé, aucun changement de quota)
- [ ] Achat Growth Pack (79€) → **+20 analyses bonus** (chat inchangé)
- [ ] Achat Scale Pack (239€) → **+80 analyses bonus** (chat inchangé)
- [ ] **Ordre de consommation** : bonus analyses consommées AVANT quota mensuel
- [ ] **Renouvellement mensuel** : quota mensuel recrédité, analyses bonus non consommées conservées
- [ ] Upgrade PRO→SCALE via Billing Portal Stripe
- [ ] Annulation → analyses bonus suspendues (inutilisables en FREE), conservées en base, réactivées à la re-souscription
- [ ] Paiement échoué → email Resend au client, accès maintenu pendant retry Stripe (7j)
- [ ] Redémarrage Railway → exports toujours téléchargeables (régénération depuis DB)

### Quotas

- [ ] FREE : quota analyse = 1, quota chat = 3 (mensuel)
- [ ] PRO : quota analyse = 30, quota chat = 75 (mensuel)
- [ ] SCALE : quota analyse = 100, quota chat = 500 (mensuel)
- [ ] **Aucune limite d'interactions par analyse dans le code** — quota mensuel uniquement
- [ ] Grep de `chat_per_analysis` dans le code → 0 résultat hors commentaires
- [ ] Grep de `per_analysis` dans le code de limitation → 0 résultat

### Sécurité

- [ ] Anonymisation active avant tout envoi à Claude API (anonymization_service.py)
- [ ] Table de correspondance alias → jamais envoyée à Anthropic
- [ ] RLS Supabase : impossibilité d'accéder aux données d'une autre company
- [ ] Rate limiter PIN persistant (WP9)

### Technique

- [ ] Zéro constante commerciale hardcodée hors de `product_catalog.py`
- [ ] `GET /api/billing/plans` retourne les bonnes valeurs (FREE=1/3, PRO=30/75, SCALE=100/500)
- [ ] CHECK constraint Supabase accepte 'pro' et 'scale' (WP6)
- [ ] Exports régénérés depuis DB après redémarrage Railway (WP8)
- [ ] Pas de `deploy_stripe.py` avec clés Stripe hardcodées en git (à supprimer ou chiffrer)
- [ ] Aucune clé Stripe dans le code source (`STRIPE_PRICE_*` = variables env uniquement)

### Interface

- [ ] Zéro mention de "15 analyses" dans le frontend
- [ ] Zéro mention de "info@finflate.com"
- [ ] Zéro mention de "illimité" pour le chat (chat = 3 / 75 / 500 selon le plan)
- [ ] Prix affichés : FREE=0€, PRO=149€, SCALE=349€
- [ ] Chat affiché : FREE=3/mois, PRO=75/mois, SCALE=500/mois
- [ ] CreditsModal affiche : "+X analyses" (jamais "+X interactions")
- [ ] CreditsModal utilise Stripe Checkout (pas mailto:)

### Terminologie (TERMINOLOGY.md)

- [ ] Le mot "Analyse" est utilisé partout à la place de "rapport", "scan", "run", "credit"
- [ ] Le mot "Interaction" est utilisé à la place de "message", "requête", "token"
- [ ] Le terme "Executive Capacity Pack" est utilisé, jamais "addon", "pack de crédits", "boost"
- [ ] Le terme "Collaborateur" est utilisé, pas "guest", "invité", "team member"

---

## SÉQUENCE D'EXÉCUTION

```
WP1A (Product Catalog)          ← Premier — tout dépend de lui
    ↓
WP2 (Quota Fix)                 ← Corollaire de WP1A (vérification résiduelle)
WP3 (Stripe Config)             ← Parallèle avec WP2 possible
    ↓
WP4 (Parcours SCALE + Credits)  ← Dépend de WP3
WP5 (Frontend Alignment)        ← Dépend de WP1A
WP6 (Legacy Cleanup)            ← Dépend de WP1A + WP3
    ↓
WP8 (vérif régénération)        ← 30 min seulement, peut être fait en parallèle
WP9 (PIN Rate Limiter)          ← Indépendant
WP10 (Admin Dashboard)          ← Dépend de WP1A

WP7 → 🚫 Release 1.1 — Conversation Memory Optimization
```

---

## VALIDATION FINALE — CONTRAT DE DÉVELOPPEMENT

**Toutes les règles métier sont désormais figées.**

Le contrat de développement de la Release 1.0 de Pepperyn est constitué des documents suivants :

| Document | Rôle |
|---|---|
| `PEPPERYN_BUSINESS_RULES_V1_FINAL.md` | Contrat fonctionnel complet — référence narrative |
| `PEPPERYN_DECISIONS_V1.md` | Référence technique — tables et constantes |
| `ADR_001_PRODUCT_CATALOG.md` | Architecture Decision Record — WP1A |
| `TERMINOLOGY.md` | Glossaire officiel — terminologie obligatoire |
| `RELEASE_1_CHECKLIST.md` | Checklist d'implémentation et de validation |

**Toute évolution future des règles métier devra passer par un ADR.**  
Un ADR doit contenir : contexte, décision, justification, alternatives écartées, conséquences.

**Le Product Catalog (WP1A) peut être construit sans ambiguïté.**  
Toutes les valeurs nécessaires sont dans `PEPPERYN_DECISIONS_V1.md` section 7 (PLAN_LIMITS).

**La Release 1.0 est prête à entrer dans sa phase d'implémentation.**  
Le prochain travail est exclusivement : **WP1A — Product Catalog**.

---

*Aucun code modifié. Aucun commit. Aucune migration. En attente de validation.*

---

*Ce document est mis à jour à chaque WP terminé. Aucun code modifié dans cette phase.*
