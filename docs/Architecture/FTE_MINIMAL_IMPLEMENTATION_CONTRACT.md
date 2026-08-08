# FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md

**Nature :** contrat d'implémentation, pas une doctrine. Dérivé de la responsabilité professionnelle du CFO, pas du code existant. Réutilise et resserre `ADR-003_Financial_Time_Engine_v3_PROPOSED.md` (conçu, auto-critiqué 9/10, jamais ACCEPTED) — ne le remplace pas, en extrait le sous-ensemble strictement justifié par le déclencheur de réouverture déjà enregistré (`STRATEGIC_DEFERRED_WORK_REGISTER.md` §1.4 : *"cas vertical Phidani, limité à `PeriodObservation`/`FiscalPeriod` — pas `BusinessHistory`, pas `FutureBusinessMoment`"*). Mode : lecture seule, aucune implémentation.

---

## 1. Responsabilité professionnelle

Un excellent CFO ne lit jamais un chiffre isolément : avant tout jugement, il doit savoir sans ambiguïté **de quelle période parle une donnée**, **si cette période est close ou encore ouverte**, **quelle période la précède**, et **si Pepperyn possède déjà une connaissance de cette période précédente** — sans jamais fabriquer une certitude que la donnée ne supporte pas. C'est la version irréductible de "Contextualiser" (Chapitre 2, responsabilité #2 du `PEPPERYN_PROFESSION_MODEL.md`), et c'est exactement ce que le Golden Case Phidani exige (§19 ci-dessous).

## 2. Invariant minimal

Un jeu de données financières peut être classé en une identité de période (courante / historique / budget-prévisionnel) **de façon déterministe à partir de son propre contenu**, et cette classification est **comparable** — jamais fusionnée — à la dernière période connue pour le même Engagement, sans jamais inventer une période que la donnée ne supporte pas, et sans jamais confondre *quand le fait s'est produit* avec *quand Pepperyn l'a appris*.

## 3. Concepts temporels requis maintenant

- **PeriodObservation minimale** — pas la VO riche d'ADR-003 v3 (`raw_label`, `parsed_start/end`, `source_row_ref`) : un couple `(année, mois)` déterministe, dérivé de ce que `temporal_normalizer.py` calcule déjà.
- **Relation de comparaison** (période précédente, écart, doublon, hors-ordre) — arithmétique pure sur ces couples.
- **Confiance de clôture qualifiée** ("probablement close", jamais "close" comme fait) — exigé littéralement par le Golden Case Phidani (`STRONG_INFERENCE`, jamais `FACT`).
- **Horizons de comparaison** (YTD, rolling-12 conditionnel) — dérivés, jamais persistés.

## 4. Concepts temporels explicitement différés

`FiscalPeriod` riche (type/start/end/label), `FiscalCalendar` (années fiscales non-calendaires), `PeriodFrequency`/`RhythmDrift` (rythme observé), `BusinessHistory`, `FutureBusinessMoment` — exclus par le déclencheur de réouverture lui-même. **`Business Moment`** : jamais défini nulle part dans le corpus canonique (confirmé par recherche exhaustive sur 10 documents cognitifs) — utilisé uniquement comme étiquette illustrative ("nouvelle période disponible"), sans schéma. Inventer sa sémantique maintenant serait la construire, pas la dériver — **différé explicitement**, pas oublié.

## 5. Relation à Evidence

Le FTE ne devient pas un second Evidence Ledger. `evidence_ledger_entries` n'a aujourd'hui qu'un timestamp d'insertion (`created_at`), aucun champ de période. Le FTE lit uniquement la sortie déjà déterministe de `temporal_normalizer.build_temporal_context()` — calculée aujourd'hui à l'ingestion (`file_parser.py:294`) puis **perdue**, jamais persistée. Le premier incrément capture cette sortie une fois, de façon strictement additive (aucune réécriture d'une ligne existante — compatible avec le trigger d'immutabilité inconditionnel sur `UPDATE`).

**Contradiction nommée, non réparée :** `QuantifiedImpact.temporal_role` (`models/financial_truth.py:210`) porte un commentaire *"De temporal_normalizer"*, mais rien dans le code ne relie ce champ à `temporal_normalizer` — sa valeur ne provient que de ce que le LLM choisit d'émettre dans le JSON `quantified_impact`, donc non déterministe. Ce champ **ne doit pas** servir d'entrée au noyau déterministe du FTE malgré son nom trompeur. Signalé, pas corrigé.

## 6. Relation à Engagement

Engagement scope le FTE (`entity_id` aujourd'hui, `1:1` transitoire). Le FTE ne lit `Engagement.cadence` (déclarée) qu'en entrée optionnelle — il n'écrit jamais dedans, et ne fabrique aucune "cadence observée" dans ce premier incrément (ce serait `PeriodFrequency`, différé). Compatible sans changement avec un futur `1:N` (§1.2.a) car le FTE interroge toujours "la dernière période connue pour cet Engagement", jamais "l'unique Engagement de cette Entity".

## 7. Relation à DecisionArc

Aucune des six dates de `DecisionArc` (`created_at`, `updated_at`, `decision_confirmed_at`, `execution_updated_at`, `closed_at`, `abandoned_at`) n'est touchée. Toutes sont déjà, par construction et par discipline documentée dans le code lui-même (`arc_service.py:16` — *"decision_confirmed_at ≠ date réelle de décision"*), du temps de connaissance ou du temps système — jamais du temps métier. Le FTE ne devient pas propriétaire du cycle de vie décisionnel ; une consommation future de `BriefingItem.temporal_context` par le vocabulaire du FTE est possible mais explicitement hors de ce premier incrément.

## 8. `temporal_normalizer.py` — verdict

**EVOLVE, pas KEEP, pas HARVEST, pas RETIRE.** Vérifié à nouveau, ligne par ligne, contre le code réel de `main` (pas contre la conclusion de l'audit précédent, qui reste globalement correcte mais légèrement optimiste). Le module opère une vraie inférence déterministe (batch "année courante" via `_determine_current_year`, règle YTD-prioritaire-sur-fréquence), sans LLM, sans calendrier fiscal codé en dur. Nuance non documentée jusqu'ici : sa classification est **strictement locale au fichier** — un fichier périmé uploadé tardivement déclarerait sa dernière colonne `CURRENT_ACTUAL` même si, à l'échelle de l'Engagement, cette période est déjà historique. Le FTE doit donc traiter sa sortie comme un **signal d'entrée**, pas comme la vérité finale de période — la vérité de période comparée dans le temps reste arbitrée par le FTE via l'historique de l'Engagement. Son propre code n'est pas modifié par ce contrat ; seule sa consommation (aujourd'hui : aucune persistance) doit évoluer.

## 9. Temps métier / Temps de connaissance / Temps de décision

Cette distinction n'est nommée nulle part dans le corpus canonique existant ("three clocks" absent, confirmé), mais **la discipline sous-jacente existe déjà** dans le code (`decision_confirmed_at` ≠ date réelle). Elle est donc validée par la pratique, seulement jamais nommée. Pour le FTE :
- **Temps métier** — la période calendaire que décrit la donnée (ex. "septembre 2019"). C'est le seul temps que le FTE produit réellement.
- **Temps de connaissance** — quand Pepperyn a ingéré/classé la donnée. Déjà entièrement couvert par `created_at` existant ; le FTE ne crée aucun nouveau champ pour cela, il refuse seulement de le confondre avec le temps métier.
- **Temps de décision** — appartient entièrement à `DecisionArc` (§7). Le FTE ne le modélise pas.

## 10. Contrat de données minimal

| Champ | Type | Sens | Source | Déterministe | Nullable | Pourquoi maintenant | Consommateur actuel |
|---|---|---|---|---|---|---|---|
| `observed_period_year` | `INT` | Année de la colonne la plus récente classée par `temporal_normalizer` | `build_temporal_context()["detected_current_year"]`, déjà calculé, aujourd'hui perdu | Oui | Oui (Article III — absence ≠ zéro) | Sans lui, aucune "période précédente" n'est reconstituable pour l'analyse suivante — les fichiers bruts ne sont pas conservés | `resolve_previous_observed_period()` (nouveau, ce contrat) |
| `observed_period_month` | `INT` | Mois de cette même colonne, quand résoluble | Idem, extraction mois déjà faite par `_extract_month` | Oui | Oui (résolution mois pas toujours possible) | Requis par le Golden Case Phidani (granularité mensuelle) | Idem |

Aucun autre champ. Pas de VO riche, pas de table dédiée.

## 11. Décision de persistance

**HYBRIDE, minimal.** Le FTE reste sans état par conception pour tout calcul (comparaison, confiance de clôture, horizons) — cela reste dérivé à la demande. Mais la classification de `temporal_normalizer` elle-même doit être capturée une fois, car les fichiers source ne sont pas conservés : sans persistance ponctuelle, l'information est perdue de façon irréversible après chaque analyse. Ce n'est pas une seconde vérité (One New Truth Rule respectée) : rien ne persiste aujourd'hui cette donnée nulle part — ces deux colonnes en deviennent la seule source, pas une source concurrente.

## 12. Migration base de données

**OUI, minimale.** `ALTER TABLE evidence_ledger_entries ADD COLUMN observed_period_year INT NULL, ADD COLUMN observed_period_month INT NULL;` — nouvelle migration additive (jamais une réécriture de `v18`), compatible avec le trigger d'immutabilité (bloque `UPDATE`, pas `INSERT`). Aucune nouvelle table, aucun nouveau trigger.

## 13. Premier consommateur réel

Aucun consommateur produit/UI dans ce premier incrément. Le Golden Case Phidani **est** le premier consommateur — un test de bout en bout, pas encore une fonctionnalité livrée. Cohérent avec la nature même du "walking skeleton".

## 14. Exigence minimale Phidani

Exactement les "Must Detect" de `GOLDEN_CASE_001_PHIDANI.md` : identifier septembre comme courant, août comme précédent, qualifier septembre "probablement close" (jamais un fait), fournir un YTD janvier-septembre, fournir un rolling-12 **seulement si l'historique le permet** (sinon retourner honnêtement "historique insuffisant", jamais fabriquer). Aucune généralisation de calendrier fiscal, aucune saisonnalité, aucune récurrence.

## 15. Semantique des échecs

Ambiguïté, absence, chevauchement, doublon, hors-ordre : chaque cas retourne un état explicite (`gap`, `duplicate`, `out_of_order`, `unknown`) — jamais résolu silencieusement en faveur d'une hypothèse implicite (Article III de la Constitution : *"une donnée absente reste absente ; elle ne devient jamais un zéro, une hypothèse implicite, ou une valeur par défaut présentée comme observée"*).

## 16. Contrat négatif

Le FTE minimal ne sait PAS : si une dégradation est "mauvaise", si une saisonnalité explique un écart, si une tendance est stratégiquement importante, si une recommandation doit être émise, si un moment est "une crise". Ces jugements restent hors du noyau déterministe, par construction — confirmé cohérent avec `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` (*"Période : déterministe, produite par le FTE, sans LLM"*).

## 17. Impact code attendu (planification, aucune exécution)

| Fichier | Changement attendu | Pourquoi | Risque | Statut |
|---|---|---|---|---|
| `backend/migrations/v23_evidence_ledger_observed_period.sql` | Nouveau, 2 colonnes nullable | Capturer un signal déjà calculé, aujourd'hui perdu | Faible, additif | NEW |
| `backend/services/evidence_ledger_service.py` | `save_evidence_capture()` reçoit et écrit les 2 champs | Point d'écriture unique | **Non trivial** — voir bloqueur §19 | MODIFY |
| `backend/services/llm_service.py` / `routers/analyze.py` | Faire circuler `temporal_context` (ou son résumé) jusqu'à `save_evidence_capture()` | Aujourd'hui non transmis à cet appel (vérifié : `analyze.py:763` ne reçoit que `analyse_id/company_id/entity_id/evidence_capture`) | Moyen — plomberie sur 2-3 fichiers | MODIFY (portée exacte à vérifier avant code) |
| `backend/services/fte_minimal.py` (nom illustratif) | Nouveau module, fonctions pures | Isoler le noyau déterministe du reste | Faible, module isolé | NEW |
| `backend/services/temporal_normalizer.py` | Aucun | Déjà correct, déjà déterministe | — | DO NOT TOUCH |
| `backend/models/decision_arc.py`, `backend/services/arc_service.py` | Aucun | Le temps de décision reste à DecisionArc | — | DO NOT TOUCH |
| `backend/migrations/v18_evidence_ledger.sql` | Aucun | Convention du dépôt : migrations additives uniquement | — | DO NOT TOUCH |
| `backend/models/financial_truth.py` (`temporal_role`) | Aucun | Contradiction nommée (§5), pas réparée ici | — | DO NOT TOUCH |

## 18. Tests requis (spécifiés, non écrits)

Même entrée → même classification (déterminisme) ; absence de signal → `NULL`, jamais l'année/mois système par défaut ; mois manquant entre deux analyses → `gap`, jamais ignoré ; deux analyses pour le même mois → `duplicate`, aucune ligne écrasée ; upload hors-ordre → détecté explicitement ; confiance de clôture jamais un booléen brut, toujours un état qualifié ; replay Phidani conforme aux "Must Detect" ; les six dates de `DecisionArc` prouvées non touchées (test greppé, dans le style déjà établi) ; le trigger d'immutabilité d'Evidence Ledger rejette toujours `UPDATE` après la migration ; aucun appel LLM nulle part dans `fte_minimal.py` (test greppé).

## 19. Premier incrément — IN / OUT

**IN :** 2 colonnes additives ; un module de service pur (comparaison de périodes, confiance de clôture qualifiée, YTD/rolling-12 conditionnel) ; le câblage minimal nécessaire pour que Phidani passe de bout en bout ; les tests du §18.

**OUT :** `PeriodObservation`/`FiscalPeriod` riches, `Business Moment`, `BusinessHistory`, `FutureBusinessMoment`, `FiscalCalendar`, toute API/UI, toute correction du champ `temporal_role`, toute modification de `temporal_normalizer.py` ou de `DecisionArc`, tendance/saisonnalité/prévision/anomalie, minutage de recommandation, Attention Score, prompts d'agents, benchmarks inter-entreprises.

**Bloqueurs ouverts (vérification code requise avant tout code, pas une hypothèse à coder dessus) :**
1. `temporal_context` n'est aujourd'hui **pas** transmis jusqu'à `save_evidence_capture()` (vérifié par lecture directe de `routers/analyze.py:763`) — la plomberie réelle est plus large qu'un simple ajout de paramètre ; sa portée exacte doit être tracée avant d'estimer l'incrément.
2. Le scoping par `entity_id` (au lieu de `engagement_id`) reste sûr aujourd'hui (monde `1:1`) mais devra être revu le jour où `1:N` (§1.2.a) devient réel — caveat nommé, pas un bloqueur actuel.
3. La fenêtre de tolérance exacte pour "probablement close" (Phidani : 2 octobre vs. septembre clos ≈ 1-2 jours) n'est spécifiée nulle part canoniquement — à décider explicitement avec Fred, pas à inventer silencieusement à l'implémentation.

## 20. Recommandation

**GO AVEC RÉSERVES** — le concept est correctement minimal et dérivé de la doctrine existante (pas une invention), mais les bloqueurs du §19 doivent être levés par une trace de code réelle avant d'estimer ou de commencer l'implémentation.
