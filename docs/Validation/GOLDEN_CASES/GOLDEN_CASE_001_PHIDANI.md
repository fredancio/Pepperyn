# GOLDEN_CASE_001_PHIDANI.md

**Nature :** Phase 9. Complète le walking skeleton (`PHIDANI_WALKING_SKELETON.md`) avec les deux champs identifiés comme manquants dans `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` §31.6 (Forbidden Claims, Must Remain Unknown). **Aucun replay lancé dans cette mission.**

**Correction narrow (promotion FTE v0) :** `FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md` établit que la sémantique de clôture ("probablement clos") n'est pas un fait accessible au noyau déterministe du FTE v0 — aucune combinaison de données présentes + arithmétique calendaire ne permet de savoir si une organisation a réellement clos sa période. Les deux lignes concernées ci-dessous (Must Detect, Forbidden Claims) sont corrigées en conséquence pour tester les invariants temporels réellement acceptés, sans modifier le reste du cas. Intention historique préservée : le dataset, les périodes, le contexte organisationnel et les autres exigences (Must Remain Unknown, Stability Expectations) sont inchangés.

---

## Inputs

- **Dataset :** ancienne version du fichier Phidani (janvier-août 2019) et nouvelle version (janvier-septembre 2019).
- **Date système simulée :** 2 octobre 2019.
- **Engagement :** Phidani, déjà créé (organisation existante, pas un onboarding).
- **Historique connu :** historique financier disponible pour les périodes janvier-août 2019.
- **Période précédente :** août 2019.
- **Nouvelle période :** septembre 2019.

## Must Detect

*(Faits obligatoires — un échec ici est un défaut bloquant, jamais une nuance acceptable.)*
- Une nouvelle période (septembre) est apparue par rapport à la version précédente du fichier — une information financière plus récente que la dernière connue (août) est disponible.
- Septembre suit août sans écart de continuité, **uniquement si l'information déterministe disponible le permet** (comparaison de bornes de dates, sans hypothèse de cadence mensuelle implicite) — *(corrigé : remplace l'ancienne exigence de clôture probable, retirée du périmètre FTE v0, voir note de correction ci-dessus)*.
- Août reste la période précédente de référence (dernière borne de temps métier connue).
- Un cumul YTD janvier-septembre devient disponible.
- Un rolling 12 mois devient calculable si l'historique disponible le permet (à vérifier contre le dataset réel — condition, pas garantie) ; sinon, un résultat explicite "historique insuffisant", jamais une valeur fabriquée.
- Toute colonne d'en-tête ambiguë doit être classée par `temporal_normalizer.py` avec un `PeriodRole` cohérent (`CURRENT_ACTUAL` pour septembre, `HISTORICAL_ACTUAL` pour janvier-août).
- **Clôture : aucune assertion, sous aucune forme** — ni certaine ni qualifiée. **Pertinence d'analyse : aucun jugement professionnel** — le FTE v0 constate qu'une information plus récente existe, il ne décide jamais qu'une nouvelle analyse doit être lancée (cette décision appartient à une future capacité `AnalysisPertinence`, hors périmètre).

## Expected but not exact

*(Conclusions raisonnablement attendues — leur formulation peut varier, leur substance doit converger.)*
- Une analyse notant que septembre devient une période temporellement pertinente pour une nouvelle revue.
- Une identification des recommandations passées (si elles existent dans l'historique Phidani) qui deviennent évaluables avec l'arrivée d'un mois supplémentaire de données réelles.
- Une éventuelle observation de tendance sur la période YTD, sans obligation de conclusion chiffrée précise.

## Forbidden Claims

*(Nouveau — obligatoire, absent de la première version du walking skeleton.)*
- Aucune affirmation sur des données postérieures à septembre 2019 (le dataset s'arrête là — toute mention d'octobre ou plus tard comme un fait est une invention).
- **Aucune affirmation de clôture de septembre, ni certaine ni qualifiée** *(corrigé : la clôture est désormais explicitement hors du périmètre du noyau déterministe FTE v0 — voir note de correction en tête de document — plutôt qu'une inférence `STRONG_INFERENCE` autorisée)*. Toute affirmation de clôture, même qualifiée, constitue désormais elle-même une violation de ce Golden Case pour le périmètre FTE v0. La clôture reviendra via une déclaration explicite d'une source, une configuration organisationnelle, ou un comportement de clôture observé (`BusinessHistory`) — jamais avant, jamais par convention de tolérance calendaire.
- Aucune causalité affirmée entre une variation de résultat et un événement externe non présent dans le dataset ou dans le Knowledge Model de l'Engagement Phidani.
- Aucun chiffre de comparaison rolling 12 si l'historique disponible est en réalité insuffisant pour le calculer — le système ne doit jamais compléter silencieusement les mois manquants.
- Aucune recommandation qui ne cite pas explicitement un `FinancialFact` traçable du dataset fourni.

## Must Remain Unknown

*(Nouveau — obligatoire.)*
- La cause précise d'une éventuelle variation significative entre août et septembre, si aucune explication n'est présente dans le dataset ni confirmée par l'Engagement — doit rester `UNKNOWN`, jamais résolue par supposition.
- Toute donnée future (octobre 2019 et au-delà) — doit rester absente, pas seulement non affirmée.
- La cause d'un éventuel écart entre les deux versions du fichier autre que l'ajout de la période septembre elle-même (ex. une révision rétroactive d'un chiffre d'août) — si un tel écart existe dans le dataset réel, il doit être signalé comme une exception à investiguer (Faculté 5, Questionner), jamais silencieusement absorbé dans la nouvelle version comme si de rien n'était.

## Stability Expectations

*(Reprend la structure à 6 facettes de `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` §31.5, appliquée concrètement à ce cas.)*

| Facette | Attendu sur ce cas |
|---|---|
| Factual stability | Identique à 100 % — le fait « septembre est une nouvelle période, août est la précédente » ne doit jamais varier entre deux exécutions sur le même dataset. |
| Diagnostic stability | Stable en substance — la reconnaissance que septembre devient pertinent doit apparaître à chaque exécution, indépendamment de la formulation. |
| Causal interpretation stability | Librement variable, **à condition qu'aucune exécution n'invente une cause absente du dataset** (voir Forbidden Claims). |
| Priority stability | Stable si l'Attention Engine (hors périmètre de ce Golden Case, walking skeleton ne l'inclut pas) est un jour branché — non testable sur ce cas seul. |
| Recommendation stability | Stable en substance (« une revue de septembre est pertinente maintenant ») — variable dans le détail des alternatives proposées. |
| Uncertainty stability | Forte — toute entrée de la liste « Must Remain Unknown » ci-dessus doit rester `UNKNOWN` sur les dix exécutions du protocole de replay, sans exception. |

---

## Statut de complétude

Ce document remplit désormais les huit champs minimaux requis par le protocole Golden Case (`REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` §31.6) : dataset, contexte temporel, contexte organisationnel, vérités factuelles attendues, anomalies obligatoirement détectables, conclusions raisonnablement attendues, affirmations interdites, inconnues devant rester inconnues. **Phidani #001 est maintenant un Golden Case complet, pas seulement un candidat** — sous réserve que le dataset réel (fichier Excel Phidani lui-même) soit effectivement disponible et cohérent avec les hypothèses ci-dessus au moment du premier replay, ce qui n'a pas été vérifié dans cette mission (aucun replay lancé, conformément à la consigne).

---

**GOLDEN_CASE_001_PHIDANI ÉTABLI. AUCUN REPLAY LANCÉ.**
