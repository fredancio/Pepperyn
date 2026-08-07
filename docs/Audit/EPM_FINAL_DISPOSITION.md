# EPM_FINAL_DISPOSITION.md

**Nature :** Décision finale, non révisable sans nouvelle preuve. Clôt le point "EPM (orphelin)" laissé ouvert par `TRANSFORMATION_BLUEPRINT.md` et `CURRENT_DOMAIN_MODEL.md`. Fondé sur lecture réelle du code non tracké `backend/epm/` (14 entités, `base.py`, 4 extracteurs sur 5 implémentés, 105 tests). Aucun code modifié, déplacé ou supprimé par cette mission.

**Décision architecturale :** `ExecutivePerformanceModel` en tant que modèle de domaine autonome **ne survit pas**. Disposition : **DISMANTLE & HARVEST** — la logique d'extraction déterministe est récupérable, l'objet racine et la majorité des 14 entités ne le sont pas.

---

## Mission 1 — Les 14 entités

| Entité | Responsabilité | Propriétaire canonique | Verdict |
|---|---|---|---|
| ENT-001 ExecutivePerformanceModel (racine) | Agrégat racine d'une analyse | Aucun agrégat racine unique n'est requis dans l'architecture cible | REDUNDANT |
| ENT-002 AnalysisMetadata | Contexte de production (société, période, devise, langue) | Ingestion / provenance de l'Evidence Ledger | TRANSFORM (logique de détection) |
| ENT-003 FinancialSnapshot | Photo financière (revenue, EBITDA, marges, cash, dette, runway) | Evidence Ledger / `FinancialFact` | TRANSFORM (devient read-model dérivé) |
| ENT-004 BusinessHealth | Score de santé composite 0-10 + interprétation | Aucun aujourd'hui pour le score composite ; les ratios sous-jacents → Evidence Ledger | PARTIEL — ratios TRANSFORM, score composite + interprétation OBSOLETE |
| ENT-005 FinancialKPI | Catalogue de 14 KPI extraits d'un fichier Excel Pepperyn | Evidence Ledger / `FinancialFact` | TRANSFORM |
| ENT-006 PerformanceLimiter | Facteur limitant la performance | Couche de raisonnement cognitif (`ConfidenceContract`, findings qualifiés) | REDUNDANT — aucun extracteur, concept déjà couvert |
| ENT-007 PerformanceOpportunity | Opportunité de performance | Idem ENT-006 | REDUNDANT |
| ENT-008 ExecutiveDecision | Décision actionnable, owner, deadline | `DecisionArc` / `Recommendation` (déjà plus développés) | REDUNDANT |
| ENT-009 ExecutiveRisk | Risque métier/financier | Exception & Reconciliation (concept déjà nommé, non encore implémenté) | REDUNDANT |
| ENT-010 Scenario | Trajectoire prudent/central/ambitious/downside | Aucun propriétaire canonique confirmé, mais aucun extracteur, aucune logique à perdre | OBSOLETE |
| ENT-011 RoadmapStep | Action d'exécution liée à une décision | Idem — aucun extracteur | OBSOLETE |
| ENT-012 Evidence | Preuve soutenant une entité | Evidence Ledger / `FinancialFact` (déjà plus développé) ; `SourceCell` (dans `base.py`, réellement utilisé) est plus pertinent que ce schéma jamais peuplé | REDUNDANT (le schéma) — voir Mission 5 pour `SourceCell` |
| ENT-013 DataQuality | Limites et qualité des données | `ConfidenceContract` (statuts FACT/STRONG_INFERENCE/HYPOTHESIS/UNKNOWN) couvre déjà ce rôle, avec plus de rigueur | REDUNDANT |
| ENT-014 ExecutiveSummary | Synthèse par références vers les autres entités | Couche Reporting/Deliverables future | REDUNDANT (schéma jamais peuplé) |

**10 des 14 entités n'ont jamais eu d'extracteur implémenté** (Limiter, Opportunity, Decision, Risk, Scenario, RoadmapStep, Evidence, DataQuality, ExecutiveSummary, racine) — schémas seuls, zéro logique à perdre. Seules ENT-002, ENT-003, ENT-004, ENT-005 ont une implémentation réelle (voir Mission 2).

---

## Mission 2 — Les extracteurs déterministes (le cœur de la décision)

| Fichier | Catégorie | Ce qu'il calcule/dérive | Test CFO | Destination |
|---|---|---|---|---|
| `extractors/base.py` | A + B | `SourceCell` (provenance sheet/row/column/derivation), recherche de feuille/colonne/ligne par mots-clés français/anglais insensibles aux accents, table de scoring par seuils, parsing de pourcentages | Oui, pour le matching sémantique | TRANSFORM vers ingestion — **voir gap ci-dessous** |
| `extractors/metadata_extractor.py` | A + B | Société, période, devise, langue, type de document — hiérarchie de fallback explicite, échec dur (`MetadataExtractionError`) plutôt qu'invention silencieuse. Importe déjà `services.financial_normalizer.FinancialDataPayload` (code tracké réel) | Oui | TRANSFORM vers contexte Engagement / provenance Evidence Ledger |
| `extractors/financial_snapshot_extractor.py` | A | revenue, EBITDA lus directement ; gross_margin, operating_margin calculés ; cash/dette lus si présents ; runway toujours absent (bilan requis, absent du template Pepperyn) | Oui | TRANSFORM — confirme Mission 3 |
| `extractors/financial_kpi_extractor.py` | A + B | Catalogue figé de 14 KPI (9 lecture directe + 3 calculés + 2 issus des Hypothèses), mots-clés de correspondance réglés sur le template Excel français réel de Pepperyn | Oui — la plus grande valeur de récupération | TRANSFORM — priorité de récupération |
| `extractors/business_health_extractor.py` | A (ratios) + C (bandes de seuils) + D (score composite + phrase d'interprétation figée) | ebitda_margin_pct, payroll_ratio_pct, ca_achievement_pct (A, à récupérer) ; conversion de ces ratios en score 0-10 par tables de seuils figées (C) ; moyenne pondérée + phrase d'interprétation canonique du type « Excellente santé » (D) | Ratios : oui. Score composite + phrase : **non** | Ratios → TRANSFORM. Score composite + interprétation → OBSOLETE, ne doit jamais être promu comme vérité déterministe |

**CANONICAL GAP identifié :** le matching sémantique déterministe de libellés financiers français (« chiffre d'affaires total », « EBITDA », « marge brute », « masse salariale », « trésorerie », « dette » contre les feuilles réelles du template Pepperyn) n'a pas été confirmé comme existant dans le code tracké actuel (`file_parser.py` fait de la classification structurelle et temporelle, pas ce matching sémantique de libellés). C'est la logique la plus précieuse à récupérer, et son absence ailleurs dans le dépôt tracké est un vrai vide, pas une redondance.

---

## Mission 3 — FinancialSnapshot

Confirmé par lecture du code : `FinancialSnapshot` est un **read-model dérivé**, jamais une vérité indépendante. L'entité n'est construite que si tous les champs requis sont présents dans le dict `partial` ; sinon `entity = None` et seules les valeurs partielles sont retournées. Les marges sont calculées à la volée depuis revenue/EBITDA/marge brute déjà extraits. Le principe préféré de l'architecture cible s'applique : **si reconstructible depuis des `FinancialFact` canoniques + contexte temporel, alors read-model dérivé, jamais source de vérité indépendante.** Aucune exception trouvée.

---

## Mission 4 — BusinessHealth

Distinction confirmée par le code :
- **Métriques déterministes réelles** (ebitda_margin_pct, payroll_ratio_pct, ca_achievement_pct, growth_pct si issu des Hypothèses — explicitement marqué "planifié, non vérifié" dans le code lui-même) → à récupérer comme `FinancialFact`.
- **Jugement professionnel déguisé en vérité déterministe** : les 5 tables de seuils figées (« B1.4 FROZEN, modification requires CTO sign-off ») convertissent chaque ratio en score 0-10, puis une moyenne pondérée (30/25/20/15/10 %) produit un score composite unique, accompagné d'une phrase d'interprétation canonique tirée d'une table fixe (ex. « Excellente santé : l'entreprise affiche des performances remarquables »). **Ceci ne doit jamais être promu silencieusement comme vérité déterministe.**

Ce score composite n'a nulle part où vivre aujourd'hui, et n'a probablement pas vocation à revivre sous cette forme : la doctrine Pepperyn (jugement = humain, ou raisonnement multi-agent qualifié via `ConfidenceContract`) rend obsolète l'idée d'un score de santé unique et opaque produit par une table de seuils figée. Si un besoin de synthèse de santé émerge plus tard, il doit être reconstruit dans la couche de raisonnement cognitif (Adjudicator/Executive CFO), pas ressuscité depuis ce module.

---

## Mission 5 — Evidence

`ENT-012 Evidence` (schéma Pydantic, jamais peuplé par aucun extracteur) est **redondant et obsolète** face à l'Evidence Ledger / `FinancialFact` déjà bien plus développé (ADR-001, ADR-001A).

En revanche, `SourceCell` (dans `base.py`, **réellement utilisé par les 4 extracteurs implémentés**) — `sheet_name`, `row_label`, `column_name`, `raw_value`, `derivation` (« direct » / « computed:formule » / « hypothesis » / « fallback:raison ») — est un mécanisme de provenance opérationnel, pas un schéma mort. **À vérifier avant tout portage dans T1C-A/B** : est-ce que la granularité de provenance de `FinancialFact` couvre déjà ce niveau de détail (feuille + ligne + colonne + mode de dérivation) ? Cette vérification est un point de départ concret pour T1C-A, pas un nouveau chantier d'audit.

---

## Mission 6 — Harvest des tests

105 fonctions de test recensées, réparties sur 3 fichiers à contenu réel (`test_financial_snapshot_extractor.py` : 34, `test_financial_kpi_extractor.py` : 34, `test_business_health_extractor.py` : 34 — le reste sont des fichiers stub vides).

- **À conserver comme référence** lors du portage : tests de matching de feuille/colonne/ligne (insensibilité aux accents et à la casse), tests de calcul de marges et de ratios, tests exécutés contre un fichier Pepperyn réel (`test_real_file_2025_partial_extraction`, `test_s9_real_file_*`, `test_real_file_2025_full_extraction`) — ces derniers encodent un comportement vérifié contre des données de production réelles, pas seulement une structure d'objet.
- **À ne pas porter** : tests qui protègent uniquement la forme de l'objet `BusinessHealth` composite ou la table d'interprétation figée (`test_overall_score_is_weighted_average`, `test_interpretation_is_deterministic_text`, `test_interpretation_bands_are_contiguous`, `test_entity_is_valid_businesshealth`) — ils protègent exactement la partie classée OBSOLETE.

Aucun portage mécanique de la suite complète. Le tri ci-dessus est la règle à appliquer au moment du portage réel, pas maintenant.

---

## Mission 7 — Test du Profession Model

Pour la logique d'extraction récupérable (catalogue KPI, calcul de snapshot, détection de métadonnées) : elle sert directement les facultés « Percevoir » et « Se souvenir » de l'architecture cognitive, n'est modélisée nulle part ailleurs de façon confirmée, reste appropriée en implémentation déterministe (aucun jugement, uniquement du matching et de l'arithmétique), et sa perte appauvrirait réellement Pepperyn — c'est du travail de calibrage déjà fait contre le template réel.

Pour le score composite BusinessHealth + phrase d'interprétation : sa perte ne rend Pepperyn en rien moins capable de se comporter comme un excellent CFO — au contraire, un CFO excellent ne réduit jamais la santé d'une entreprise à une moyenne pondérée figée accompagnée d'une phrase toute faite.

---

## Mission 8 — Carte de disposition cible

| Élément EPM | Rôle actuel | Disposition | Propriétaire canonique | Code conservé ? | Tests conservés ? | Phase | Raison |
|---|---|---|---|---|---|---|---|
| ENT-001 ExecutivePerformanceModel | Agrégat racine | REDUNDANT | Aucun requis | Non | Non | — | Aucun agrégat racine unique nécessaire |
| ENT-002 AnalysisMetadata + `metadata_extractor.py` | Contexte d'analyse | TRANSFORM | Ingestion / Evidence Ledger | Logique, pas le schéma | Sélectivement | T1C-A/B | Hiérarchie de fallback + échec dur = discipline utile |
| ENT-003 FinancialSnapshot + `financial_snapshot_extractor.py` | Photo financière | TRANSFORM | `FinancialFact` (read-model dérivé) | Logique, pas le schéma | Sélectivement | T1C-A/B | Confirmé read-model, jamais vérité indépendante |
| ENT-004 BusinessHealth (ratios) | Ratios EBITDA/payroll/exécution | TRANSFORM | `FinancialFact` | Logique de calcul des ratios | Sélectivement | T1C-A/B | Faits déterministes légitimes |
| ENT-004 BusinessHealth (score composite + interprétation) | Verdict de santé 0-10 + phrase | OBSOLETE | Aucun (ou futur Cognitive, à redessiner) | Non | Non | — | Jugement déguisé en fait |
| ENT-005 FinancialKPI + `financial_kpi_extractor.py` | Catalogue de 14 KPI | TRANSFORM | `FinancialFact` | Logique + catalogue de libellés | Sélectivement | T1C-A/B | Plus haute valeur de récupération |
| ENT-006 PerformanceLimiter | Facteur limitant | REDUNDANT | Raisonnement cognitif futur | Non | Non | — | Aucun extracteur, concept déjà couvert |
| ENT-007 PerformanceOpportunity | Opportunité | REDUNDANT | Idem | Non | Non | — | Idem |
| ENT-008 ExecutiveDecision | Décision actionnable | REDUNDANT | `DecisionArc`/`Recommendation` | Non | Non | — | Déjà plus développé |
| ENT-009 ExecutiveRisk | Risque | REDUNDANT | Exception & Reconciliation | Non | Non | — | Concept déjà nommé ailleurs |
| ENT-010 Scenario | Trajectoire | OBSOLETE | Aucun | Non | Non | — | Aucun extracteur, aucune logique |
| ENT-011 RoadmapStep | Action d'exécution | OBSOLETE | Aucun | Non | Non | — | Idem |
| ENT-012 Evidence (schéma) | Preuve | REDUNDANT | Evidence Ledger | Non | Non | — | Jamais peuplé, Evidence Ledger plus développé |
| `SourceCell` (dans `base.py`) | Provenance réellement utilisée | TRANSFORM *(sous réserve)* | Evidence Ledger / `FinancialFact` | Le pattern, à vérifier granularité | Non directement | T1C-A | Vérifier si `FinancialFact` couvre déjà ce niveau |
| ENT-013 DataQuality | Qualité des données | REDUNDANT | `ConfidenceContract` | Non | Non | — | Déjà plus rigoureux |
| ENT-014 ExecutiveSummary | Synthèse | REDUNDANT | Reporting futur | Non | Non | — | Jamais peuplé |
| `builder.py`, `validator.py`, `models/entities.py`, `types/pedl_types.py` | Infrastructure de l'objet EPM | OBSOLETE | — | Non | Non | — | Infrastructure d'un agrégat qui ne survit pas |
| `backend/tools/epm_viewer.py` | Outil CLI de diagnostic | OBSOLETE *(déjà classé D en mission précédente)* | — | Non (ou conservé en outil dev isolé, au choix) | Non | — | Chaîne réelle vers `file_parser`/`financial_normalizer`, mais outil, pas produit |

---

## Mission 9 — Décision finale

**A. `ExecutivePerformanceModel` peut-il être retiré ?** Oui, sans réserve, en tant que modèle de domaine autonome.

**B. Quelles capacités doivent être récupérées avant retrait ?** La logique déterministe des 4 extracteurs implémentés (catalogue KPI, calcul de snapshot, ratios de BusinessHealth hors score composite, détection de métadonnées) et le pattern `SourceCell` sous réserve de vérification de granularité contre `FinancialFact`.

**C. Une capacité récupérée nécessite-t-elle une modification de T1C-A/T1C-B ?** Possiblement mineure : si `FinancialFact` ne porte pas encore de provenance au niveau feuille/ligne/colonne/dérivation, l'ajout de ces champs (inspirés de `SourceCell`) est une extension de schéma à évaluer au moment de l'implémentation réelle de T1C-A — pas un blocage, pas une redéfinition.

**D. EPM révèle-t-il un vrai vide dans l'architecture canonique ?** Oui — le matching sémantique déterministe de libellés financiers français contre le template Excel réel de Pepperyn n'est pas confirmé exister ailleurs dans le code tracké. C'est un vide réel, pas une invention de cette mission.

**E. `backend/epm/` peut-il éventuellement être supprimé après récupération ?** Oui.

**F. T1 peut-il commencer immédiatement, ou une capacité récupérée doit-elle d'abord être incorporée dans la spécification T1 ?** T1 peut commencer immédiatement. La récupération de la logique d'extraction n'est pas un préalable bloquant — elle enrichit l'ingestion `FinancialFact` au moment de T1C-A/B, elle ne la conditionne pas.

---

**EPM FINAL DISPOSITION : RETIRE AFTER HARVEST**
**HARVEST REQUIRED BEFORE T1 : NO** *(la récupération enrichit T1C-A/B, elle ne le bloque pas)*
**T1 SPECIFICATION CHANGE REQUIRED : NO** *(modification mineure possible de provenance, pas un changement de spécification)*
**CANONICAL ARCHITECTURE GAP FOUND : YES** *(matching sémantique de libellés financiers français, non confirmé ailleurs)*
**SAFE TO BEGIN T1 : YES**
