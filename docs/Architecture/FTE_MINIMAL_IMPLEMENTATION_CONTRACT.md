# FTE_MINIMAL_IMPLEMENTATION_CONTRACT.md

**Nature :** contrat d'implémentation, pas une doctrine. Dérivé de la responsabilité professionnelle du CFO, pas du code existant. Réutilise et resserre `ADR-003_Financial_Time_Engine_v3_PROPOSED.md` (conçu, auto-critiqué 9/10, jamais ACCEPTED) — ne le remplace pas, en extrait le sous-ensemble strictement justifié par le déclencheur de réouverture déjà enregistré (`STRATEGIC_DEFERRED_WORK_REGISTER.md` §1.4 : *"cas vertical Phidani, limité à `PeriodObservation`/`FiscalPeriod` — pas `BusinessHistory`, pas `FutureBusinessMoment`"*). Mode : lecture seule, aucune implémentation.

**Révision (arbitrage final, même jour) :** ce contrat a été resserré une seconde fois après arbitrage explicite sur 6 questions (représentation canonique de période, clôture, exigences Phidani irréductibles, statut de `PeriodObservation`, persistance minimale, isolation de `temporal_role`). Le résultat est strictement plus petit que la première version, jamais plus riche — cohérent avec l'intuition de Fred (*"le FTE va encore rétrécir"*). Les sections modifiées par cet arbitrage sont marquées **[RÉVISÉ]**.

---

## 1. Responsabilité professionnelle

Un excellent CFO ne lit jamais un chiffre isolément : avant tout jugement, il doit savoir sans ambiguïté **de quelle période parle une donnée**, **si cette période est close ou encore ouverte**, **quelle période la précède**, et **si Pepperyn possède déjà une connaissance de cette période précédente** — sans jamais fabriquer une certitude que la donnée ne supporte pas. C'est la version irréductible de "Contextualiser" (Chapitre 2, responsabilité #2 du `PEPPERYN_PROFESSION_MODEL.md`), et c'est exactement ce que le Golden Case Phidani exige (§19 ci-dessous).

## 2. Invariant minimal

Un jeu de données financières peut être classé en une identité de période (courante / historique / budget-prévisionnel) **de façon déterministe à partir de son propre contenu**, et cette classification est **comparable** — jamais fusionnée — à la dernière période connue pour le même Engagement, sans jamais inventer une période que la donnée ne supporte pas, et sans jamais confondre *quand le fait s'est produit* avec *quand Pepperyn l'a appris*.

## 3. Concepts temporels requis maintenant **[RÉVISÉ]**

- **Représentation canonique de période** — `period_start: DATE` + `period_end: DATE`. Pas `(année, mois)` : ce couple encoderait le mois comme une hypothèse de domaine, forçant une réinterprétation destructrice ou des champs parallèles le jour où un reporting trimestriel, hebdomadaire, annuel ou à calendrier fiscal non standard apparaît. Deux dates couvrent tous ces cas sans hypothèse de granularité, pour le même coût (2 champs). Distinction explicite requise : un montant de bilan décrit une **position à une date** (le point pertinent est `period_end`) ; un montant de compte de résultat décrit une **activité sur un intervalle** (`[period_start, period_end]`). La représentation ne force pas ce choix — elle porte les deux bornes, l'interprétation (point vs intervalle) reste une propriété du fait/métrique lui-même (déjà un axe distinct dans le Financial Truth Layer — "nature", "base temporelle"), jamais de l'identité de période.
- **Relation de comparaison** (nouvelle période, écart, doublon, hors-ordre) — arithmétique pure sur des dates, sans aucune connaissance de cadence requise pour la détection d'écart basique (contiguïté = `nouvelle_période.start == dernière_période_connue.end + 1 jour`).
- **Horizons dérivés** (YTD, rolling-12 conditionnel) — calculés à la demande à partir des colonnes déjà présentes dans le fichier en cours d'analyse, jamais persistés, jamais reconstruits depuis un historique de fichiers (les fichiers bruts ne sont pas conservés — voir §11).

**Retiré de "requis maintenant" par l'arbitrage : la clôture.** Voir §14 pour la justification complète — ni "close" ni "probablement close" ne sont un fait primitif accessible au noyau déterministe du FTE v0.

## 4. Concepts temporels explicitement différés

`FiscalPeriod` riche (type/start/end/label au-delà des deux dates ci-dessus), `FiscalCalendar` (années fiscales non-calendaires), `PeriodFrequency`/`RhythmDrift` (rythme observé), `BusinessHistory`, `FutureBusinessMoment`, **sémantique de clôture** (voir §14 — reviendra via déclaration explicite d'une source, ou via `BusinessHistory`/rythme observé, jamais via une constante de tolérance inventée) — exclus par le déclencheur de réouverture lui-même ou par l'arbitrage de cette session. **`Business Moment`** : jamais défini nulle part dans le corpus canonique (confirmé par recherche exhaustive sur 10 documents cognitifs) — utilisé uniquement comme étiquette illustrative ("nouvelle période disponible"), sans schéma. Inventer sa sémantique maintenant serait la construire, pas la dériver — **différé explicitement**, pas oublié.

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

## 10. Contrat de données minimal **[RÉVISÉ]**

Un seul champ persisté — pas deux. Justification complète en §11.

| Champ | Type | Sens | Source | Déterministe | Nullable | Pourquoi maintenant | Consommateur actuel |
|---|---|---|---|---|---|---|---|
| `observed_period_end` | `DATE` | Borne de fin de la période la plus récente classée par `temporal_normalizer` pour CETTE analyse (ex. 2019-09-30) | Dérivé de `build_temporal_context()`, déjà calculé, aujourd'hui perdu | Oui | Oui (Article III — absence ≠ zéro) | Seul fait irrécupérable une fois le fichier source non conservé — nécessaire et suffisant pour comparer "période la plus récente maintenant" vs "la dernière fois" | `resolve_previous_observed_period_end()` (nouveau, ce contrat) |

Tout le reste (intervalle complet de la période courante, YTD, rolling-12, relation de comparaison) est **dérivé à chaque analyse depuis les colonnes déjà présentes dans le fichier en cours de traitement** — jamais reconstruit depuis un historique persisté. Aucune VO riche, aucune table dédiée, aucun objet avec sa propre identité (voir §"PeriodObservation — statut" ci-dessous).

**`PeriodObservation` — statut, tranché par l'arbitrage :** **PROJECTION UNIQUEMENT, pas un objet de première classe.** Rien dans le premier incrément n'a besoin de référencer une "observation de période" indépendamment de l'entrée Evidence Ledger dont elle provient — lui donner une identité propre maintenant serait une anticipation sans consommateur réel (Article IX). C'est une métadonnée portée par l'enregistrement Evidence existant, pas un nouvel agrégat.

## 11. Décision de persistance **[RÉVISÉ]**

Prémisse vérifiée directement dans le code (pas supposée) : recherche exhaustive de tout appel de stockage de fichier (`storage`, `bucket`, `.upload(`) dans `backend/` — **aucun résultat**. Les fichiers sont traités entièrement en mémoire (`file_bytes: bytes` en paramètre, jamais écrits sur un support durable). La prémisse "les fichiers bruts ne sont pas conservés" est donc confirmée empiriquement, pas supposée.

**PERSISTER :** uniquement `observed_period_end` (§10) — la borne de fin de la période la plus récente observée dans l'analyse en cours. C'est le seul fait qui, non capturé maintenant, disparaît définitivement.

**DÉRIVER (jamais persisté) :** l'intervalle complet de la période courante (recalculé à chaque analyse depuis les colonnes du fichier présent) ; la relation à la période précédente (nouvelle / écart / doublon / hors-ordre — comparaison entre la nouvelle borne et `observed_period_end` de l'entrée précédente) ; la couverture YTD ; la disponibilité du rolling-12 ; le fait qu'une information plus récente existe (§14, item H déterministe). Rien de tout cela n'est une seconde vérité (One New Truth Rule respectée) : c'est soit calculé à la volée, soit — pour `observed_period_end` — la seule et unique trace d'un fait qui n'existe nulle part ailleurs aujourd'hui.

## 12. Migration base de données **[RÉVISÉ]**

**OUI, minimale — une seule colonne.** `ALTER TABLE evidence_ledger_entries ADD COLUMN observed_period_end DATE NULL;` — nouvelle migration additive (jamais une réécriture de `v18`), compatible avec le trigger d'immutabilité (bloque `UPDATE`, pas `INSERT`). Aucune nouvelle table, aucun nouveau trigger.

## 13. Premier consommateur réel

Aucun consommateur produit/UI dans ce premier incrément. Le Golden Case Phidani **est** le premier consommateur — un test de bout en bout, pas encore une fonctionnalité livrée. Cohérent avec la nature même du "walking skeleton".

## 14. Exigence minimale Phidani — clôture retirée, exigences classées **[RÉVISÉ]**

**Clôture ("September is closed") : RETIRÉE du noyau déterministe v0.** Aucune combinaison de (données présentes + arithmétique calendaire + date système) ne permet de savoir si une organisation a réellement clos sa période — cela dépend d'un processus organisationnel (délai de clôture J+1 à J+10 selon l'organisation, écritures tardives possibles) que le FTE v0 n'observe pas. La consigne explicite de ne pas inventer de constante de tolérance confirme que ce n'est pas un fait primitif de v0. La clôture reviendra soit via une déclaration explicite d'une source/connecteur ("cet export est définitif"), soit via `BusinessHistory` (rythme de clôture observé) — jamais avant, jamais par convention arbitraire.

**Tension nommée avec `GOLDEN_CASE_001_PHIDANI.md` — signalée, non réparée :** ce document liste littéralement "inférer que septembre est probablement clos" parmi ses "Must Detect", avec la contrainte que ce ne soit jamais affirmé comme `FACT`. Le v0 tel que défini ici ne produit **aucune** affirmation de clôture, ni qualifiée ni certaine — un silence, pas une inférence prudente. Cela satisfait trivialement la contrainte "jamais FACT" (l'absence de toute affirmation ne peut jamais être une affirmation de fait), mais ne satisfait pas littéralement le "Must Detect" tel que rédigé. Cette divergence doit être arbitrée par quiconque possède l'autorité sur ce document canonique — pas silencieusement résolue ici.

**Exigences Phidani, classées (A→H de la mission d'arbitrage) :**
- **REQUIS MAINTENANT :** A (période la plus récente = septembre 2019) ; B (dernière période connue = août 2019, via `observed_period_end` persisté) ; C (septembre suit août sans écart — pure arithmétique de dates, aucune connaissance de cadence nécessaire) ; E (YTD janvier-septembre disponible — dérivé des colonnes déjà présentes dans le fichier) ; H, moitié factuelle uniquement ("une information plus récente existe").
- **DÉRIVABLE MAINTENANT MAIS NON REQUIS :** D (reformulation narrative de A+B+C, pas un fait primitif séparé) ; G (le mécanisme rolling-12 est trivial une fois assez d'historique — mais le dataset Phidani lui-même n'a que janvier-septembre 2019, donc le résultat honnête pour CE cas est "historique insuffisant", jamais une valeur fabriquée).
- **DIFFÉRÉ :** H, moitié jugement ("donc il faut relancer une analyse") — appartient à une future capacité de type `AnalysisPertinence` (ADR-003 v2), hors du périmètre `PeriodObservation`/`FiscalPeriod` autorisé par le déclencheur de réouverture.
- **NON SUPPORTÉ (par le noyau déterministe v0) :** F (clôture) — voir ci-dessus.

## 15. Semantique des échecs

Ambiguïté, absence, chevauchement, doublon, hors-ordre : chaque cas retourne un état explicite (`gap`, `duplicate`, `out_of_order`, `unknown`) — jamais résolu silencieusement en faveur d'une hypothèse implicite (Article III de la Constitution : *"une donnée absente reste absente ; elle ne devient jamais un zéro, une hypothèse implicite, ou une valeur par défaut présentée comme observée"*).

## 16. Contrat négatif **[RÉVISÉ]**

Le FTE minimal ne sait PAS : si une dégradation est "mauvaise", si une saisonnalité explique un écart, si une tendance est stratégiquement importante, si une recommandation doit être émise, si un moment est "une crise", **et — retiré par cet arbitrage — si une période est close ou probablement close**. Ces jugements restent hors du noyau déterministe, par construction — confirmé cohérent avec `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` (*"Période : déterministe, produite par le FTE, sans LLM"*).

## 17. Impact code attendu (planification, aucune exécution) **[RÉVISÉ]**

| Fichier | Changement attendu | Pourquoi | Risque | Statut |
|---|---|---|---|---|
| `backend/migrations/v23_evidence_ledger_observed_period.sql` | Nouveau, 1 colonne nullable (`observed_period_end DATE`) | Capturer un signal déjà calculé, aujourd'hui perdu | Faible, additif | NEW |
| `backend/services/evidence_ledger_service.py` | `save_evidence_capture()` reçoit et écrit ce champ unique | Point d'écriture unique | **Non trivial** — voir bloqueur §19 | MODIFY |
| `backend/services/llm_service.py` / `routers/analyze.py` | Faire circuler `temporal_context` (ou son résumé) jusqu'à `save_evidence_capture()` | Aujourd'hui non transmis à cet appel (vérifié : `analyze.py:763` ne reçoit que `analyse_id/company_id/entity_id/evidence_capture`) | Moyen — plomberie sur 2-3 fichiers | MODIFY (portée exacte à vérifier avant code) |
| `backend/services/fte_minimal.py` (nom illustratif) | Nouveau module, fonctions pures | Isoler le noyau déterministe du reste | Faible, module isolé | NEW |
| `backend/services/temporal_normalizer.py` | Aucun | Déjà correct, déjà déterministe | — | DO NOT TOUCH |
| `backend/models/decision_arc.py`, `backend/services/arc_service.py` | Aucun | Le temps de décision reste à DecisionArc | — | DO NOT TOUCH |
| `backend/migrations/v18_evidence_ledger.sql` | Aucun | Convention du dépôt : migrations additives uniquement | — | DO NOT TOUCH |
| `backend/models/financial_truth.py` (`temporal_role`) | Aucun | Contradiction nommée (§5), pas réparée ici | — | DO NOT TOUCH |

## 18. Tests requis (spécifiés, non écrits) **[RÉVISÉ]**

Même entrée → même classification (déterminisme) ; absence de signal → `NULL`, jamais une date système par défaut ; écart entre deux analyses (mois manquant) → `gap`, jamais ignoré ; deux analyses pour la même période → `duplicate`, aucune ligne écrasée ; upload hors-ordre → détecté explicitement ; **aucune affirmation de clôture n'est jamais produite, sous aucune forme, qualifiée ou non** (remplace l'ancien test de "confiance de clôture qualifiée") ; replay Phidani conforme aux exigences classées §14 (A/B/C/E requis, F absent) ; rolling-12 retourne honnêtement "historique insuffisant" sur le dataset Phidani réel, jamais une valeur fabriquée ; les six dates de `DecisionArc` prouvées non touchées (test greppé, dans le style déjà établi) ; le trigger d'immutabilité d'Evidence Ledger rejette toujours `UPDATE` après la migration ; aucun appel LLM nulle part dans le module de service ; **`QuantifiedImpact.temporal_role` n'est jamais lu par ce module** (test greppé, voir §21).

## 19. Premier incrément — IN / OUT **[RÉVISÉ]**

**IN :** 1 colonne additive (`observed_period_end`) ; un module de service pur (relation de comparaison, YTD/rolling-12 conditionnel — **sans** confiance de clôture) ; le câblage minimal nécessaire pour que Phidani passe de bout en bout sur les exigences classées REQUISES (§14) ; les tests du §18.

**OUT :** `PeriodObservation`/`FiscalPeriod` comme objets de première classe, `Business Moment`, `BusinessHistory`, `FutureBusinessMoment`, `FiscalCalendar`, **toute sémantique de clôture**, toute API/UI, toute correction du champ `temporal_role`, toute modification de `temporal_normalizer.py` ou de `DecisionArc`, tendance/saisonnalité/prévision/anomalie, minutage de recommandation (`AnalysisPertinence`), Attention Score, prompts d'agents, benchmarks inter-entreprises.

**Bloqueurs ouverts (vérification code requise avant tout code, pas une hypothèse à coder dessus) :**
1. `temporal_context` n'est aujourd'hui **pas** transmis jusqu'à `save_evidence_capture()` (vérifié par lecture directe de `routers/analyze.py:763`) — la plomberie réelle est plus large qu'un simple ajout de paramètre ; sa portée exacte doit être tracée avant d'estimer l'incrément.
2. Le scoping par `entity_id` (au lieu de `engagement_id`) reste sûr aujourd'hui (monde `1:1`) mais devra être revu le jour où `1:N` (§1.2.a) devient réel — caveat nommé, pas un bloqueur actuel.
3. ~~Fenêtre de tolérance pour "probablement close"~~ — **résolu par retrait complet de la clôture du périmètre v0** (§14). Plus un bloqueur : il n'y a plus de constante à inventer.

## 20. Recommandation **[RÉVISÉ]**

**GO** — le concept est maintenant plus petit, sans hypothèse de granularité embarquée, sans jugement de clôture prématuré, avec un seul champ persisté justifié par une prémisse vérifiée dans le code (pas supposée). Le bloqueur #1 (plomberie de transmission de `temporal_context`) reste réel mais relève d'une découverte normale au moment du code, pas d'un défaut de conception à trancher avant autorisation.

---

## 21. Isolation de `temporal_role` **[NOUVEAU]**

Confirmé : **le FTE ne doit jamais lire `QuantifiedImpact.temporal_role` comme entrée temporelle canonique.** Son commentaire ("De temporal_normalizer") laisse croire à une provenance déterministe ; en réalité il n'est peuplé, s'il l'est, que par ce que le LLM choisit d'émettre dans le JSON `quantified_impact` (vérifié par trace de code, §5). Le confondre avec la sortie réelle de `temporal_normalizer.build_temporal_context()` réintroduirait silencieusement du LLM dans un noyau qui doit en rester à zéro. Règle : toute lecture de `temporal_role` dans un module `fte_*` est une erreur de conception, à interdire par un test greppé (§18), pas seulement par convention.
