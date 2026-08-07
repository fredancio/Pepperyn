# CANONICAL_DOCS_STRUCTURE_PROPOSAL.md

**Nature :** Phase 3 + Phase 4 (index d'autorité, `docs/README.md` proposé). Proposition de structure uniquement — **aucun déplacement de fichier exécuté dans cette mission**, cohérent avec la Phase 3 (import documentaire) du Foundation Recovery Sprint, toujours en attente de validation humaine.

---

## Phase 3 — Arborescence cible

Critère retenu : un nouveau développeur doit comprendre Pepperyn en moins d'une heure sans lire cinquante fichiers. La structure indicative de Fred est globalement adoptée, avec deux simplifications : `Audit/` regroupe tout ce qui est preuve plutôt que gouvernance (au lieu de sous-dossiers par sprint, qui recréeraient une taxonomie chronologique plutôt que fonctionnelle) ; `Archive/` reçoit explicitement tout ce qui passe en HISTORICAL ou SUPERSEDED dans `DOCUMENT_AUTHORITY_MAP.md`, sans exception.

```
docs/
  README.md                                    ← Phase 4, index d'autorité

  Foundation/
    PEPPERYN_CONSTITUTION.md                    ← A. CANONICAL
    PEPPERYN_PROFESSION_MODEL.md                ← A. CANONICAL
    MODEL_FIDELITY_PROTOCOL.md                  ← A. CANONICAL
    PROFESSION_MODEL_FOUNDATION_CLOSURE.md       ← A. CANONICAL
    MODEL_GAP_REGISTER.md                        ← A. CANONICAL (registre vivant)
    PROFESSION_MODEL_EVIDENCE_LOG.md             ← A. CANONICAL (registre vivant)

  Domain/
    CURRENT_DOMAIN_MODEL.md                      ← A. CANONICAL
    IDEAL_DOMAIN_MODEL.md                        ← A. CANONICAL
    TRANSFORMATION_BLUEPRINT.md                  ← A. CANONICAL

  Architecture/
    ADR/
      ADR-001_Evidence_Foundation.md             ← A. CANONICAL
      ADR-001A_Evidence_Ownership.md              ← A. CANONICAL
      ADR-002_Engagement_Foundation.md            ← A. CANONICAL
      ADR-003_Financial_Time_Engine_v3.md          ← C. PROPOSED (jamais ACCEPTED — le nom de fichier ne doit pas laisser croire le contraire)
    Cognitive/
      PEPPERYN_COGNITIVE_ARCHITECTURE_REVIEW.md    ← C. PROPOSED
      COGNITIVE_CAPABILITY_MAP.md                  ← C. PROPOSED
      COGNITIVE_CONTRACTS_PROPOSAL.md              ← C. PROPOSED
      MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md ← C. PROPOSED
      REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md ← C. PROPOSED
    TRUST_BOUNDARY_CLOSURE_PLAN.md                 ← B. ACCEPTED SUPPORTING (cette mission)

  Product/
    PRODUCT_BOARD.md                              ← A. CANONICAL (une fois Phase 5 exécutée)
    PRODUCT_OPERATING_SYSTEM.md                    ← B. ACCEPTED SUPPORTING
    STRATEGIC_DEFERRED_WORK_REGISTER.md            ← A. CANONICAL

  Validation/
    GOLDEN_CASES/
      GOLDEN_CASE_001_PHIDANI.md                   ← B. ACCEPTED SUPPORTING (cette mission)
    LEGACY_CAPABILITY_PRESERVATION_POLICY.md        ← B. ACCEPTED SUPPORTING

  Execution/                                       ← nouveau, absent de la proposition indicative de Fred, ajouté ici et justifié ci-dessous
    FOUNDATION_RECOVERY_EXECUTION_ORDER.md
    PHIDANI_WALKING_SKELETON_EXECUTION_PLAN.md
    REASONING_PIPELINE_MIGRATION_PLAN.md
    PRE_IMPLEMENTATION_GATE_CHECKLIST.md

  Audit/
    PROFESSION_MODEL_IMPLEMENTATION_CARTOGRAPHY.md
    GIT_FOUNDATION_RECOVERY_MAP.md
    LEGACY_CAPABILITY_INVENTORY.md
    LEGACY_CAPABILITY_REVIEW_MATRIX.md
    ANONYMIZATION_CAPABILITY_REVIEW.md
    TEMPORAL_NORMALIZER_VS_FTE_REVIEW.md
    (tous les autres documents « D. AUDIT/EVIDENCE »)

  Archive/
    (tout document classé E. SUPERSEDED ou F. HISTORICAL dans DOCUMENT_AUTHORITY_MAP.md,
     y compris PEPPERYN_PRODUCT_CONSTITUTION.md, ADR-003 v1/v2, PRODUCT_BOARD.md version
     gouvernance, Capability Roadmap v1, sprints Product Design/UI/Vision non absorbés)
```

**Écart assumé par rapport à la proposition indicative de Fred :** un dossier `Execution/` est ajouté. Justification : la Phase 5-11 de cette mission produit des documents qui ne sont ni de la doctrine (`Foundation/`, `Domain/`, `Architecture/`) ni de la preuve (`Audit/`) ni du pilotage court terme (`Product/`) — ce sont des **plans d'exécution séquencés**, une fonction distincte qui mélangée à `Product/` recréerait exactement le problème que la reconstruction du Product Board (Phase 5) cherche à corriger (ne jamais mélanger livré/conçu/hypothèse/vision). Un plan d'exécution n'est aucun des quatre — c'est une **séquence de gates**, catégorie propre.

---

## Phase 4 — `docs/README.md` (proposition)

```markdown
# Pepperyn — Index documentaire

## Si vous ne lisez qu'un document
`PEPPERYN_PROFESSION_MODEL.md` (Foundation/) — pourquoi Pepperyn existe.
Puis `PRODUCT_BOARD.md` (Product/) — ce qui est réellement construit aujourd'hui.

## Hiérarchie d'autorité — si deux documents se contredisent, lequel gagne ?

Constitution
  ↓
Profession Model (+ Model Fidelity Protocol)
  ↓
Domain Model (Current = constat, Ideal = cible) + Transformation Blueprint
  ↓
ADR acceptée (statut ACCEPTED explicite dans son propre texte — pas simplement présente dans ce dossier)
  ↓
Product Board (état réel + décisions actives)
  ↓
Plans d'exécution (Execution/)
  ↓
Code

**Ce que cette hiérarchie ne dit PAS, et qui doit être dit explicitement :**
- Un document "Audit/" ne gouverne jamais rien directement — il alimente une décision au niveau au-dessus, il ne la remplace pas. Un audit qui contredit le Product Board déclenche une révision du Product Board, il n'a pas lui-même autorité tant que cette révision n'a pas eu lieu.
- Un ADR "PROPOSED" (comme ADR-003 v3 aujourd'hui) n'a PAS autorité sur le code — seul un ADR explicitement "ACCEPTED" en a. Un ADR proposé peut néanmoins avoir autorité sur un plan d'exécution s'il est explicitement cité comme référence par ce plan (cas d'ADR-003 v3 pour le Financial Time Engine).
- Le Strategic Deferred Work Register n'est subordonné à rien — il a sa propre autorité sur une seule question : "ce chantier est-il autorisé à démarrer maintenant ?" Il ne peut jamais être contredit silencieusement par un Product Board qui ouvrirait un chantier sans déclencheur nommé.

## Documents actifs par catégorie
Voir `DOCUMENT_AUTHORITY_MAP.md` (Audit/) pour la classification complète A-G.

## Branches qui ne doivent plus servir de source d'autorité
`governance/mental-model-2026-08-05` et toute branche `governance/*` antérieure à l'import canonique (Phase 3 du Foundation Recovery Sprint, toujours non exécutée) : leur contenu fait autorité **seulement une fois importé sur `main`**, jamais par référence directe à la branche elle-même. `governance/pepperyn-profession-model-2026-08-06`, version divergente de `PRODUCT_BOARD.md` : SUPERSEDED, ne jamais citer comme source d'état produit.
```

**Challenge de la hiérarchie proposée par Fred, comme demandé explicitement :**

La hiérarchie initiale de Fred (Constitution → Profession Model → Domain Model → ADR acceptée → Product Board → Implementation Plan → Code) est correcte dans son ordre, mais elle a un angle mort : **elle ne dit rien du Strategic Deferred Work Register ni des documents d'Audit**, alors que ce sont deux familles qui interagissent avec presque tous les niveaux. Le README ci-dessus corrige cet angle mort en ajoutant deux règles explicites plutôt qu'en insérant ces deux familles dans la chaîne verticale elle-même — les y insérer directement créerait une fausse impression qu'ils gouvernent au même titre qu'une Constitution ou un Product Board, alors que leur autorité est plus étroite et spécifique (le registre gouverne « quand un chantier peut démarrer », pas « ce qui est vrai » ; l'audit alimente une révision, il ne décide pas lui-même).

---

**CANONICAL_DOCS_STRUCTURE_PROPOSAL ÉTABLIE. AUCUN FICHIER DÉPLACÉ.**
