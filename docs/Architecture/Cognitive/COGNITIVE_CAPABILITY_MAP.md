# COGNITIVE_CAPABILITY_MAP.md

**Nature :** Mission 2 (propriétaires DDD) + Mission 3 (frontière déterministe/probabiliste). Aucun code.

---

## Mission 2 — Propriétaires DDD

| Faculté / Registre | Aggregate propriétaire | Domain Service | Persisté | Dérivé | Sans état |
|---|---|---|---|---|---|
| **1. Percevoir** | Aucun aggregate propre — produit des VO (`FinancialFact`, `PeriodObservation`, `SourceDocument`, `EntityReference`, `DeclaredContext`, `ExternalFact`) rattachés à l'aggregate **Evidence** (ADR-001/001A) | Service de normalisation (aujourd'hui `file_parser.py`, `FileConnector`) | Les VO eux-mêmes + provenance, dans Evidence Ledger | Rien — c'est la source | Le service de parsing lui-même |
| **2. Comprendre l'organisation** | **KnowledgeModel**, propriété d'**Engagement** (même logique déjà retenue pour BusinessHistory dans une session antérieure — pas un objet flottant global) | Enterprise Familiarization (écrit dedans), service de réconciliation Knowledge Model | Fact / Confirmed Context / Candidate Context / Unknown / Contradiction, avec origine/date/confiance/périmètre | Vue matérialisée dérivée des registres de la faculté 3, **avec ses propres invariants versionnés** — pas un simple cache | Aucun |
| **3. Se souvenir — Evidence Ledger** | **Evidence** (déjà établi, ADR-001/001A) | — | Faits + provenance | Rien | — |
| **3. Se souvenir — Decision Memory** | Candidat : **DecisionRecord**, propriété d'Engagement (cohérent avec la migration DecisionArc→Engagement déjà notée) | — | Recommandations proposées/acceptées/rejetées/exécutées/observées | Rien | — |
| **3. Se souvenir — Business History** | Propriété d'**Engagement**, pas du FTE (déjà tranché lors du challenge de frontière antérieur à cette session) | Détection de motifs (`RhythmDrift`, `RecurringSignal` — déjà spécifiés déterministes dans ADR-003 v3) | Motifs récurrents qualifiés | Dérivé de l'historique d'observations FTE, mais persisté comme connaissance durable, pas recalculé à chaque fois | Le détecteur de motifs lui-même |
| **3. Se souvenir — Interaction Memory** | Candidat, à concevoir : **InteractionRecord**, propriété d'Engagement | — | Questions/réponses/confirmations/responsabilités | Rien | — |
| **4. Se situer dans le temps (FTE)** | Aucun — **sans état par conception, déjà établi dans ADR-003 v3** (« sans état propre, sauf décision contraire explicitement justifiée ») | Domain Service pur, kernel Supporting | Rien — le FTE ne persiste rien lui-même | `BusinessMoment`, `FinancialTemporalContext`, etc. — tout est dérivé à la demande de PeriodObservation + Engagement | Le FTE tout entier |
| **5. Questionner (Exception & Reconciliation)** | **ExceptionCase**, nouvel aggregate, bounded context propre (Supporting), lecture seule sur Evidence Ledger — pas propriété d'Engagement (c'est une question d'intégrité des faits, pas de relation) | Service de réconciliation (égalités, rapprochements, cohérence inter-périodes) | Cas d'exception qualifiés (observation → question → explication → réconciliation) | Rien à l'origine — dérive des faits Evidence, mais le cas lui-même, une fois ouvert, est persisté et suit son propre cycle de vie | Les contrôles déterministes eux-mêmes |
| **6. Raisonner (agents)** | Aucun — les agents ne possèdent rien. Consomment `CognitiveCaseFile` (read model, pas un aggregate), produisent des VO (`IndependentAnalysis`, `AdjudicationResult`, `ExecutiveRecommendation`) qui sont ensuite persistés **par** Decision Memory, jamais directement par un agent | Les agents eux-mêmes sont les « Domain Services » probabilistes, sans persistance propre | Rien directement — la persistance passe toujours par Decision Memory | Tout ce qu'ils produisent est dérivé du CognitiveCaseFile | Tous — stateless par construction, conforme à la mission (« Ils ne modifient pas directement les registres ») |
| **7. Prioriser (Attention Engine)** | Aucun aggregate propre — Domain Service cross-Engagement, portfolio-level | Service de scoring d'attention | `AttentionDecision`, probablement recalculée à la demande plutôt que persistée durablement (à trancher — voir réserve) | Entièrement dérivé (FTE + exceptions + décisions + Engagement) | Le service de scoring |
| **8. Agir et apprendre — apprentissage local** | **DecisionRecord** (Engagement) | — | Hypothèse confirmée/réfutée, confiance modifiée | — | — |
| **8. Agir et apprendre — apprentissage professionnel global** | **Aucun Engagement** — propriété de la couche de gouvernance Profession Model elle-même (`MODEL_GAP_REGISTER.md`, `PROFESSION_MODEL_EVIDENCE_LOG.md`, déjà existants et déjà distincts pour cette raison précise) | Processus de promotion (anonymisation, validation humaine, non-régression — déjà spécifié dans le Model Fidelity Protocol) | Entrées de registre, jamais une règle globale sans promotion explicite | — | — |

**Réserve explicite sur Prioriser :** le briefing ne tranche pas si `AttentionDecision` doit être persistée (historisée pour audit) ou seulement recalculée à la demande. Recommandation : persister au moins un instantané par cycle de Portfolio, pour permettre un futur Reproducibility Signal sur la priorisation elle-même (Mission 31.5) — sans quoi la stabilité de priorité ne serait jamais vérifiable a posteriori.

---

## Mission 3 — Frontière déterministe / probabiliste

| Opération | Classification | Justification |
|---|---|---|
| Normalisation de fichier en `FinancialFact` | **Déterministe** | Structure connue, pas de jugement — mais **écart avec le code réel** : `file_parser.py` appelle aujourd'hui `llm_service` (confirmé par grep dans l'audit legacy). Cible : réduire ou justifier explicitement ce recours, pas le perpétuer sans le nommer. |
| Classification de colonnes sensibles (anonymisation) | **Déterministe** | Déjà confirmé dans `ANONYMIZATION_CAPABILITY_REVIEW.md` — aucun LLM dans le module. |
| Détection d'exceptions (égalités, rapprochements, cohérence inter-périodes) | **Déterministe** | Le briefing l'exige explicitement ; c'est un contrôle, pas un jugement. |
| Formulation de la question posée à propos d'une exception | **LLM autorisé** | Traduire une anomalie détectée en langage clair est un acte de formulation, pas de décision factuelle. |
| Décider si les données sont correctes malgré une exception | **LLM interdit** | Le briefing l'interdit explicitement — seule une réconciliation déterministe ou une confirmation humaine peut clore un cas. |
| BusinessMoment / contexte temporel (FTE) | **Déterministe, sans LLM** | Déjà établi dans ADR-003 v3, confirmé cohérent avec le briefing. |
| Detection de motifs Business History (`RhythmDrift`, `RecurringSignal`) | **Probabiliste contrôlé** (statistique, pas LLM) | Déjà spécifié ainsi dans ADR-003 v3 — pas un LLM, mais pas un simple seuil binaire non plus. |
| Analyst A / Analyst B — interprétation | **Probabiliste volontaire (contrôlé)** | Diversité de jugement recherchée, dans l'espace des hypothèses, jamais des faits — température non nulle justifiée. |
| Adjudicator — comparaison des deux analyses | **Probabiliste contrôlé, faible latitude** | Tâche de comparaison logique, pas de créativité — proche du déterministe sans l'être totalement (nécessite compréhension du langage). |
| Executive CFO — synthèse | **Probabiliste contrôlé** | Latitude sur la formulation et la priorisation relative des recommandations, jamais sur les faits sous-jacents. |
| Promotion Candidate Context → Confirmed Context (Knowledge Model) | **LLM interdit pour la décision finale — validation humaine ou règle déterministe explicite requise** | Une croyance ne devient un fait organisationnel confirmé que par confirmation humaine ou déclaration explicite — jamais par accumulation silencieuse de confiance LLM. |
| Quality Gate (schéma, traçabilité, absence de recommandation sans preuve) | **Déterministe** | C'est tout l'objet du Gate — voir réserve dans `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` sur le remplacement du score LLM actuel. |
| Score de qualité actuel (`_score_analysis`, code réel) | **Probabiliste — non conforme à la cible** | Aujourd'hui un auto-jugement LLM joue le rôle qu'un Quality Gate déterministe devrait jouer — écart nommé, à corriger, pas à ignorer. |
| AttentionDecision — niveau (score) | **Déterministe (formule)** | Doit être une fonction calculable des facteurs (matérialité, urgence, fraîcheur...), pas une évaluation libre. |
| AttentionDecision — raisons/explication textuelle | **LLM autorisé, à partir des facteurs déterministes uniquement** | Peut mettre en mots les facteurs déjà calculés, jamais en inventer de nouveaux. |
| Apprentissage local (Decision Memory) | **Déterministe pour l'enregistrement, probabiliste contrôlé pour la détection de motif** | Enregistrer un résultat est mécanique ; détecter qu'un motif se répète est un jugement contrôlé, similaire à Business History. |
| Promotion vers apprentissage professionnel global | **LLM interdit pour la décision, gouvernance humaine obligatoire** | Déjà la règle du Model Fidelity Protocol — confirmée, pas à réinventer. |

---

**COGNITIVE_CAPABILITY_MAP ÉTABLIE. AUCUN CODE ÉCRIT.**
