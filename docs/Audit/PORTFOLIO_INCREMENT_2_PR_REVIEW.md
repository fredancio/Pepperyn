# PORTFOLIO INTELLIGENCE — Incrément 2 — PR Review

**Date :** 2026-08-05
**Branche :** `feature/portfolio-home-increment-2-2026-08-05` (basée sur `feature/portfolio-home-increment-1-2026-08-05`, non fusionnée)
**Cadrage :** GO IMPLEMENT — Portfolio Intelligence Increment 2, suite à `docs/Product/portfolio-card-review/` (Portfolio Card Review, verdict approuvé).
**Statut :** non fusionnée, en attente de revue.

---

## 1. Fichiers modifiés

| Fichier | Nature |
|---|---|
| `backend/models/decision_arc.py` | `BriefingItem.age_days` (nouveau champ) ; `PortfolioCard.other_active_count` et `why_it_matters_display` (nouveaux champs). |
| `backend/services/arc_service.py` | `_arc_to_briefing_item` expose `age_days` ; `build_review_briefing` — nouvelle sémantique de `limit` ; nouvelle fonction pure `_is_why_it_matters_distinct` ; `build_portfolio_briefing` — compteur, why_it_matters filtré, tri à 3 clés. |
| `backend/routers/arcs.py` | Correction du même piège `limit=0` au niveau de la route `GET /api/review-briefing`. |
| `backend/tests/test_review_briefing.py` | +4 tests (sémantique de `limit`). |
| `backend/tests/test_portfolio_briefing.py` | +21 tests (compteur, distinction why_it_matters, tie-break). |
| `frontend/lib/types.ts` | `BriefingItem.age_days` (requis) ; `PortfolioCard.other_active_count`, `why_it_matters_display` (additifs). |
| `frontend/components/chat/PortfolioHome.tsx` | Carte reconstruite en hiérarchie à 7 niveaux. |
| `frontend/components/chat/__tests__/PortfolioHome.test.tsx` | Réécrit — +12 tests (contexte temporel, compteur, why_it_matters filtré, périmètre strict). |
| `frontend/components/chat/__tests__/ReviewBriefing.test.tsx` | `makeItem()` complété avec `age_days` (cohérence de type uniquement, aucun changement de comportement testé). |

Aucune migration. Aucun nouveau concept de domaine. Aucun fichier hors de ce périmètre modifié.

---

## 2. Comportement livré

### Mission 1 — Contexte temporel

`top_item.temporal_context` (déjà généré côté backend, déjà conforme aux règles — aucun gabarit existant n'utilisait "à traiter aujourd'hui" ou équivalent) est désormais affiché sur la carte, en position 4 de la hiérarchie. Aucune génération de texte côté frontend — affichage pur d'un champ déjà calculé. Testé explicitement : aucune des trois formulations interdites n'apparaît nulle part sur l'écran rendu.

### Mission 2 — Compteur

`other_active_count` compte, par client, les points dont `priority != "closed"`, à l'exclusion du point déjà affiché (`top_item`). Un point clos ne demande plus de préparation — il n'est jamais compté (voir décision documentée dans `PORTFOLIO_INFORMATION_HIERARCHY.md`). Affiché uniquement si `> 0`, au singulier ("+1 autre point à suivre") ou au pluriel ("+2 autres points à suivre").

### Mission 3 — why_it_matters filtré

Fonction pure `ArcService._is_why_it_matters_distinct(text)` : renvoie `False` pour `None` et pour un ensemble fermé et documenté de quatre textes jugés redondants avec l'icône de priorité, le statut ou le contexte temporel (voir `PORTFOLIO_INFORMATION_HIERARCHY.md` §3.2) :

- *"Toujours sans décision confirmée après au moins une revue."*
- *"Décision encore en attente."*
- *"Exécution en cours."*
- *"Statut en cours de traitement."*

Deux textes sont jugés distincts et donc affichés :

- *"Effet pas encore confirmé dans une analyse."* — précise quelle preuve manque, information absente du titre/priorité/contexte temporel.
- *"Apprentissage en attente."* — clarifie qu'un point "Fait" n'est pas totalement terminal, nomme l'action résiduelle.

`why_it_matters_display` est calculé côté backend uniquement, sur `PortfolioCard` — `top_item.why_it_matters` (consommé par le Review Briefing existant) n'est jamais modifié ni filtré. Aucun texte n'est inventé : la fonction ne fait que choisir, parmi des gabarits déjà existants et déjà testés, lesquels passer à l'affichage.

### Mission 4 — Tri

Tri à trois clés dans `build_portfolio_briefing` :

1. **Priorité** du point le plus prioritaire du client (`BRIEFING_PRIORITY_ORDER` — urgent, à vérifier, fait, clos). Inchangé depuis l'Incrément 1.
2. **Ancienneté décroissante** (`age_days`, le plus ancien en premier) — corrige le tie-break accidentel identifié par la Portfolio Card Review (`updated_at desc` de la requête SQL, sans rapport avec l'ancienneté réelle du point).
3. **Nom du client**, ordre alphabétique — tie-break final stable, uniquement pour garantir un ordre déterministe quand priorité et ancienneté sont identiques.

`age_days` est calculé dans `_arc_to_briefing_item`, une valeur par branche de statut, déjà cohérente avec le texte `temporal_context` correspondant :

| Statut | Date source de `age_days` |
|---|---|
| `intention` | `created_at` |
| `execution`, complète | `execution_updated_at` ou, à défaut, `decision_confirmed_at` |
| `execution`, en cours | `decision_confirmed_at` ou, à défaut, `updated_at` |
| `consequences_linked` / `learning_proposed` | `updated_at` |
| `closed` | `closed_at` |
| statut inattendu (fallback) | `updated_at` |

Aucune matérialité financière introduite, conformément à la consigne.

### Mission 5 — Sémantique de `limit`

`build_review_briefing(limit: Optional[int] = 5)` :

- `limit=None` → aucune limite, tous les items actifs retournés.
- `limit=0` → zéro résultat, littéral.
- `limit > 0` → au plus `limit` items.
- `limit < 0` → `ValueError` explicite.

`build_portfolio_briefing` appelle désormais `limit=None` explicitement, remplaçant l'ancienne valeur arbitraire `limit=1000`. La route `GET /api/review-briefing` (qui plafonne toujours à 5, comportement externe inchangé) a été corrigée du même piège : `min(limit, 5) if limit else 5` (où `limit=0` retombait silencieusement sur 5) devient `max(0, min(limit, 5))` (où `limit=0` renvoie bien 0).

### Mission 6 — Carte

Hiérarchie finale, dans l'ordre : priorité → nom du client → titre → contexte temporel → why_it_matters (si distinct) → compteur (si > 1) → action unique ("Préparer cette revue"). Aucun élément hors périmètre ajouté — vérifié explicitement par un test comptant les éléments interactifs de la carte (`getAllByRole('button')` → longueur 1).

---

## 3. Résultats des tests

| Suite | Résultat |
|---|---|
| `backend/tests/test_portfolio_briefing.py` + `test_review_briefing.py` | 48 passed |
| Suite backend complète (hors 3 fichiers en échec de collecte pré-existant, sans rapport avec ce changement — `test_executive_decision_model.py`, `tests/epm/`, `test_temporal_normalizer.py`) | 943 passed, 8 failed (pré-existants : slides PPTX, variables Stripe — inchangés avant/après ce commit), 1 skipped |
| `frontend` — `PortfolioHome.test.tsx` + `ReviewBriefing.test.tsx` + `InputBar.prefill.test.tsx` | 30 passed (0 régression) |
| `npm run build` (production) | Succès — `/app/portfolio` toujours prérendue statiquement, 24/24 pages générées |

---

## 4. Écarts par rapport à la demande

Aucun écart de périmètre. Deux précisions d'implémentation, documentées ici par transparence :

1. **Classification de "Apprentissage en attente."** — la Portfolio Card Review l'avait notée comme apportant "peu" de valeur (même catégorie que les textes finalement jugés redondants). En implémentant la fonction pure, un examen plus strict (le texte clarifie que "Fait" n'est pas terminal, information absente ailleurs sur la carte) l'a reclassée comme distincte. Reclassification documentée dans le code (`arc_service.py`) et ci-dessus (section 2, Mission 3) — cohérente avec le principe déjà énoncé par Fred ("uniquement lorsqu'il ajoute une information non redondante"), pas une déviation de la règle.
2. **Correction de la route `GET /api/review-briefing`** (section 2, Mission 5) — non explicitement demandée mais directement dans le périmètre : c'est exactement le même bug de convention `limit=0` falsy, à un niveau au-dessus de la fonction visée par la Mission 5. Corrigée avec le même raisonnement plutôt que laissée en incohérence à un appel de distance.

---

## 5. Verdict

**APPROVED.**

Périmètre strictement respecté (les 6 missions, rien de plus). Zéro régression mesurée sur les deux suites de tests et le build. Toutes les règles de non-affichage (jamais d'injonction, jamais de texte inventé, jamais de matérialité financière introduite) sont vérifiées par des tests explicites, pas seulement par relecture de code.

---

PORTFOLIO INTELLIGENCE
INCREMENT 2 IMPLEMENTED.
READY FOR REVIEW.
