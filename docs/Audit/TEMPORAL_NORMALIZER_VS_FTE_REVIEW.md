# TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md

**Nature :** Phase 8. Audit du code réel de `backend/services/temporal_normalizer.py` (337 lignes, lu intégralement cette session). Aucun code modifié.

**Conclusion en tête, puis démonstration :** **le risque de double vérité temporelle, signalé comme non résolu dans le Cognitive Architecture Review et le Strategic Deferred Work Register, ne se matérialise pas une fois le fichier lu.** Ce n'est pas un doublon du FTE — c'est un composant qui opère à une couche entièrement différente. Le blocage nommé pour l'implémentation du FTE (« aucun FTE tant que ce risque n'est pas tranché ») est levé par ce document.

---

## Ce que le fichier fait réellement

`temporal_normalizer.py` classifie les **en-têtes de colonnes d'un fichier Excel unique** en rôles de période (`CURRENT_ACTUAL`, `HISTORICAL_ACTUAL`, `PRIOR_YEAR`, `BUDGET`, `FORECAST`, `YTD`, `UNKNOWN`), par une hiérarchie de signaux textuels (libellé explicite « CURRENT »/« N » > année la plus récente parmi les colonnes YTD > année maximale parmi les colonnes non-budget/non-forecast > fréquence en dernier recours). **100 % déterministe, aucun LLM, fonction pure** (`classify_columns(headers) -> list[TemporalColumn]`), sans état, sans persistance.

**Consommateurs réels, vérifiés :**
- `file_parser.py:294` — appelle `build_temporal_context(temporal_headers)`, injecte le résultat dans `result["temporal_context"]`, transmis ensuite au prompt LLM (« Tells the LLM which columns are current vs historical vs budget »).
- `financial_truth.py:210` — champ `temporal_role`, sourcé explicitement « De temporal_normalizer ».

**Ce n'est donc ni du code mort ni un doublon caché — c'est un composant actif, correctement câblé, à la couche de perception (Percevoir, Faculté 1 de la Cognitive Architecture).**

---

## Comparaison avec la doctrine FTE (ADR-003 v3)

| | `temporal_normalizer.py` | Financial Time Engine (ADR-003 v3) |
|---|---|---|
| **Périmètre** | Un fichier Excel unique, ses en-têtes de colonnes | L'organisation entière, à travers le temps et les analyses successives |
| **Question posée** | « Cette colonne représente quelle sorte de période ? » | « Ce moment est-il pertinent pour cette organisation, compte tenu de son historique et de son Engagement ? » |
| **Entrée** | Texte brut d'en-tête (« 9M YTD », « Budget 2019 ») | `PeriodObservation`, Engagement, historique |
| **Sortie** | `PeriodRole` par colonne (VO local, jetable) | `BusinessMoment`, `FinancialTemporalContext`, `DataFreshness`, `ComparisonHorizons` |
| **État** | Sans état, fonction pure | Sans état par conception (déjà spécifié identique dans ADR-003 v3) |
| **Connaissance de l'organisation** | Aucune — ignore tout d'Engagement, d'historique, de comportement | Centrale — consomme l'Engagement et l'historique |
| **Déterminisme** | Oui, regex/heuristique | Oui, déjà spécifié ainsi |

**Le chevauchement réel est nul, pas partiel** : les deux composants sont déterministes et sans état — c'est leur seul point commun — mais ils répondent à deux questions disjointes, à deux échelles disjointes (un fichier vs une organisation dans le temps). Un `PeriodRole` (« cette colonne est `CURRENT_ACTUAL` ») n'est pas une donnée concurrente d'un `BusinessMoment` (« septembre 2019 vient probablement de se clôturer ») — c'est un signal d'entrée plausible pour le construire.

---

## Décision par responsabilité

| Responsabilité | Verdict | Justification |
|---|---|---|
| Classification d'en-têtes de colonnes Excel en rôle de période | **KEEP** | Correcte, déterministe, déjà consommée réellement — aucune raison de la reconstruire. |
| Détection de l'année « courante » d'un fichier par hiérarchie de signaux | **KEEP** | Logique déjà robuste (gère explicitement le cas piège 12 mois N-1 + 6 mois YTD N cité dans le docstring). |
| Fourniture d'un signal d'entrée pour `PeriodObservation` (FTE) | **ABSORB INTO FTE — comme fournisseur, pas comme composant fusionné** | Le FTE, une fois implémenté, doit consommer la sortie de `temporal_normalizer.py` comme un des signaux construisant `PeriodObservation`, plutôt que de réinventer sa propre classification de colonnes. Ce n'est pas une fusion de code — c'est un branchement explicite à ajouter au moment de l'implémentation FTE. |
| Compréhension de la pertinence temporelle organisationnelle (BusinessMoment, horizons de comparaison) | **N/A — hors périmètre de ce fichier, propriété exclusive du FTE** | `temporal_normalizer.py` ne prétend à aucun moment résoudre cette question — aucune confusion possible dans le code lui-même. |
| Champ `temporal_role` dans `financial_truth.py` | **Dette héritée, pas un problème de doublon** | Ce champ alimente un module par ailleurs confirmé dormant (jamais lu par les renderers, `LEGACY_CAPABILITY_REVIEW_MATRIX.md`) — sa valeur réelle aujourd'hui est nulle, indépendamment de la question FTE. |

**Aucune responsabilité n'est classée REPLACE ou RETIRE.**

---

## Conclusion obligatoire

**Le risque de double vérité temporelle est levé.** `temporal_normalizer.py` n'est pas une seconde doctrine temporelle concurrente du FTE — c'est un utilitaire de perception, correctement borné, qui devient un fournisseur naturel du FTE une fois celui-ci implémenté. **Gate E (`PRE_IMPLEMENTATION_GATE_CHECKLIST.md`) peut être considéré comme passé** sur la base de ce document — la seule action requise au moment de l'implémentation FTE est un branchement explicite (`PeriodObservation` doit citer `temporal_normalizer.py` comme une de ses sources), pas un arbitrage de conflit.

---

**TEMPORAL_NORMALIZER_VS_FTE_REVIEW ÉTABLI À PARTIR DU CODE RÉEL. AUCUN CODE MODIFIÉ. RISQUE DE DOUBLE VÉRITÉ TEMPORELLE TRANCHÉ : ABSENT.**
