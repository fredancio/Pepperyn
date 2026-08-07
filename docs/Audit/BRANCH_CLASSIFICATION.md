# BRANCH_CLASSIFICATION.md

**Nature :** Phase 13. 76 branches locales recensées (`git for-each-ref`). Classification groupée par statut réel, pas par nom. **Aucune branche n'est supprimée par cette mission.** La consigne de Fred interdit la suppression de branches ambiguës ; seule une recommandation est produite ici.

---

## MERGED / CONTENU PROMU dans cette consolidation

Ces branches ont fourni le contenu maintenant physiquement importé dans `docs/` sur `consolidation/canonical-repository-2026-08-07` : `governance/mental-model-2026-08-05`, `governance/pepperyn-profession-model-2026-08-06`, `governance/canonical-foundation-execution-orchestration-2026-08-07`, `architecture/cognitive-synchronization-review-2026-08-07`, `audit/legacy-capability-preservation-review-2026-08-07`, `audit/workspace-reconciliation-2026-08-07`, `audit/product-board-canonical-arbitration-2026-08-06`, `capability/portfolio-intelligence-increment-1-2026-08-05`, `audit/integration-gate-1-2026-08-03` (GD-001), `docs/adr-003-financial-time-engine`, `docs/adr-003-v2-financial-time-engine`, `docs/adr-003-v3-financial-time-engine`. Contenu recouvrable par cette consolidation + Git history. **Ne pas supprimer maintenant** : leur contenu complet n'a pas fait l'objet d'une comparaison fichier-par-fichier exhaustive (seuls les fichiers nommément listés dans les missions précédentes ont été importés) — une suppression prématurée romprait la traçabilité si un fichier oublié y restait.

## HISTORIQUE UNIQUEMENT (déjà mergé dans `main` avant cette mission, ou remplacé)

`chore/sprint-0-repo-hygiene`, `docs/adr-002-engagement-foundation`, `release-1/wp1a-product-catalog`, `release-1/wp1b-billing-migration`, `release-1/wp1d-frontend-alignment`, `release-1/wp1e-stabilization`, `release-1/wp4a-commercial-catalog-frontend`, `release-1/wp4b-scale-self-service`, `release-1/wp4c-commercial-offer-alignment`, `layout-baseline-v1`, `pre-monthly-review-snapshot-2026-08-02`, `feature/commercial-consistency-audit`, `feature/monthly-review-quality-banner-2026-08-04`, `feature/portfolio-home-increment-1-2026-08-05`, `feature/portfolio-home-increment-2-2026-08-05`, `feature/review-briefing-implementation-2026-08-05`, `fix/portfolio-closed-only-clients-2026-08-05`, `release-gate/portfolio-closed-only-fix-report-2026-08-05`, `release-gate/portfolio-increment-1-2-report-2026-08-05`, `prototype/client-review-readiness-ui`. Historique probable mais **non re-vérifié fichier par fichier dans cette mission** (hors périmètre — le périmètre est la documentation, pas un audit exhaustif de 76 branches).

## CONTIENT ENCORE DU MATÉRIEL ACTIF UNIQUE (à ne pas toucher)

`feature/t1c-a-evidence-capture`, `feature/t1c-b-atomic-financial-facts`, `feature/t2a-engagement-persistence` — code T1/T2 accepté, non mergé (voir §5 du README). `backup/main-before-foundation-recovery-2026-08-06` — filet de sécurité explicite, à conserver jusqu'à confirmation que la récupération a réussi.

## BLOQUÉ / NON RÉSOLU

`governance/foundation-closure-2026-08-05` — diverge de `governance/mental-model-2026-08-05` sur 18 fichiers, non arbitré (voir README §"Point bloquant non résolu" et `Audit/DOCUMENT_AUTHORITY_MAP.md`). **Ne pas supprimer, ne pas trancher silencieusement.**

## PROPOSÉ / VISION / EXPÉRIMENTAL (non promu, non historique — décisions en attente ou non retenues)

`governance/adr-numbering-cleanup-2026-08-05`, `governance/capability-roadmap-v1-2026-08-03`, `governance/decision-loop-and-vision-2026-08-05`, `governance/enterprise-knowledge-model-2026-08-05`, `governance/enterprise-knowledge-model-refinement-2026-08-05`, `governance/knowledge-acquisition-principle-review-2026-08-05`, `governance/portfolio-release-gate-product-board-2026-08-05`, `governance/product-board-canonical-on-main-2026-08-05`, `governance/product-board-post-closed-only-fix-2026-08-05`, `governance/product-board-v1-2026-08-05`, `governance/reconciliation-2026-08-05`, `portfolio-daily-priority-screen-2026-08-05`, `product/decision-followup-plan-2026-08-05`, `product/implementation-sprint-1-2026-08-03`, `product/monthly-review-design-sprint-1-2026-08-03`, `product/narrative-journey-audit-2026-08-05`, `product/pivot-review-2026-08-03`, `product/portfolio-card-review-2026-08-05`, `product/portfolio-home-implementation-plan-2026-08-05`, `product/portfolio-home-product-validation-2026-08-05`, `product/portfolio-intelligence-mvp-2026-08-05`, `product/return-loop-design-2026-08-05`, `product/ui-specification-sprint-2026-08-03`, `product/ux-implementation-sprint-1-2026-08-03`, `prototype/organisation-sharing-demo-2026-08-05`, `prototype/portfolio-external-user-testing-2026-08-05`, `vision/decision-simulation-engine-2026-08-04`, `vision/enterprise-data-acquisition-review-2026-08-05`, `vision/reasoning-reliability-review-2026-08-05`, `audit/foundation-recovery-sprint-2026-08-06`, `audit/profession-model-implementation-cartography-2026-08-06`. Contenu potentiellement utile mais non arbitré comme canonique — recouvrable par nom de branche, référencé dans `Audit/DOCUMENT_AUTHORITY_MAP.md` quand applicable. **Ne pas supprimer.**

## CANDIDAT SÛR À SUPPRESSION (recommandation seulement — aucune suppression exécutée)

`main.lock.bak`, `main.lock.disabled`, `main.lock.stale.1782675753675425826` — artefacts de verrouillage accidentels (pas des branches de travail), datés du 22-29 juin, sans lien avec du contenu documentaire ou du code. Recommandation : suppression sûre après confirmation explicite de Fred, car aucune valeur informationnelle identifiée. **Non supprimées dans cette mission** en l'absence de cette confirmation.

---

**76 branches classées. 0 branche supprimée. 3 candidats sûrs identifiés (artefacts de lock), en attente de confirmation humaine explicite avant toute suppression.**
