# PORTFOLIO CLOSED-ONLY CLIENT FIX — PR REVIEW

**Date :** 2026-08-05
**Origine :** `PORTFOLIO_HOME_PRODUCT_VALIDATION.md`, verdict ONE MINIMAL CORRECTION REQUIRED (section 6).
**Branche :** `fix/portfolio-closed-only-clients-2026-08-05`, depuis `main` (commit `615cc50`).

---

## 1. Cause exacte du défaut

`build_review_briefing` exclut uniquement `status == "abandoned"` (par construction — le Review Briefing doit continuer d'afficher les points `closed`, avec leur historique). `build_portfolio_briefing` regroupait ensuite `items` (déjà trié par priorité) par `entity_id`, en prenant le **premier** item rencontré par client comme `top_item` — sans jamais vérifier que ce premier item n'était pas lui-même `closed`. Pour un client dont tous les arcs sont `closed`, cet item `closed` était donc le seul candidat, devenait `top_item`, et produisait une carte Portfolio complète avec l'action active "Préparer cette revue" — alors qu'il n'y a rien à préparer.

Le compteur (`active_counts`) excluait déjà correctement les points `closed` ; seule la sélection du `top_item` (et donc la création même de la carte) en était affectée.

---

## 2. Règle métier appliquée

Un point `closed` ne constitue jamais une raison active de préparer un client, **au niveau du Portfolio uniquement** :
- Exclu de la sélection du point principal (`top_item`).
- Exclu du compteur (déjà le cas).
- Exclu de la détermination de la priorité de la carte.
- Un client dont tous les points sont `closed` (ou `abandoned`, déjà exclu) ne produit aucune carte.

Le Review Briefing (`build_review_briefing`) est **volontairement inchangé** : un client déjà ouvert dans le chat doit pouvoir consulter l'historique de ses points clos (learning_text, date de clôture). La distinction entre les deux périmètres est documentée explicitement dans le docstring de `build_portfolio_briefing`.

---

## 3. Fichiers modifiés

| Fichier | Changement |
|---|---|
| `backend/services/arc_service.py` | `build_portfolio_briefing` : introduction de `active_items` (items hors `closed`) comme base de regroupement par client ; simplification de `other_active_count` (le `top_item` est désormais toujours actif par construction) ; docstring étendu avec la règle métier et la distinction explicite Portfolio/Review Briefing. `build_review_briefing` **non modifié**. |
| `backend/tests/test_portfolio_briefing.py` | Ajout de `TestPortfolioClosedOnlyExclusion` (9 tests, cas 1 à 9 du mandat). Mise à jour de `test_top_item_itself_never_double_counted` (Mission 4 du mandat initial), dont le scénario testait l'ancien comportement bogué (top_item lui-même `closed`) — devenu impossible par construction ; remplacé par un cas voisin toujours valide, avec commentaire explicite sur le changement. |

Aucun fichier frontend modifié — le frontend n'affichait déjà que les champs fournis par le backend ; en garantissant que `top_item.priority` n'est plus jamais `"closed"`, l'écran cesse mécaniquement de produire des cartes closes actives, sans changement de code côté `PortfolioHome.tsx`.

---

## 4. Comportement du Portfolio après correction

- Client avec uniquement des arcs `closed` (ou `abandoned`) : **aucune carte**.
- Client avec un mélange d'arcs ouverts et clos : carte fondée **uniquement** sur les arcs ouverts (point principal, compteur, priorité).
- Client avec uniquement des arcs ouverts : comportement inchangé.
- Action "Préparer cette revue" : présente uniquement lorsqu'un sujet actif existe, par construction (plus de carte du tout sinon).

---

## 5. Maintien de l'historique

Aucune donnée supprimée, aucun statut transformé, aucune ligne modifiée en base. Le correctif est une exclusion en mémoire, au moment de l'agrégation Portfolio uniquement — les arcs `closed` restent intacts et intégralement consultables via le Review Briefing (`test_closed_arc_data_and_history_remain_intact_in_review_briefing`, `test_review_briefing_unaffected_by_portfolio_closed_filter`).

---

## 6. Résultats des tests

| Vérification | Résultat |
|---|---|
| Tests Portfolio ciblés (`test_portfolio_briefing.py` + `test_review_briefing.py`) | **57/57 verts** (48 préexistants + 9 nouveaux) |
| Suite backend complète | **952 passés**, 8 échecs préexistants et non liés (identiques avant/après), 1 skip |
| Suite frontend Jest | **30/30 verts** (inchangé, aucun fichier frontend modifié) |
| Build production Next.js | Réussi, route `/app/portfolio` présente (3.22 kB) |

**8 échecs préexistants, confirmés strictement identiques :** `test_edx_002.py::test_pptx_generates_without_edx002_shows_methodology`, `test_edx_002.py::test_pptx_has_17_slides_with_edx002`, `test_product_catalog.py::TestRobustness::test_20_validate_stripe_price_ids_returns_all_false_without_vars`, `test_product_catalog.py::TestRobustness::test_20_pack_stripe_price_id_property_without_env`, `test_rule_001_zero_manual_intervention.py::TestEDMSourceValues::test_edm_source_values`, `test_rule_001_zero_manual_intervention.py::TestPPTXContent::test_pptx_has_20_slides`, `test_rule_003_renderer_responsibility.py::TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`, `test_rule_003_renderer_responsibility.py::TestRendererSelfContainment::test_pptx_handles_extreme_text_length`.

---

## 7. Revalidation avec les 12 clients de `PORTFOLIO_HOME_PRODUCT_VALIDATION.md`

Le même jeu de données (script Python jetable, `ArcService` réel + Supabase mocké, puis rendu réel de `PortfolioHome.tsx` non modifié) a été rejoué après correction :

- **10 cartes** au lieu de 11 — Traiteur Second (seul point `closed`) a disparu, comme attendu.
- Cabinet Rousseau (aucun arc) reste absent, comme avant.
- **Ordre des 10 cartes restantes strictement inchangé** (mêmes clients, même séquence de priorité/ancienneté/nom).
- **Compteurs inchangés** sur toutes les cartes restantes (Lefèvre +3, Lemoine +1, Martin +2, Dupuis +1).
- Aucun espace vide, aucune carte incohérente.
- Rendu réel confirmé : 10 boutons "Préparer cette revue" pour 10 cartes — l'action n'est jamais présente sans sujet actif.

---

## 8. Verdict

**APPROVED**

Correctif unique, minimal, localisé à `build_portfolio_briefing`. Cause exacte identifiée et corrigée. Périmètre du Review Briefing explicitement préservé et re-testé. 9 tests dédiés ajoutés, 1 test obsolète mis à jour avec justification. Zéro régression sur les 8 échecs préexistants ni sur les suites existantes. Revalidation sur le jeu de données réel de la Product Validation conforme en tout point (disparition du client closed-only, ordre et compteurs des autres cartes inchangés). Aucun enrichissement visuel, aucune correction des deux réserves UX (toujours OBSERVE IN USER TESTING), aucun Incrément 3 ouvert.
