# WP1E — STABILIZATION REPORT
## Release 1.0 — Pepperyn

**Date :** 2026-07-14  
**Branche :** `release-1/wp1e-stabilization`  
**Commit de départ :** `5f6037d` (feat: WP1D — align frontend with Option B usage architecture)  
**Auteur de l'audit :** Claude Sonnet 4.6 + Fred Anciaux  

---

## LIMITES DE CET AUDIT

> **Cet audit est principalement statique.** Les conclusions ci-dessous sont issues d'une lecture du code source, des tests unitaires automatisés et de greps ciblés. Elles ne constituent pas une validation end-to-end en conditions réelles.

Les éléments suivants n'ont **pas** été réalisés :

- Aucun paiement réel effectué
- Aucun paiement Stripe Test Mode complet exécuté de bout en bout
- Aucun compte synthétique créé en base
- Aucun parcours FREE, PRO ou SCALE exécuté intégralement (navigation, Stripe, webhook, activation, affichage)
- Aucun test mobile réel (responsive analysé statiquement uniquement)
- Aucun test de collaboration réel avec deux sessions simultanées

**Conséquence :** les conclusions fonctionnelles (parcours FREE conforme, webhook idempotent, stock suspendu…) devront être **confirmées par des tests manuels ou end-to-end après application des correctifs**, avant de considérer la Release 1.0 comme validée en conditions réelles.

---

## VERDICT

```
NO-GO — CORRECTIONS REQUISES
```

**3 anomalies P0 bloquantes. 6 anomalies P1. 4 anomalies P2.**

Le système est architecturalement sain. Le backend, les tests et la logique d'usage sont stables (lecture statique).  
Les corrections requises concernent les surfaces commerciales, un parcours manquant et deux règles de gouvernance des entités.

---

## 1. BRANCHE ACTIVE

`release-1/wp1e-stabilization` — créée depuis `release-1/wp1d-frontend-alignment` (commit `5f6037d`).

---

## 2. BASELINE TECHNIQUE

### Backend — Tests
| Suite | Résultat |
|---|---|
| `test_product_catalog.py` | ✅ PASSED |
| `test_billing_migration.py` | ✅ PASSED |
| `test_usage_service.py` | ✅ PASSED |
| `test_rule_001_zero_manual_intervention.py` | ❌ 2 FAILED (connus) |
| `test_rule_002_zero_truncation.py` | ✅ PASSED |
| `test_rule_003_renderer_responsibility.py` | ❌ 2 FAILED (connus) |
| **Total** | **248 passed, 4 failed historiques** |

**Échecs PPTX historiques déjà connus (inchangés depuis avant WP1E) :**
- `TestEDMSourceValues::test_edm_source_values`
- `TestPPTXContent::test_pptx_has_20_slides`
- `TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`
- `TestRendererSelfContainment::test_pptx_handles_extreme_text_length`

**Suite EPM :** 5 erreurs de collection (`ModuleNotFoundError: No module named 'epm.types'`) — module hors scope Release 1.0.

**Aucun nouvel échec de test introduit par WP1A–WP1D.**

### Frontend — TypeScript
```
npx tsc --noEmit → EXIT CODE 0 (zéro erreur)
```

### Frontend — Build
Build Next.js confirmé par Fred sur machine locale Windows.  
Sandbox bloqué (SWC Linux binaire absent, DNS restreint) — limite d'environnement, non une erreur de code.

---

## 3. PARCOURS FREE

### Inscription directe FREE
| Point de contrôle | Statut | Source |
|---|---|---|
| Aucun passage par Stripe | ✅ | `register/page.tsx` → `signUpAdmin()` → Supabase uniquement |
| Plan enregistré = `free` | ✅ | `handle_new_user()` en DB |
| 1 analyse mensuelle | ✅ | `PLAN_LIMITS["free"].analyses = 1` |
| 3 interactions mensuelles | ✅ | `PLAN_LIMITS["free"].chat_monthly_cap = 3` |
| 1 entité maximum | ✅ | `PLAN_LIMITS["free"].max_entities = 1` |
| Deuxième analyse refusée | ✅ | Backend usage_service.py — quota check |
| Renouvellement mensuel affiché | ✅ | `renewal_date` retourné par API, affiché via WP1D |
| Aucun checkout créé | ✅ | `billing_service.py` bloque FREE explicitement |

### FREE avec Executive Capacity Pack suspendu
| Point de contrôle | Statut |
|---|---|
| Stock visible | ✅ `analyses_bonus_remaining` retourné même si suspendu |
| Stock inutilisable | ✅ `analyses_bonus_suspended: true` → quota quotidien non augmenté |
| Wording rassurant affiché | ✅ WP1D — "Aucune analyse ne sera perdue." |
| CTA vers PRO ou SCALE | ✅ Sidebar + CreditsModal |
| Aucune décrémentation du stock | ✅ `bonus_suspended` bloque la consommation en backend |

---

## 4. PARCOURS PRO

| Point de contrôle | Statut | Note |
|---|---|---|
| Route checkout PRO | ✅ | `/checkout/pro/page.tsx` fonctionnel |
| Compte créé avant Stripe | ✅ | Supabase d'abord, email confirm → redirect checkout |
| Price ID PRO depuis env | ✅ | `STRIPE_PRICE_PRO` — erreur explicite si absent |
| Mode `subscription` | ✅ | `billing_service.py` ligne 83 |
| Webhook idempotent | ✅ | `apply_stripe_webhook` RPC avec `stripe_event_id` unique |
| Double event → un seul effet | ✅ | RPC retourne `status: "duplicate"` |
| Plan `pro` activé | ✅ | webhook → `update_plan` → `companies.plan = 'pro'` |
| **Prix affiché = 149€/mois** | **⚠️ P1** | Correct dans upgrade/page.tsx mais **15 analyses/mois** (doit être 30) |
| **30 analyses mensuelles** | **❌ P0** | Upgrade page et PricingPlans affichent **15** — incorrect |
| **75 interactions mensuelles** | ✅ | Correct (catalog = 75) |
| Aucune valeur POWER | ✅ | POWER non exposé dans interface commerciale |

---

## 5. PARCOURS SCALE

| Point de contrôle | Statut | Note |
|---|---|---|
| **Route checkout SCALE** | **❌ P0** | `/checkout/scale` n'existe pas |
| **`register?plan=scale`** | **❌ P0** | `isPro` = `planParam === 'pro'` uniquement — plan=scale → flux FREE, pas Stripe |
| Prix affiché = 349€/mois | ✅ | Correct dans upgrade/page.tsx |
| **100 analyses mensuelles** | **❌ P1** | Upgrade et PricingPlans affichent **250** — incorrect |
| **500 interactions mensuelles** | ✅ | Correct (catalog = 500) |
| CTA SCALE → `/contact` | ⚠️ P1 | SCALE ne peut pas être acheté en ligne — redirection manuelle uniquement |
| Entités illimitées (None) | ✅ | `PLAN_LIMITS["scale"].max_entities = None` |

---

## 6. EXECUTIVE CAPACITY PACKS

### Contrat backend (correct)
| Pack | Analyses | Prix backend | Stripe env var |
|---|---|---|---|
| Starter Capacity Pack | 10 | 39,00 € | `STRIPE_PRICE_ADDON_STARTER` |
| Growth Capacity Pack | 20 | 79,00 € | `STRIPE_PRICE_ADDON_GROWTH` |
| Scale Capacity Pack | 80 | 239,00 € | `STRIPE_PRICE_ADDON_SCALE` |

### Divergences frontend (3 surfaces)

| Surface | Pack | Analyses affichées | Prix affiché | Correct ? |
|---|---|---|---|---|
| `upgrade/page.tsx` | Starter | +10 | **19€** | ❌ (39€) |
| `upgrade/page.tsx` | Growth | +**50** | **69€** | ❌ (20, 79€) |
| `upgrade/page.tsx` | Scale | +**200** | **199€** | ❌ (80, 239€) |
| `CreditsModal.tsx` | Starter | 10 | **19€** | ❌ (39€) |
| `CreditsModal.tsx` | Growth | **50** | **69€** | ❌ (20, 79€) |
| `CreditsModal.tsx` | Scale | **200** | **199€** | ❌ (80, 239€) |
| `PricingPlans.tsx` | Starter | +10 | **19€** | ❌ (39€) |
| `PricingPlans.tsx` | Growth | +**50** | **69€** | ❌ (20, 79€) |
| `PricingPlans.tsx` | Scale | +**200** | **199€** | ❌ (80, 239€) |
| `billing/success/page.tsx` | Growth Pack | +**50** | — | ❌ (20) |
| `billing/success/page.tsx` | Scale Pack | +**200** | — | ❌ (80) |

**Comportement backend (idempotence, consommation, stock) :**
| Point | Statut |
|---|---|
| Paiement crédite le bon compte | ✅ `metadata.company_id` vérifié |
| Quantité exacte depuis product_catalog | ✅ `pack.analyses_added` — source unique |
| Même event → une seule fois | ✅ RPC `stripe_event_id` idempotent |
| Stock consommé avant quota mensuel | ✅ `usage_service.py` — Option B |
| Pas d'interactions ajoutées | ✅ `add_bonus` → seul `bonus_analyses_remaining` |
| Pas de changement de plan | ✅ action `add_bonus` ≠ `update_plan` |
| Stock persist au renouvellement | ✅ colonne `companies.bonus_analyses_remaining` non réinitialisée |
| FREE conserve sans consommer | ✅ `analyses_bonus_suspended = True` si plan=free |

---

## 7. RENOUVELLEMENT / ANNULATION / RÉACTIVATION

| Scénario | Statut | Note |
|---|---|---|
| `analyses_count` réinitialisé | ✅ | Reset mensuel dans usage_service.py |
| `bonus_analyses_remaining` inchangé | ✅ | Option B — colonne companies |
| Date renouvellement correcte | ✅ | Premier du mois suivant UTC |
| Annulation → `customer.subscription.deleted` → `downgrade_free` | ✅ | billing_service.py l.265 |
| Stock Executive Capacity conservé après annulation | ✅ | `downgrade_free` ne touche pas `bonus_analyses_remaining` |
| Stock suspendu sur FREE | ✅ | `analyses_bonus_suspended` calculé dynamiquement |
| **`invoice.payment_failed` : noop uniquement** | **⚠️ P1** | Aucune rétrogradation, aucun email — comportement non défini |
| Réactivation → stock réactivé | ✅ | `bonus_suspended` recalculé à la prochaine requête |
| Aucune perte de stock | ✅ | Stock permanent en DB |

---

## 8. COLLABORATION / ENTITÉS / PIN

### PIN
| Point | Statut |
|---|---|
| `POST /api/auth/pin` — connexion Invité par PIN | ✅ Router `auth.py` |
| `POST /api/auth/pin-guest` — email + PIN | ✅ |
| Seul Admin peut changer le PIN | ✅ Route protégée admin Supabase |
| Rate-limiter brute-force | ✅ Mentionné dans le docstring |

### Entités
| Point | Statut | Note |
|---|---|---|
| Plan < PRO bloqué | ✅ | `PLAN_LEVEL.get(plan, 0) < PLAN_LEVEL["pro"]` |
| **Legacy aliases non reconnus** | **⚠️ P1** | `standard`, `standard_beta`, `premium` absents du `PLAN_LEVEL` local → niveau 0 → HTTP 403 |
| **max_entities non enforced** | **⚠️ P1** | PRO peut créer > 10 entités — limite produit non vérifiée dans le code |
| SCALE entités illimitées | ✅ | `max_entities = None` accepté dans usage_service |
| SCALE `None` sans crash | ✅ | Comparaisons avec `None` gérées (pas de `> None`) |

### Collaboration
| Point | Statut | Note |
|---|---|---|
| Admin peut inviter Collaborateur | 🔍 | Flux d'invitation non retrouvé dans les routers — à confirmer |
| Collaborateur connexion email+PIN | ✅ | `/api/auth/pin-guest` |
| Droits Collaborateur limités | 🔍 | Gouvernance fine non auditée — hors scope core WP1E |

---

## 9. AUDIT UI (statique — dev server non disponible en sandbox)

### Surfaces auditées

**Landing principale (`app/page.tsx`) :** Pas de prix visibles directement — renvoie vers `/upgrade`.

**Inscription FREE (`register/page.tsx`) :**
- ✅ Flux FREE sans Stripe
- ⚠️ P1 : Texte "15 analyses / mois" sur la confirmation PRO (ligne 198)
- ⚠️ P1 : Aucun flux `plan=scale` — redirige vers FREE

**Inscription PRO (`register/page.tsx` + `/checkout/pro`) :**
- ✅ Création compte → confirmation email → redirect `/checkout/pro`
- ✅ CheckoutProPage déclenche `POST /api/billing/checkout` avec `plan_or_addon: 'pro'`
- ✅ Erreur gérée avec CTA vers `/upgrade`

**Inscription SCALE :**
- ❌ P0 : Aucune route `/checkout/scale` — SCALE non achetable en ligne

**Page Upgrade (`upgrade/page.tsx`) :**
- ❌ P0/P1 : Quotas PRO (15) et SCALE (250) incorrects
- ❌ P1 : Prix et quantités des packs tous incorrects
- ⚠️ P1 : CTA SCALE → `/contact` uniquement
- ⚠️ P2 : Terme "interactions contextuelles" non remplacé par "échanges"
- ⚠️ P2 : "Crédits supplémentaires disponibles" → devrait dire "Executive Capacity Pack"

**Sidebar (ChatContainer.tsx) :**
- ✅ WP1D appliqué — quotas depuis API
- ⚠️ P2 : `MAX_CHAT_QUESTIONS_FREE = 3` et `LIMIT_MESSAGE` utilisent "interactions contextuelles"
- ✅ Pas de recalcul métier côté frontend

**Executive Capacity Modal (CreditsModal.tsx) :**
- ✅ Quotas affichés depuis API (Option B)
- ❌ P1 : Prix et quantités hardcodés dans `ADDONS` incorrects

**Settings (`settings/page.tsx`) :**
- ✅ WP1D appliqué — billingUsage depuis API
- ✅ Aucun fallback vers anciennes colonnes

**Page retour Stripe (`billing/success/page.tsx`) :**
- ❌ P1 : `PLAN_LABELS` affiche "+50 analyses" et "+200 analyses" pour Growth/Scale Pack

**Page CRM Admin / Growth Admin :**
- ⚠️ P2 : `superadmin.py` utilise `"pro": 59` comme MRR PRO — ancien prix (devrait être 149)

**PricingPlans.tsx (landing) :**
- ❌ P1 : 15 analyses PRO, 250 analyses SCALE, prix packs incorrects

---

## 10. AUDIT LEGACY

### Plans et prix — occurrences actives

| Terme | Fichier | Ligne | Classification |
|---|---|---|---|
| `"pro": 59` (ancien MRR) | `backend/routers/superadmin.py` | 195 | P2 — analytique interne |
| `"power": 129` | `backend/routers/superadmin.py` | 196 | P2 — analytique interne |
| `15 analyses / mois` (PRO) | `upgrade/page.tsx` | 22 | **P0** — affiché utilisateur |
| `15 analyses / mois` (PRO) | `PricingPlans.tsx` | 68 | **P0** — landing |
| `15 analyses / mois` (PRO) | `register/page.tsx` | 198 | **P0** — inscription |
| `250 analyses / mois` (SCALE) | `upgrade/page.tsx` | 30 | **P1** — affiché utilisateur |
| `250 analyses / mois` (SCALE) | `PricingPlans.tsx` | 93 | **P1** — landing |

### Packs — prix hardcodés incorrects

| Valeur | Fichiers | Classification |
|---|---|---|
| `addon_starter: 19€, +10` | `upgrade/page.tsx`, `CreditsModal.tsx`, `PricingPlans.tsx` | **P0** — prix trompeur |
| `addon_growth: 69€, +50` | idem | **P0** — prix et quantité trompeurs |
| `addon_scale: 199€, +200` | idem | **P0** — prix et quantité trompeurs |

### Vocabulaire utilisateur

| Terme | Fichiers | Classification |
|---|---|---|
| `interactions contextuelles` | `upgrade/page.tsx`, `PricingPlans.tsx`, `ChatContainer.tsx` | P1 — WP4/WP5 |
| `Crédits supplémentaires disponibles à la demande` | `upgrade/page.tsx` | P2 — WP4/WP5 |
| `info@finflate.com` | `contact/page.tsx`, `Footer.tsx`, `FaqSection.tsx`, mentions légales | P1 — email incorrect |

### Architecture legacy — résidus acceptables

| Terme | Localisation | Classification |
|---|---|---|
| `bonus_analyses` | Migrations SQL (historique) | Documentation historique — acceptable |
| `usage_limits.bonus_analyses` | Migration v10, v11b | Vestige Option A — commenté, non actif |
| `total_allowed` | `api.ts` (alias compat) | Suppression prévue WP5 |
| `bonus_analyses?` | `api.ts` (alias compat) | Suppression prévue WP5 |
| `PLANS_CATALOGUE supprimé` | `billing.py` (commentaire) | Documentation historique |
| `ADDON_QUANTITIES supprimé` | `billing_service.py` (commentaire) | Documentation historique |

---

## 11. AUDIT SÉCURITÉ

| Point | Statut | Note |
|---|---|---|
| Aucune clé `service_role` côté client | ✅ | Absence dans `frontend/lib/` et `frontend/app/` |
| Aucun secret versionné | ✅ | Clés lues depuis `os.getenv()` |
| Signature Stripe vérifiée avant traitement | ✅ | `stripe.Webhook.construct_event()` l.166 |
| `STRIPE_WEBHOOK_SECRET` vide → Stripe lève exception | ✅ | `construct_event` échoue sans secret valide |
| RPC `apply_stripe_webhook` : `REVOKE anon / authenticated` | ✅ | Migrations v10 ll.200–202 |
| RPC `apply_stripe_webhook` : `GRANT service_role` uniquement | ✅ | Migration v10 l.203 |
| Idempotence réelle : `stripe_event_id` unique | ✅ | Clé primaire `stripe_webhook_events` |
| `handle_new_user()` SECURITY DEFINER | ⚠️ Backlog | Trigger Supabase standard — à documenter |
| **`invoice.payment_failed` → noop** | ⚠️ P1 | Aucune action, aucun email — risque d'accès prolongé après échec paiement |
| Absence de données sensibles dans réponses d'erreur | ✅ | Logs internes, réponses HTTP génériques |

---

## 12. LISTE DES ANOMALIES

---

### P0 — BLOQUANTES RELEASE

**P0-001 — Quota PRO affiché : 15 analyses (doit être 30)**
- Scénario : Utilisateur visite `/upgrade`, PricingPlans (landing), inscription PRO
- Attendu : 30 analyses / mois (product_catalog.py l.140)
- Observé : "15 analyses / mois"
- Fichiers : `frontend/app/upgrade/page.tsx:22`, `frontend/components/landing/PricingPlans.tsx:68`, `frontend/app/register/page.tsx:198`
- Recommandation : Corriger les constantes hardcodées. Envisager chargement depuis `GET /api/billing/plans`
- WP : **WP4**

**P0-002 — Packs Executive Capacity : prix et quantités incorrects dans toutes les surfaces commerciales**
- Scénario : Utilisateur clique sur un pack depuis CreditsModal, upgrade, ou landing
- Attendu : Starter=10 analyses/39€, Growth=20/79€, Scale=80/239€ (product_catalog.py)
- Observé : Starter=10/19€, Growth=50/69€, Scale=200/199€
- Fichiers : `upgrade/page.tsx:37–39`, `CreditsModal.tsx:23–27`, `PricingPlans.tsx:164–166`, `billing/success/page.tsx:3–7`
- Recommandation : Aligner sur product_catalog ou charger depuis `GET /api/billing/plans`
- WP : **WP4**

**P0-003 — Parcours SCALE inexistant**
- Scénario : Utilisateur visite `/register?plan=scale` ou clique "Passer à SCALE"
- Attendu : Flux compte → checkout Stripe → activation SCALE
- Observé : `register/page.tsx` → `isPro = planParam === 'pro'` → plan=scale → flux FREE. Aucune page `/checkout/scale`.
- Fichiers : `frontend/app/register/page.tsx:36`, `frontend/app/checkout/` (dossier `scale` absent)
- Recommandation : Généraliser `isPro` en `isPayedPlan`, créer `/checkout/[plan]/page.tsx` générique, gérer PRO et SCALE
- WP : **WP4**

---

### P1 — IMPORTANTES AVANT LANCEMENT

**P1-001 — Quota SCALE affiché : 250 analyses (doit être 100)**
- Fichiers : `upgrade/page.tsx:30`, `PricingPlans.tsx:93`
- WP : WP4

**P1-002 — SCALE non achetable en ligne (CTA → /contact)**
- Observé : CTA SCALE → `/contact`, pas de checkout Stripe
- Lié à P0-003
- WP : WP4

**P1-003 — `invoice.payment_failed` : noop sans action**
- Risque : Abonné dont le renouvellement échoue conserve son accès PRO/SCALE indéfiniment
- Aucun email envoyé, aucune rétrogradation planifiée
- WP : WP2 (à définir avec Fred — règle produit requise)

**P1-004 — Legacy aliases (standard, standard_beta, premium) bloqués dans entities.py**
- `PLAN_LEVEL` local ne contient pas ces alias → `get(..., 0)` → niveau 0 → HTTP 403
- Un client `standard` (= PRO) ne peut pas créer d'entités
- Fichier : `backend/routers/entities.py:114`
- Recommandation : Remplacer `PLAN_LEVEL` local par `LEGACY_PLAN_ALIASES` + `PLAN_LIMITS` de product_catalog
- WP : **WP1E**

**P1-005 — `max_entities` non enforced dans entities.py**
- Un compte PRO peut créer > 10 entités sans blocage backend
- Fichier : `backend/routers/entities.py` — vérification du count absente
- WP : **WP1E**

**P1-006 — `info@finflate.com` exposé dans interface utilisateur**
- Email d'une société antérieure affiché dans contact, footer, FAQ, mentions légales
- Fichiers : `contact/page.tsx:71–73`, `Footer.tsx:26–27`, `FaqSection.tsx:225,356`, pages légales
- WP : WP4/WP5

**P1-007 — `billing/success/page.tsx` : PLAN_LABELS avec quantités de packs incorrectes**
- "Growth Pack (+50 analyses)" → doit être "+20 analyses"
- "Scale Pack (+200 analyses)" → doit être "+80 analyses"
- Fichier : `billing/success/page.tsx:4–6`
- WP : WP4

---

### P2 — MINEURES

**P2-001 — Terme "interactions contextuelles" non remplacé dans surfaces commerciales**
- Fichiers : `upgrade/page.tsx:14,22,30`, `PricingPlans.tsx:51,69,94`, `ChatContainer.tsx:20,48`
- Recommandation : Aligner sur "échanges de suivi" (nomenclature WP1D)
- WP : WP4/WP5

**P2-002 — "Crédits supplémentaires disponibles à la demande" (PRO features)**
- Devrait dire "Executive Capacity Pack disponible à la demande"
- Fichier : `upgrade/page.tsx:22`
- WP : WP4

**P2-003 — `superadmin.py` : MRR PRO = 59€ (ancien prix)**
- `_PLAN_MRR["pro"] = 59` — analytique interne uniquement, non visible utilisateur
- Fichier : `backend/routers/superadmin.py:195–196`
- WP : WP4

**P2-004 — Suite EPM : 5 erreurs de collection (`ModuleNotFoundError: epm.types`)**
- Module `epm.types` introuvable dans le PYTHONPATH de test
- Tests EPM non exécutables sans configuration supplémentaire
- WP : Backlog technique (hors Release 1.0)

---

## 13. DONNÉES DE TEST

Aucune donnée de test synthétique créée en production.  
Aucun compte Stripe test utilisé.  
Audit statique du code uniquement.

---

## 14. FICHIERS CRÉÉS OU MODIFIÉS

| Fichier | Action |
|---|---|
| `docs/release-1/WP1E_STABILIZATION_REPORT.md` | Créé |

Aucune modification de code dans cette mission.

---

## 15. GIT STATUS

```
Branche : release-1/wp1e-stabilization
Commit  : 5f6037d (point de départ WP1E)
```

Fichiers modifiés non commités :
- `frontend/tsconfig.tsbuildinfo` (artifact de build)
- `docs/release-1/WP1E_STABILIZATION_REPORT.md` (nouveau — à commiter après validation)

Aucun push effectué. Aucun fichier de code modifié.

---

## 16. CONFIRMATION

- ✅ Aucun push effectué
- ✅ Aucun autre WP commencé
- ✅ Aucune donnée de production modifiée
- ✅ Aucun paiement réel effectué
- ✅ Aucun commit de correction créé

---

## 17. RECLASSIFICATION PAR CHANTIER

---

### WP4A — COMMERCIAL CATALOG FRONTEND

**Objectif :** Toutes les surfaces commerciales alimentées par le Product Catalog ou `GET /api/billing/plans`. Zéro constante commerciale locale dans le frontend.

| Anomalie | Gravité | Description |
|---|---|---|
| P0-001 | **P0** | Quota PRO : 15 → 30 (`upgrade/page.tsx`, `PricingPlans.tsx`, `register/page.tsx`) |
| P0-002 | **P0** | Packs : prix et quantités incorrects (3 fichiers × 3 packs) |
| P1-001 | P1 | Quota SCALE : 250 → 100 |
| P1-006 | P1 | `info@finflate.com` → `contact@pepperyn.com` (contact, footer, FAQ, mentions légales) |
| P1-007 | P1 | `billing/success` PLAN_LABELS : +50/+200 → +20/+80 analyses |
| P2-001 | P2 | "interactions contextuelles" → "échanges de suivi" |
| P2-002 | P2 | "Crédits supplémentaires disponibles" → "Executive Capacity Pack disponible" |
| P2-003 | P2 | `superadmin.py` MRR PRO = 59€ → 149€ (analytique interne) |

**Fichiers concernés :**
`frontend/app/upgrade/page.tsx` · `frontend/components/landing/PricingPlans.tsx` · `frontend/app/register/page.tsx` · `frontend/components/ui/CreditsModal.tsx` · `frontend/app/app/billing/success/page.tsx` · `frontend/app/contact/page.tsx` · `frontend/components/landing/Footer.tsx` · `frontend/components/landing/FaqSection.tsx` · pages légales · `backend/routers/superadmin.py`

---

### WP4B — SCALE SELF-SERVICE JOURNEY

**Objectif :** Un utilisateur peut souscrire à SCALE en ligne, sans contact manuel, avec le même niveau de qualité que le parcours PRO existant.

| Anomalie | Gravité | Description |
|---|---|---|
| P0-003 | **P0** | Parcours SCALE complet inexistant (register + checkout + activation + retour) |

Cette anomalie regroupe ce qui a été initialement séparé en P0-003 et P1-002 : ce sont deux symptômes du même problème. La route `/checkout/scale` absente, le `register?plan=scale` ignoré, et le CTA `/contact` sont trois manifestations d'un seul chantier.

**Fichiers à créer ou modifier :**
`frontend/app/register/page.tsx` (généraliser `isPro` → `isPaidPlan`) · `frontend/app/checkout/[plan]/page.tsx` (à créer, route générique PRO + SCALE)

---

### WP4C — ENTITY GOVERNANCE

**Objectif :** Les limites d'entités sont réellement appliquées côté backend, avec des erreurs utilisateur claires.

| Anomalie | Gravité | Description |
|---|---|---|
| P1-004 | P1 | Legacy aliases (`standard`, `standard_beta`, `premium`) → niveau 0 → HTTP 403 erroné |
| P1-005 | P1 | `max_entities` non enforced : PRO peut créer > 10 entités |

**Règles à implémenter :**
- FREE : 1 entité maximum
- PRO : 10 entités maximum
- SCALE : illimité (`max_entities = None`)
- Legacy aliases : résolution via `product_catalog.LEGACY_PLAN_ALIASES` + `PLAN_LIMITS`

**Fichier :** `backend/routers/entities.py`

---

### WP4D — PAYMENT FAILURE POLICY

**Statut : Décision métier requise avant tout code.**

#### Contexte actuel
`invoice.payment_failed` → `action: "noop"` dans `billing_service.py`. Aucune action déclenchée, aucun email envoyé. Un abonné dont le renouvellement échoue conserve son accès PRO ou SCALE indéfiniment.

#### Options disponibles

**Option 1 — Notification uniquement (risque élevé)**
- Email envoyé à l'utilisateur
- Accès maintenu sans limite de temps
- Risque : accès gratuit indéfini après échec paiement

**Option 2 — Grace period + rétrogradation automatique (recommandé)**
- J+0 : email "paiement échoué, mettez à jour votre carte"
- J+3 : relance email
- J+7 : rétrogradation automatique vers FREE
- Stock Executive Capacity Pack conservé mais suspendu (règle existante FREE)
- Réactivation immédiate dès paiement réussi
- Comportement des Collaborateurs pendant la grace period : accès maintenu
- Comportement après rétrogradation : Collaborateurs bloqués (plan FREE = admin seul)

**Option 3 — Suspension immédiate**
- Accès suspendu dès le premier échec
- Impact utilisateur fort — non recommandé pour des abonnements mensuels

**Option 4 — Délégation à Stripe**
- Stripe Smart Retries (3–4 tentatives sur ~15 jours)
- Stripe envoie ses propres emails de recouvrement
- Pepperyn reçoit `customer.subscription.deleted` uniquement si Stripe abandonne
- Rétrogradation déclenchée seulement à la suppression par Stripe
- Avantage : zéro code de grace period à écrire
- Risque : comportement dépendant de la configuration Stripe Dashboard

#### Recommandation
**Option 4 (délégation Stripe) en phase de lancement**, car :
- Stripe Smart Retries est activé par défaut et optimisé
- `customer.subscription.deleted` est déjà géré et testé
- Zéro dette technique de grace period à maintenir
- Acceptable pour un lancement : risque financier limité sur une base d'abonnés restreinte

Compléter avec un email Pepperyn sur `invoice.payment_failed` pour avertir l'utilisateur (une seule ligne de notification — pas de logique de rétrogradation).

**Décision requise :** Option 4 + email de notification, ou choix différent ?

---

## 18. ORDRE DE CORRECTION RECOMMANDÉ

```
WP4A → WP4B → WP4C → Décision WP4D → Validation end-to-end réelle
```

**Justification :**

1. **WP4A en premier** : les anomalies P0-001 et P0-002 sont visibles immédiatement par tout utilisateur sur la page `/upgrade` et la landing. Elles créent une promesse commerciale fausse (prix, quantités). Elles sont indépendantes de Stripe et ne nécessitent aucune décision métier.

2. **WP4B ensuite** : le parcours SCALE peut être développé une fois les surfaces commerciales correctes, pour éviter d'aligner un checkout sur des données qui vont changer. WP4B dépend de WP4A (les prix affichés dans la confirmation doivent être corrects).

3. **WP4C après** : gouvernance des entités est un correctif backend ciblé, indépendant des deux précédents. Peut être parallélisé avec WP4B si les ressources le permettent.

4. **WP4D après décision** : aucun code tant que la règle produit n'est pas définie.

5. **Validation end-to-end en dernier** : parcours complets avec Stripe Test Mode et comptes synthétiques, après correction des P0 et P1 critiques.

---

## 19. ÉLÉMENTS BLOQUANT LA RELEASE

```
P0-001 — Quota PRO affiché incorrect (15 au lieu de 30)
P0-002 — Prix et quantités des packs tous incorrects
P0-003 — Parcours SCALE inexistant
```

Ces trois anomalies sont bloquantes car elles constituent soit une promesse commerciale fausse visible par l'utilisateur (P0-001, P0-002), soit un parcours de vente inopérant pour un plan entier (P0-003).

Les P1 (P1-004, P1-005 entity governance) sont importantes avant lancement mais ne bloquent pas la Release si P0 sont levés et si la base de comptes initiale est essentiellement PRO.

---

## 20. ÉLÉMENTS NÉCESSITANT UNE DÉCISION MÉTIER

| Décision | WP | Description |
|---|---|---|
| Politique `invoice.payment_failed` | WP4D | Grace period, durée, comportement collaborateurs, comportement stock |
| CTA SCALE | WP4B | Self-service en ligne ou maintien `/contact` pour la Release 1.0 ? |
| `info@finflate.com` | WP4A | Adresse de remplacement confirmée (contact@pepperyn.com ?) |

---

## 21. SECURITY BACKLOG

| Élément | Risque | Action |
|---|---|---|
| `handle_new_user()` SECURITY DEFINER | Faible (trigger Supabase standard) | Documenter, prévoir audit Supabase RLS complet post-Release 1.0 |
| Suite EPM non exécutable | Nul (module hors Release 1.0) | Corriger PYTHONPATH dans un sprint dédié |

---

*Rapport généré le 2026-07-14 — WP1E Stabilization Audit (statique)*  
*Validation end-to-end réelle : à planifier après correction des P0 et P1*
