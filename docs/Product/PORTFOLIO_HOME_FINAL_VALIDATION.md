# PORTFOLIO HOME — FINAL VALIDATION

**Date :** 2026-08-05
**Périmètre :** Release Gate du correctif "Closed-Only Clients" — vérification, fusion, revalidation produit, verdict final sur la disponibilité de Portfolio Home pour des tests utilisateurs externes.

---

## 1. Cause du défaut corrigé

`build_portfolio_briefing` sélectionnait, pour chaque client, le premier élément d'une liste déjà triée par priorité comme `top_item` — sans exclure les éléments `closed`. Un client dont tous les arcs étaient `closed` produisait donc une carte Portfolio complète avec l'action active "Préparer cette revue", alors qu'il n'y avait rien à préparer. Le compteur d'autres points actifs excluait déjà correctement les éléments `closed` ; seule la sélection du point principal (et donc la création même de la carte) en était affectée.

---

## 2. Pré-flight et périmètre (Missions 1-2)

- `main` avant fusion : `615cc50`. Branche corrective : `fix/portfolio-closed-only-clients-2026-08-05`, terminal `77edb78`, descendant linéairement de `main` (`git merge-base --is-ancestor` confirmé).
- Fichiers modifiés par la branche : `backend/services/arc_service.py`, `backend/tests/test_portfolio_briefing.py`, `docs/Architecture/blueprint/PORTFOLIO_CLOSED_ONLY_FIX_PR_REVIEW.md` — aucun fichier hors périmètre.
- Règle finale vérifiée et documentée dans le code (docstring de `build_portfolio_briefing`) et dans les tests : le Review Briefing (`build_review_briefing`) continue d'afficher les éléments `closed` comme historique, sans filtre ; Portfolio Home les exclut de son agrégation active, au même titre que les éléments `abandoned` (déjà exclus). Aucune donnée supprimée, aucun statut modifié, historique intact — confirmé par deux tests dédiés (`test_closed_arc_data_and_history_remain_intact_in_review_briefing`, `test_review_briefing_unaffected_by_portfolio_closed_filter`).
- Incrément 3 : confirmé non ouvert avant fusion (Product Board).

---

## 3. Fusion (Mission 3)

Commit de fusion : **`bc98187`** — `merge --no-ff fix/portfolio-closed-only-clients-2026-08-05` dans `main`. Aucune autre branche fusionnée. Aucun autre comportement modifié (diff limité aux 3 fichiers listés en section 2).

---

## 4. Validation technique après fusion (Mission 4)

| Vérification | Résultat |
|---|---|
| Tests Portfolio ciblés | **57/57 verts** |
| Suite backend complète | **952 passés**, 8 échecs préexistants et non liés (**identiques**), 1 skip |
| Suite frontend Jest | **30/30 verts** (aucun fichier frontend modifié) |
| Build production Next.js | Réussi, route `/app/portfolio` présente |

**8 échecs préexistants, confirmés strictement identiques à ceux de toutes les étapes précédentes de ce projet :** `test_edx_002.py::test_pptx_generates_without_edx002_shows_methodology`, `test_edx_002.py::test_pptx_has_17_slides_with_edx002`, `test_product_catalog.py::TestRobustness::test_20_validate_stripe_price_ids_returns_all_false_without_vars`, `test_product_catalog.py::TestRobustness::test_20_pack_stripe_price_id_property_without_env`, `test_rule_001_zero_manual_intervention.py::TestEDMSourceValues::test_edm_source_values`, `test_rule_001_zero_manual_intervention.py::TestPPTXContent::test_pptx_has_20_slides`, `test_rule_003_renderer_responsibility.py::TestRendererIsolation::test_pptx_produces_valid_bytes_with_empty_lists`, `test_rule_003_renderer_responsibility.py::TestRendererSelfContainment::test_pptx_handles_extreme_text_length`.

Zéro nouvelle régression.

---

## 5. Revalidation produit — 12 clients (Mission 5)

Le jeu de données fictif de `PORTFOLIO_HOME_PRODUCT_VALIDATION.md` a été rejoué à l'identique sur `main` fusionné (même script `ArcService` réel + Supabase mocké, même rendu réel de `PortfolioHome.tsx` non modifié) :

- **10 cartes** (au lieu de 11) — Traiteur Second (seul point `closed`) a disparu, comme attendu. Cabinet Rousseau (aucun arc) reste absent.
- **Ordre des 10 cartes restantes strictement inchangé** : Lefèvre, Nguyen, Girard, Vidal, Lemoine, Fontaine, Martin, Belhadj, Dupuis, Roussel.
- **Compteurs exacts et inchangés** : Lefèvre +3, Lemoine +1, Martin +2, Dupuis +1, tous les autres à 0.
- Chaque CTA "Préparer cette revue" correspond désormais, par construction, à un sujet actif réel — vérifié : 10 boutons pour 10 cartes, aucun espace vide, aucune carte incohérente.
- **Réserves UX existantes** : reconfirmées inchangées — aucun fichier frontend n'a été modifié par ce correctif. Restent classées **OBSERVE IN USER TESTING** :
  1. Densité des cartes à plusieurs informations secondaires sur une longue liste.
  2. Couleur de `why_it_matters_display` identique à celle du nom du client.

---

## 6. Verdict produit final (Mission 6)

Répondant à nouveau à la question fondamentale — un professionnel comprend-il, sans explication, quel client ouvrir, pourquoi, et quelle action effectuer :

1. **Quel client ouvrir** : oui, sans ambiguïté — l'ordre (priorité → ancienneté → nom) est prouvé correct sur un jeu de données réaliste de 12 clients, et le défaut qui aurait pu tromper cette réponse (carte closed-only avec action active) est corrigé.
2. **Pourquoi** : oui pour l'essentiel (ancienneté, compteur, `why_it_matters` filtré) ; une nuance mineure déjà connue subsiste (départage alphabétique invisible entre deux clients à stricte égalité de priorité et d'ancienneté), non bloquante.
3. **Quelle action** : oui, action unique, et désormais garantie de toujours correspondre à un sujet réellement actif.

Le seul défaut bloquant identifié par la Portfolio Home Product Validation est corrigé, testé, et revalidé sur le jeu de données réel. Les deux réserves UX restantes ont déjà été jugées non bloquantes et sont maintenues à observer, pas à corriger, conformément à la règle de ne proposer aucune nouvelle amélioration sauf blocage réel d'usage — aucune des deux ne bloque l'usage.

**Verdict : B — READY FOR EXTERNAL USER TESTING WITH MINOR RESERVATIONS**

---

## 7. Product Board (Mission 7)

`docs/Architecture/PRODUCT_BOARD.md` mis à jour sur `main` (commit `a58110e`, merge `d9857f3`) :
- Correction Closed-Only Clients : **DONE**.
- Portfolio Home Product Validation : **PASSED WITH MINOR RESERVATIONS**.
- Incrément 3 : **NOT OPENED**.
- Prochaine étape : **External User Testing**.

Aucun document Legacy modifié.

---

## 8. Tag local (Mission 8)

**`portfolio-home-mvp-validation-complete`**, tag annoté, sur `main` HEAD (`d9857f3`), suivant la convention existante du dépôt (voir `t1-evidence-foundation-complete`, `t2-engagement-foundation-complete`). Le tag précédent `portfolio-intelligence-mvp-inc-1-2-complete` (posé avant ce correctif) n'a pas été déplacé — il reste un marqueur historique exact de l'état à ce moment-là. Aucun tag poussé vers `origin`.

---

## 9. État final de main

```
d9857f3 (HEAD -> main) merge: Product Board — état post correction Closed-Only (Release Gate, Mission 7)
a58110e PRODUCT_BOARD.md — Closed-Only fix DONE, Portfolio Home Product Validation PASSED WITH MINOR RESERVATIONS
bc98187 merge: Portfolio closed-only client fix (Release Gate, Mission 3)
77edb78 fix(portfolio): exclude closed-only clients from Portfolio Home
615cc50 (état de main avant cette Release Gate)
```

`main` est 13 commits en avance sur `origin/main` — **aucun push effectué**.

Aucun Incrément 3 ouvert. Aucune donnée réelle touchée à aucune étape (mocks jetables uniquement).

---

## 10. Verdict

**PORTFOLIO HOME FINAL VALIDATION COMPLETED.**
