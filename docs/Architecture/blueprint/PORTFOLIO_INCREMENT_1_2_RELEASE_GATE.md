# PORTFOLIO INTELLIGENCE — RELEASE GATE, INCRÉMENTS 1 & 2

**Date :** 2026-08-05
**Périmètre :** intégration sur `main` des Incréments 1 (écran minimal) et 2 (complétude de la carte) de Portfolio Intelligence, précédemment approuvés séparément (`PORTFOLIO_CARD_REVIEW.md`, `PORTFOLIO_INCREMENT_2_PR_REVIEW.md`) mais jamais fusionnés.

---

## 1. Mission 1 — Pré-flight

**Commits confirmés avant toute fusion :**

| Référence | Commit |
|---|---|
| `main` (avant fusion) | `74a796f` |
| Terminal Incrément 1 | `3f6435d` (branche `feature/portfolio-home-increment-1-2026-08-05`) |
| Terminal Incrément 2 | `08a2451` (branche `feature/portfolio-home-increment-2-2026-08-05`) |

**Linéarité vérifiée** par `git merge-base` :
- `main` ↔ Incrément 1 : base commune = `74a796f` (Incrément 1 part directement de `main`).
- Incrément 1 ↔ Incrément 2 : base commune = `3f6435d` (Incrément 2 part directement du terminal d'Incrément 1).
- `git merge-base --is-ancestor` confirme l'ascendance stricte dans les deux cas.

**Working tree** : zéro fichier tracké modifié avant fusion. Seuls des éléments non trackés et hors périmètre étaient présents (`.env.example`, `Démo/`, `README.md`, `_BACKUP_EXTERNE_HORS_GIT/`, `archive/`, `backend/epm/`, `backend/tests/epm/`, `backend/tools/`, `config.yaml`, `data/`, `e2e-campaign-1/`, `leadgen/`, `main.py`, `pepperyn_sales_brain_v1/`, `pepperyn_sales_engine_v3/`, `requirements.txt`) — confirmés non inclus dans les fusions (voir listes de fichiers modifiés, sections 2 et 3).

**Graphe simplifié :**

```
main (74a796f)
  └─ Incrément 1 (3f6435d)
       └─ Incrément 2 (08a2451)
```

Relation strictement linéaire — fusion autorisée à procéder.

---

## 2. Mission 2 — Fusion Incrément 1

**Commande :** `git merge --no-ff feature/portfolio-home-increment-1-2026-08-05`
**Commit de fusion :** `ae79a9e`
**Fichiers modifiés (10)** : `backend/models/decision_arc.py`, `backend/routers/arcs.py`, `backend/services/arc_service.py`, `backend/tests/test_portfolio_briefing.py`, `frontend/app/app/portfolio/page.tsx`, `frontend/components/chat/ChatContainer.tsx`, `frontend/components/chat/PortfolioHome.tsx`, `frontend/components/chat/__tests__/PortfolioHome.test.tsx`, `frontend/lib/arc-api.ts`, `frontend/lib/types.ts` — liste identique à celle annoncée pour l'Incrément 1, aucun fichier hors périmètre.

**Validation après fusion :**

| Vérification | Résultat |
|---|---|
| Tests backend ciblés (`test_portfolio_briefing.py` + `test_review_briefing.py`) | 31/31 verts |
| Suite backend complète | 926 passés, **8 échecs préexistants** (identiques, voir liste section 5), 1 skip |
| Suite frontend Jest | 23/23 verts |
| Build production Next.js | Réussi, route `/app/portfolio` présente (3.09 kB, 90.4 kB First Load JS) |
| Navigation Portefeuille → Review Briefing | Confirmée par inspection : `PortfolioHome.tsx` `handlePrepareReview` → `router.push('/app/chat?entity=' + entityId)` ; `ChatContainer.tsx:98` lit `searchParams.get('entity')` au montage |

Aucune régression détectée — poursuite autorisée vers l'Incrément 2.

---

## 3. Mission 3 — Fusion Incrément 2

**Commande :** `git merge --no-ff feature/portfolio-home-increment-2-2026-08-05`
**Commit de fusion :** `771e7ae`
**Fichiers modifiés (10)** : `backend/models/decision_arc.py`, `backend/routers/arcs.py`, `backend/services/arc_service.py`, `backend/tests/test_portfolio_briefing.py`, `backend/tests/test_review_briefing.py`, `docs/Architecture/blueprint/PORTFOLIO_INCREMENT_2_PR_REVIEW.md`, `frontend/components/chat/PortfolioHome.tsx`, `frontend/components/chat/__tests__/PortfolioHome.test.tsx`, `frontend/components/chat/__tests__/ReviewBriefing.test.tsx`, `frontend/lib/types.ts` — liste identique à celle annoncée pour l'Incrément 2, aucun fichier hors périmètre.

**Validation après fusion :**

| Vérification | Résultat |
|---|---|
| Tests backend ciblés | 48/48 verts |
| Suite backend complète | **943 passés**, 8 échecs préexistants (identiques), 1 skip |
| Suite frontend Jest | **30/30 verts** |
| Build production Next.js | Réussi, route `/app/portfolio` présente (3.22 kB, 90.5 kB First Load JS) |

Zéro régression détectée. Les deux incréments restent traçables séparément dans l'historique (`3f6435d`/`ae79a9e` pour l'Incrément 1, `7a3a4ca`/`08a2451`/`771e7ae` pour l'Incrément 2, merges `--no-ff` distincts).

---

## 4. Mission 4 — Validation métier (16 points)

Vérifiée sur `main` fusionné, par lecture de code (`arc_service.py::build_portfolio_briefing`, `PortfolioHome.tsx`) et par les tests existants de `test_portfolio_briefing.py`.

| # | Comportement | Vérifié |
|---|---|---|
| 1 | Une carte par client concerné | Oui — regroupement par `entity_id` (`by_entity` dict), `TestPortfolioGrouping::test_one_card_per_entity` |
| 2 | Tri primaire par priorité | Oui — `BRIEFING_PRIORITY_ORDER` en première clé de tri |
| 3 | Tri secondaire par ancienneté à égalité de priorité | Oui — `-age_days` en deuxième clé, `TestPortfolioTieBreak::test_older_point_ranks_first_within_same_priority` |
| 4 | Tie-break final stable par nom de client | Oui — `entity_name.lower()` en troisième clé, `test_final_tie_break_by_entity_name_when_priority_and_age_equal` |
| 5 | Nom du client visible | Oui — `card.entity_name` affiché, niveau 2 de la hiérarchie |
| 6 | Point principal visible | Oui — `card.top_item.title`, niveau 3 |
| 7 | Contexte temporel visible et factuel | Oui — `card.top_item.temporal_context`, généré par `_arc_to_briefing_item` (ex. "Recommandé il y a 45 jours") |
| 8 | Aucune injonction non prouvable ("À traiter aujourd'hui") | Oui — tous les gabarits de `temporal_context` sont descriptifs, jamais impératifs |
| 9 | Compteur absent quand aucun autre point | Oui — rendu conditionnel `card.other_active_count > 0`, `TestPortfolioCounter::test_zero_when_only_one_active_point` |
| 10 | Compteur exact quand plusieurs points | Oui — `test_counts_other_active_points_excluding_the_one_shown` (3 points → top_item + 2) |
| 11 | `why_it_matters` affiché seulement si distinct | Oui — filtré par `_is_why_it_matters_distinct`, ensemble fermé de 4 textes redondants, `TestPortfolioWhyItMattersDisplay` |
| 12 | Action unique "Préparer cette revue" | Oui — un seul `<button>` par carte, confirmé par le test de périmètre strict (`getAllByRole('button')` longueur 1) |
| 13 | Client correctement pré-sélectionné dans le Review Briefing | Oui — `handlePrepareReview` → `/app/chat?entity=${entityId}` → lu par `ChatContainer` au montage |
| 14 | Aucun score opaque | Oui — aucun champ de score dans `PortfolioCard` ni dans le rendu |
| 15 | Aucun nouveau concept métier | Oui — pur regroupement de `BriefingItem` existant, aucune nouvelle table, aucun nouveau calcul de domaine |
| 16 | Aucune donnée financière ajoutée à la carte | Oui — grep sur mots-clés financiers (revenu, marge, montant, CA) dans le périmètre Portfolio : aucune occurrence |

Les 16 points sont conformes.

---

## 5. Mission 5 — Validation de `limit`

| Cas | Comportement vérifié |
|---|---|
| `limit=None` | Illimité — `build_review_briefing(limit=None)` retourne tous les items actifs (`test_limit_none_returns_all_items`) |
| `limit=0` | Zéro élément littéral — jamais réinterprété comme "non fourni" (`test_limit_zero_returns_empty_list_literally`) |
| `limit<0` | `ValueError` explicite au niveau service (`test_negative_limit_raises_value_error`) |
| Valeur `1000` | N'existe plus nulle part dans le code — `build_portfolio_briefing` appelle désormais `limit=None` explicitement. Seule trace : un commentaire historique expliquant la correction |
| Anciens appels | Comportement par défaut inchangé — `limit` non fourni retourne toujours 5 éléments (`test_default_limit_unchanged_at_five`) |
| Route `GET /api/review-briefing` | Applique sa propre convention documentée : `max(0, min(limit, 5))` — `limit=0` renvoie 0, `limit<0` est ramené à 0 (convention de clamp assumée à ce niveau, distincte du `ValueError` du service, documentée dans le code et dans `PORTFOLIO_INCREMENT_2_PR_REVIEW.md`) |

**8 échecs backend préexistants (identiques avant et après les deux fusions, non liés à Portfolio Intelligence) :**
`test_edx_002.py::test_pptx_generates_without_edx002_shows_methodology`, `test_edx_002.py::test_pptx_has_17_slides_with_edx002`, `test_product_catalog.py::TestRobustness::test_20_validate_stripe_price_ids_returns_all_false_without_vars`, `test_product_catalog.py::TestRobustness::test_20_pack_stripe_price_id_property_without_env`, `test_rule_001_zero_manual_intervention.py::TestEDMSourceValues::test_edm_source_values`, `test_rule_001_zero_manual_intervention.py::TestPPTXContent::test_pptx_has_20_slides`, `test_rule_003_renderer_responsibility.py::TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`, `test_rule_003_renderer_responsibility.py::TestRendererSelfContainment::test_pptx_handles_extreme_text_length`.

---

## 6. Mission 6 — Review visuelle

Trois rendus réels capturés depuis le composant `PortfolioHome.tsx` non modifié (rendu React Testing Library, HTML du DOM réellement produit) :

- **Scénario A** — client avec un seul point actif (Dupont & Fils SARL, urgent, 45 jours) : `why_it_matters` redondant masqué, compteur absent.
- **Scénario B** — client avec plusieurs points actifs (Atelier Martin, à vérifier, 12 jours) : compteur "+2 autres points à suivre" et `why_it_matters` distinct tous deux affichés.
- **Scénario C** — trois clients de même priorité (urgent), triés par ancienneté décroissante : Boulangerie Girard (60j) → Cabinet Lemoine (38j) → Atelier Nguyen (22j).

**Évaluation :**
- Lisibilité 3 secondes : tenue sur les trois scénarios — icône, nom, titre immédiatement lisibles.
- Hiérarchie visuelle : nom du client en gras et plus grand, champs secondaires (contexte temporel, compteur) en gris atténué, action unique en bouton bleu à fort contraste — hiérarchie correcte.
- Longueur de texte : titres longs tronqués proprement (`truncate`), aucun débordement observé.
- Visibilité de l'action : bouton "Préparer cette revue" identique et visible sur les trois scénarios.

**Deux observations documentées (aucune modification apportée à l'UX, conformément à la consigne) :**
1. Le scénario B (4 lignes secondaires empilées : temporel, why_it_matters, compteur) est le plus dense — encore lisible en 3 secondes, mais à surveiller si la liste s'allonge.
2. `why_it_matters_display` utilise la même couleur de texte foncée que le nom du client (`text-[#1A1A2E]`) plutôt que le gris atténué utilisé pour le contexte temporel et le compteur — légère inversion de hiérarchie visuelle, à corriger éventuellement lors de l'Incrément 3.

---

## 7. Mission 7 — Gouvernance

`docs/Architecture/PRODUCT_BOARD.md` mis à jour sur sa branche canonique dédiée (`governance/portfolio-release-gate-product-board-2026-08-05`, commit `64e9670`, non fusionnée) :
- Incrément 1 : DONE, fusionné (`ae79a9e`).
- Incrément 2 : DONE, fusionné (`771e7ae`).
- État réel des tests reporté (943 passés / 8 échecs préexistants / 1 skip backend, 30/30 frontend).
- `main` marqué à jour dans les sections Capability, Dernier incrément livré et Métriques.
- Incrément 3 (état vide honnête) proposé en section 5 — **non ouvert**.
- Aucune autre copie de gouvernance ni document Legacy modifié.

---

## 8. État final de `main`

```
771e7ae (HEAD -> main) merge: Portfolio Intelligence — Incrément 2 (Release Gate, Mission 3)
├─ 08a2451 PORTFOLIO_INCREMENT_2_PR_REVIEW.md — APPROVED
├─ 7a3a4ca Portfolio Intelligence — Incrément 2 (card completeness)
ae79a9e merge: Portfolio Intelligence — Incrément 1 (Release Gate, Mission 2)
├─ 3f6435d Portfolio Intelligence — Incrément 1 (Capability 7)
74a796f (état de main avant cette Release Gate)
```

`main` n'a pas été poussé vers `origin` (7 commits d'avance, non publiés — conforme à la consigne de ne rien pousser sans validation explicite).

---

## 9. Dettes et réserves restantes

- Observation Mission 6, point 2 (couleur de `why_it_matters_display`) — mineure, non bloquante, candidate pour l'Incrément 3.
- Incrément 3 (état vide honnête) et Incrément 4 (routage par défaut vers le Portefeuille) restent en Backlog, non ouverts.
- Les 8 échecs backend préexistants restent non liés à ce périmètre et non traités ici (hors mandat de cette Release Gate).
- Aucune migration Supabase n'était impliquée dans ces deux incréments — aucun risque de donnée introduit.

---

## 10. Verdict

**RELEASE GATE PASSED WITH MINOR RESERVATIONS**

Les deux incréments sont fusionnés sur `main`, dans l'ordre, avec traçabilité git séparée préservée. Toutes les validations techniques (tests ciblés, suite complète, build) et métier (16 points) sont conformes, zéro régression sur les 8 échecs préexistants. La seule réserve est l'observation visuelle mineure de la Mission 6 (couleur de `why_it_matters_display`), documentée sans justifier de rollback.
