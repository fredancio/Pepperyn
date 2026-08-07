# COGNITIVE_CONTRACTS_PROPOSAL.md

**Nature :** Mission 4 (contrat `CognitiveCaseFile`) + Mission 7 (liste des contrats à figer). Aucun code — schémas conceptuels uniquement.

---

## Mission 4 — Contrat cible du `CognitiveCaseFile`

Principe directeur : les agents ne reçoivent jamais l'historique brut, seulement un dossier assemblé, borné et traçable. Le contrat doit être **extensible sans obliger les agents à reconstruire les fondations** — chaque section peut grandir en richesse sans changer sa forme.

```
CognitiveCaseFile
├── mandate: AnalysisMandate
│     — question(s) posée(s), périmètre, contraintes, horizons applicables
│     — produit par Case Framer / Evidence Graph (voir MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md)
│
├── evidence: EvidenceContext
│     — faits qualifiés (FACT/STRONG_INFERENCE/HYPOTHESIS/UNKNOWN), provenance, sheets_verified
│     — jamais de montant sans référence à une source
│
├── temporal: TemporalContext
│     — BusinessMoment, DataFreshness, ComparisonHorizons, TemporalWarnings
│     — produit exclusivement par le FTE, jamais recalculé ailleurs
│
├── organization: OrganizationContext
│     — extrait pertinent du Knowledge Model (Confirmed/Candidate/Unknown/Contradiction)
│     — jamais l'intégralité du Knowledge Model — sélection justifiée par pertinence
│
├── exceptions: OpenExceptions
│     — cas ExceptionCase ouverts et pertinents pour ce dossier
│
├── decisions: DecisionContext
│     — recommandations passées pertinentes, leur statut, leur résultat observé
│
├── behavior: BehavioralContext
│     — motifs Business History pertinents (ex. clôtures tardives récurrentes)
│     — **absent de la liste de gel Mission 7 dans le briefing d'origine alors que cité ici au chapitre 15 — incohérence interne du briefing, corrigée dans ce document**
│
├── open_questions: UnresolvedQuestions
│     — inconnues explicites, non résolues, qui ne doivent jamais être silencieusement comblées
│
└── external: ExternalContext (optionnel, autorisé uniquement)
      — passé exclusivement par l'External Knowledge Gateway (Mission 16 du briefing)
      — chaque élément porte source, date, juridiction, provenance
```

**Règle de sélection (Context Assembly Engine) :** chaque section est peuplée par pertinence, validité temporelle, confiance, importance, provenance, risque d'omission — jamais par défaut « tout ce qui existe ». La recherche sémantique peut assister la sélection, jamais introduire une donnée sans provenance.

**Règle d'extensibilité :** un futur enrichissement (par exemple, un Business Moment plus riche, ou une nouvelle catégorie d'exception) doit pouvoir ajouter des champs à l'intérieur d'une section existante sans changer la forme du contrat lui-même ni obliger un agent à connaître le détail interne d'une section qu'il ne consomme pas.

---

## Mission 7 — Contrats à figer avant tout code

Liste du briefing, vérifiée et corrigée :

| Contrat | Conservé tel quel | Correction apportée |
|---|---|---|
| `EvidenceContext` | Oui | — |
| `TemporalContext` | Oui | — |
| `KnowledgeContext` | Renommé `OrganizationContext` | Cohérence avec le nom utilisé au chapitre 15 du briefing (`OrganizationContext`), qui diverge du nom utilisé au chapitre 7 (`KnowledgeContext`) — incohérence interne à corriger avant le gel, pas après. |
| `ExceptionContext` | Renommé `OpenExceptions` | Même type de correction — le chapitre 15 utilise `OpenExceptions`, à aligner. |
| `DecisionContext` | Oui | — |
| `CognitiveCaseFile` | Oui | Voir Mission 4 ci-dessus. |
| `IndependentAnalysis` | Oui | — |
| `AdjudicationResult` | Oui | — |
| `ExecutiveRecommendation` | Oui | — |
| `LearningProposal` | Oui | — |
| **`BehavioralContext`** | **Ajouté** | Cité au chapitre 15 (composant du `CognitiveCaseFile`) mais absent de la liste de gel du chapitre 7 — omission corrigée ici. |
| **`AttentionDecision`** | **Ajouté** | Cité au chapitre 12 avec un schéma explicite (niveau, raisons, facteurs, informations manquantes, action suivante) mais absent de la liste de gel — omission corrigée. |
| **`ConfidenceContract`** | **Ajouté** | Le statut `FACT`/`STRONG_INFERENCE`/`HYPOTHESIS`/`UNKNOWN` traverse explicitement plusieurs étapes du pipeline (Mission 31.3) — il mérite d'être un contrat nommé et figé en tant que tel, pas seulement une propriété implicite de chaque autre contrat. |
| **`ContradictionRecord`** | **Ajouté, sous réserve de la décision Mission 31.3** | Voir argumentation dans `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` §31.3 — objet orthogonal, pas un 5e statut. |

**Principe transversal de gel :** un contrat figé fixe ses champs et leurs invariants, jamais son mécanisme de production interne. `TemporalContext` peut être produit demain par un FTE enrichi sans que sa forme change — c'est précisément ce qui permet la construction verticale progressive (Chapitre 21 du briefing).

---

**COGNITIVE_CONTRACTS_PROPOSAL ÉTABLI. AUCUN CODE ÉCRIT.**
