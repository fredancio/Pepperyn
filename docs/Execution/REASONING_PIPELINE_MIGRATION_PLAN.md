# REASONING_PIPELINE_MIGRATION_PLAN.md

**Nature :** Phase 11. Migration formalisée uniquement — **aucun agent codé dans cette mission**. Fondé sur la lecture réelle de `backend/services/llm_service.py::run_full_pipeline` (Pipeline v4).

---

## Current → Target, transition par transition

| Rôle actuel | Fichier/fonction réelle | Rôle cible | Réutilisation | Suppression | Recâblage | Risque | Test | Feature flag | Rollback |
|---|---|---|---|---|---|---|---|---|---|
| `classify_document` | `llm_service.py` | Conservé identique | Totale | Aucune | Aucun | Faible | Existant | N/A | N/A |
| Evidence Graph agent | `_run_evidence_graph_agent` | **Fusionné avec Case Framer** — étendu pour inclure mandat/contraintes/horizons (verdict MERGE, `MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md`) | Élevée — prompt de base conservé, système étendu | Aucune fonction supprimée, étendue | Sortie enrichie transmise à `CognitiveCaseFile` au lieu de `evidence_graph_section` seul | Moyen — un mandat mal cadré pollue tout le reste | Test Golden Case : le mandat produit ne contient aucun jugement interprétatif (règle du Case Framer) | `USE_COGNITIVE_PIPELINE` | Retour à `_run_evidence_graph_agent` seul si le mandat introduit une dérive mesurée |
| Financial Analyst pre-pass | `_run_financial_analyst_prep`, prompt `FINANCIAL_ANALYST_SYSTEM` | **Recâblé en Analyst A**, appel parallèle et indépendant au lieu de séquentiel | Élevée — le prompt système existant est un bon point de départ, à ajuster pour retirer toute référence à un « pré-pass » qui présupposerait un Call 1 à venir | Fonction actuelle conservée pendant la transition (voir plan d'exécution) | Isolé — ne reçoit plus le `CognitiveCaseFile` partagé avec aucune trace de Strategic CFO | Élevé — c'est le changement le plus structurant (rupture de la séquentialité qui cause l'ancrage prouvé) | Golden Case : taux de désaccord mesuré avec Analyst B (réserve empirique déjà nommée) | `USE_COGNITIVE_PIPELINE` | Fallback vers pipeline actuel en un flag |
| Strategic CFO pre-pass | `_run_strategic_cfo_prep`, prompt `STRATEGIC_CFO_SYSTEM` | **Recâblé en Analyst B**, idem | Élevée, même logique | Idem | Idem — **ne reçoit plus `analyst_findings` en entrée**, c'est précisément la correction de l'ancrage | Élevé, même raison | Idem | `USE_COGNITIVE_PIPELINE` | Idem |
| Call 1 (`call_analysis_v3`) | `llm_service.py` | **Rôle scindé** — sa fonction de synthèse est reprise par Executive CFO (entrée bornée à l'`AdjudicationResult`, pas au dossier brut), sa fonction d'analyse initiale est reprise par Analyst A/B | Partielle — le prompt d'origine (`ANALYSIS_SYSTEM_V3`/`ENHANCED_ANALYSIS_SYSTEM`) sert de base à Executive CFO, adapté pour ne plus recevoir de données brutes | Conservée pendant la transition | Executive CFO reçoit désormais un `AdjudicationResult`, jamais `parsed_data`/`anonymized_data` directement — garde-fou de scope explicite | Élevé — risque de dérive de périmètre si le contrat d'entrée n'est pas strictement imposé | Test de contrat : Executive CFO échoue si son entrée contient un champ hors `AdjudicationResult` | `USE_COGNITIVE_PIPELINE` | Fallback |
| Call 2 (`call_verification_v3`) | `llm_service.py`, reçoit `cfo_decisions_str` | **Remplacé par Adjudicator** — ne reçoit plus jamais les décisions déjà prises par un agent en amont, reçoit deux analyses indépendantes | Faible — la logique de vérification actuelle est structurellement contaminée (reçoit `cfo_decisions`), pas réutilisable telle quelle | Conservée pendant la transition | Compare A et B au lieu de vérifier une chaîne unique déjà convergée | Élevé — c'est le composant qui corrige directement la contamination prouvée | Test explicite : injecter deux analyses factuellement incompatibles dans un Golden Case, vérifier que l'Adjudicator ne les moyenne jamais | `USE_COGNITIVE_PIPELINE` | Fallback |
| `_score_analysis` (score LLM 0-10) | `llm_service.py` | **Remplacé par le Quality Gate déterministe** (`deterministic_gate.py`, Phase 10) | Aucune — logiques de nature différente (probabiliste vs déterministe) | **RETIRE une fois le Gate validé sur Golden Case**, jamais avant | Le retry sur échec de qualité devient un échec de Gate, pas un score bas | Moyen — le Gate doit couvrir au moins les mêmes cas que le score actuel détecte, sans quoi c'est une régression de qualité déguisée en simplification | Golden Case : comparer, sur les cas historiques disponibles, ce que le score LLM aurait signalé vs ce que le Gate détecte | `USE_COGNITIVE_PIPELINE` | Coexistence temporaire : les deux mécanismes tournent en parallèle, log de divergence, avant retrait définitif du score |

---

## Éléments transversaux à intégrer explicitement, pas en périphérie

- **Interdiction d'ancrage** : implémentée structurellement par l'absence de tout partage de contexte entre Analyst A et Analyst B au-delà du `CognitiveCaseFile` — testable (voir Phase 10, étape 5).
- **Indépendance A/B** : garantie par l'appel parallèle (pas seulement « pas de lecture mutuelle » documentée — l'implémentation doit rendre l'appel simultané, pas juste non-séquentiel dans l'ordre du code).
- **Trust Gateway** : tous les appels ci-dessus, sans exception, doivent traverser le Trust Gateway minimal (`TRUST_BOUNDARY_CLOSURE_PLAN.md`) — cette migration ne doit pas être exécutée avant que Gate D soit passé, sans quoi le nouveau pipeline hériterait des contournements déjà prouvés.
- **ConfidenceContract** : chaque fonction listée ci-dessus doit désormais retourner des affirmations qualifiées (`FACT`/`STRONG_INFERENCE`/`HYPOTHESIS`/`UNKNOWN`), pas du texte libre — c'est un changement de signature, pas seulement de comportement interne.
- **ContradictionRecord** : produit par l'Adjudicator exclusivement, jamais par Analyst A/B individuellement (cohérent avec l'argumentation DDD de `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` §31.3 — la contradiction est une relation entre deux affirmations, pas une propriété d'une seule).
- **Quality Gate déterministe** : seul point de la migration qui réduit un coût plutôt que d'en ajouter un — à ne pas retarder par prudence excessive, contrairement aux autres transitions plus délicates.

---

**REASONING_PIPELINE_MIGRATION_PLAN ÉTABLI. AUCUN AGENT CODÉ. AUCUN PROMPT SYSTÈME DÉFINITIF.**
