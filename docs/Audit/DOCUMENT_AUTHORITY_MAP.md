# DOCUMENT_AUTHORITY_MAP.md

**Nature :** Phase 2. Classification en exactement une catégorie par document/famille (A-G). Aucun document en double catégorie.

| Famille / Document | Catégorie | Justification |
|---|---|---|
| `PEPPERYN_CONSTITUTION_v1.0.md` | **A. CANONICAL** | Norme suprême déclarée comme telle par son propre texte ; aucune version concurrente de contenu identique. |
| `PEPPERYN_PRODUCT_CONSTITUTION.md` (racine, 250 lignes) | **F. HISTORICAL** | Génération antérieure, pas un doublon — utile pour comprendre l'évolution, non applicable au produit actuel. |
| Ideal Domain Model, Current Domain Model, Transformation Blueprint | **A. CANONICAL** | Cités sans ambiguïté par tous les ADR ultérieurs ; aucune version concurrente. |
| ADR-001, ADR-001A, ADR-002 | **A. CANONICAL** | Statuts RESOLVED/ACCEPTED déclarés dans leur propre texte, jamais contestés depuis. |
| ADR-003 v3 | **C. PROPOSED** | Jamais promu ACCEPTED — à ne pas confondre avec une invalidation de son contenu (déjà noté dans `CANONICAL_DOCUMENT_SET_PROPOSAL.md`). |
| ADR-003 v1, v2 | **E. SUPERSEDED** | Remplacement explicite déclaré dans le texte de la version suivante. |
| Profession Model, Model Fidelity Protocol, Foundation Closure | **A. CANONICAL** | Apex conceptuel déjà traité comme référence permanente par toutes les missions depuis sa création — fonctionnellement canonique même sans promotion sur `main`. |
| Model Gap Register, Profession Model Evidence Log | **A. CANONICAL** | Registres vides par construction, aucune ambiguïté de contenu possible — canoniques par défaut dès leur création. |
| `PROFESSION_MODEL_IMPLEMENTATION_CARTOGRAPHY.md` | **D. AUDIT / EVIDENCE** | Preuve d'écart modèle/code, ne gouverne rien directement. |
| `PRODUCT_BOARD.md` (version `main`) | **B. ACCEPTED SUPPORTING** *(provisoire — voir Phase 5)* | Factuellement exacte sur l'état livré (Portfolio Intelligence), mais incomplète (silencieuse sur North Star/Vision) — ne peut pas rester seule catégorie A tant que la reconstruction (Phase 5) n'est pas exécutée. |
| `PRODUCT_BOARD.md` (version gouvernance, `dfb8a47`) | **E. SUPERSEDED** | Contournée le même jour par la recréation sur `main` (`2f1a6b6`), jamais réintégrée — déjà établi dans `PRODUCT_BOARD_CANONICAL_ARBITRATION.md`. |
| `PRODUCT_OPERATING_SYSTEM.md`, `PROJECT_DASHBOARD.md`, `DECISION_LOOP.md` | **B. ACCEPTED SUPPORTING** | Subordonnés au Product Board, pas de contenu contradictoire identifié. |
| Foundation Recovery (5 documents) | **D. AUDIT / EVIDENCE** | Analyse et plan, ne gouverne pas directement — les décisions qu'ils appellent sont dans cette mission (Phase 6). |
| Legacy Capability Preservation — Policy | **B. ACCEPTED SUPPORTING** | Politique de gouvernance opérationnelle, explicitement pas encore Constitution, mais adoptée comme règle de travail. |
| Legacy Capability Preservation — Inventory, Matrix, Anonymization Review, Rapport de clôture | **D. AUDIT / EVIDENCE** | Preuve, pas gouvernance. |
| Strategic Deferred Work Register | **A. CANONICAL** | Registre à source unique par construction (« ne pas créer de nouveau registre » déjà une règle posée) — canonique dès sa création, mis à jour, jamais dupliqué. |
| Cognitive Architecture (7 documents) | **C. PROPOSED** | Verdict B rendu explicitement — conception non encore adoptée pour implémentation, sujette à Gates (Phase 12). |
| Capability Roadmap v1 (5 documents) | **F. HISTORICAL** | Fonction absorbée par le Product Board et le Strategic Deferred Work Register — jamais explicitement supersédée jusqu'à cette mission, corrigée ici. |
| Product Design / Pivot Sprints (Monthly Review *, Pivot Audit, etc.) | **F. HISTORICAL** | Décisions déjà exécutées et absorbées dans l'état réel de `main` (pivot Portfolio Intelligence) — utiles pour comprendre le raisonnement, non applicables comme guide d'action aujourd'hui. |
| Vision Sprint (10 documents + conclusion) | **B. ACCEPTED SUPPORTING** | Verdict GO/NO-GO explicitement rendu (Option B, long terme) — reconnu valide, subordonné aux priorités canoniques courantes. |
| UI/UX Specification Sprints (~13 documents) | **F. HISTORICAL**, à l'exception de ce qui a un consommateur réel | Partiellement absorbé (Portfolio Home, Review Briefing construits) — le reste reste une proposition non exécutée, donc historique plutôt que canonique. |
| `governance/mental-model-2026-08-05` vs `governance/foundation-closure-2026-08-05` (18 fichiers divergents) | **G. BLOCKED / UNRESOLVED** | Dépend d'un arbitrage humain non encore demandé — signalé mais hors périmètre d'exécution de cette mission (voir réserve Phase 4/14). |
| `ARCHITECTURE_MILESTONES.md`, `ROADMAP_ARCHITECTURE.md`, `WP5C_RETROSPECTIVE.md` (sur `main`) | **F. HISTORICAL** | Traces d'étapes dépassées, présentes sur `main` sans fonction de gouvernance active. |

---

## Réduction de complexité effectuée dans cette phase

Deux décisions consolident plutôt qu'elles n'ajoutent : le Capability Roadmap v1 est explicitement déclaré **F. HISTORICAL** ici — il n'était classé nulle part avant cette mission, créant une ambiguïté silencieuse (deux systèmes de pilotage, Capability Roadmap et Product Board, sans hiérarchie déclarée entre eux). Cette mission tranche : le Product Board et le Strategic Deferred Work Register sont désormais les deux seuls documents de pilotage actifs, le Capability Roadmap reste comme référence de raisonnement passé uniquement.

---

**DOCUMENT_AUTHORITY_MAP ÉTABLIE. AUCUNE CATÉGORIE MULTIPLE.**
