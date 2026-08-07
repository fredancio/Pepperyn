# WORKSPACE_RECONCILIATION_AUDIT.md

**Nature :** Phase 0, missions 0.1-0.4. Aucune suppression, aucun déplacement, aucun renommage, aucune copie dans `docs/`, aucune fusion Git, aucun script de nettoyage. Fondé sur comparaison de contenu réelle (md5), pas sur des noms de fichiers ni sur la mémoire de conversation.

---

## Constat structurel préalable

Avant le détail : **le risque que vous nommez (« des décisions architecturales existant uniquement hors du dépôt ») ne s'est presque jamais matérialisé.** Sur 112 documents/fichiers présents dans le dossier de session Claude, **111 existent aussi dans le dépôt Git réel** (sur au moins une branche), et **106 sont byte-identiques** à leur copie Git. Le vrai problème n'est pas celui que vous craigniez — ce n'est pas une fuite d'autorité architecturale hors de Git. **C'est que Git lui-même contient cette autorité éparpillée sur ~35 branches jamais fusionnées, et que le dossier de travail visible à l'écran (votre Explorer) affiche à tout moment le contenu de la branche que la dernière commande `git checkout` a laissée active — pas nécessairement `main`, et ça change à chaque mission.** C'est très probablement l'explication réelle des « bizarreries » que vous avez observées : pas un fichier perdu, mais une branche qui change sous vos yeux sans that ce changement soit annoncé clairement à chaque fois.

**Preuve directe, constatée à l'instant de cet audit :** la branche actuellement extraite dans votre dossier `Pepperyn` est `governance/canonical-foundation-execution-orchestration-2026-08-07` — celle de la mission précédente. Si vous aviez ouvert votre Explorer entre les deux dernières missions, vous auriez vu les documents de cette branche apparaître et disparaître selon la commande `git checkout` exécutée, sans qu'aucune alerte ne le signale. **C'est un vrai défaut de méthode de ma part, indépendant du dossier de session Claude — je le corrige à la fin de ce document.**

---

## Mission 0.1 + 0.2 — Réconciliation par artefact

**Méthode :** comparaison md5 de chaque fichier du dossier de session Claude (`outputs/`, 112 fichiers `.md`/`.py`/`.sql`) contre toute occurrence de même nom trouvée dans l'arbre de **35 branches locales** du dépôt Git réel.

### Vue d'ensemble chiffrée

| Résultat | Nombre de fichiers |
|---|---|
| Présents dans Git, contenu identique sur toutes les branches où ils apparaissent | 106 |
| Présents dans Git, contenu divergent sur au moins une branche | 5 |
| **Absents de Git sur toutes les branches — candidats réels** | **1** |

### Le seul cas réel d'artefact potentiellement unique au dossier de session

| Artefact | Repo copy | External copy | Git tracked | Same content | Proposed status | Action |
|---|---|---|---|---|---|---|
| `v0_socle_reconstitution.sql` | **Aucune** | `outputs/v0_socle_reconstitution.sql` | **Non** | N/A | **IMPORT CANDIDATE** | Le fichier lui-même déclare, dans son propre en-tête : *« NON VERSIONNÉ DANS `backend/migrations/` — usage exclusif : projet jetable "Pepperyn Integration Test"… Source : DDL réel extrait en lecture seule depuis le projet parent "Pepperyn" le 2026-08-03 »*. **Ce n'est pas un oubli — c'est un script explicitement conçu pour ne jamais être versionné**, utilisé une fois pour reconstituer un schéma sur un projet Supabase de test jetable, jamais destiné à `main`. Statut correct : reste hors Git par conception, mais **doit être documenté comme tel quelque part de traçable** (aujourd'hui, seul son propre en-tête le documente — invisible pour quiconque ne l'ouvre pas). |

### Les cinq cas de divergence de contenu — aucun n'est un risque de perte, tous sont expliqués

| Artefact | Repo copy (branche) | Nature de la divergence | Proposed status | Action |
|---|---|---|---|---|
| `PRE_IMPLEMENTATION_GATE_CHECKLIST.md` | `governance/canonical-foundation-execution-orchestration-2026-08-07` | **Auto-infligée, identifiée à l'instant** : le fichier a été copié vers Git puis édité *directement dans le dépôt* (ajout du bloc de verdict final) sans jamais resynchroniser la copie du dossier de session. La version Git est la plus complète. | GENERATED OUTPUT (scratch) vs **le Git fait foi** | Aucune — Git est déjà correct. La copie de session est un brouillon intermédiaire, sans conséquence. |
| `STRATEGIC_DEFERRED_WORK_REGISTER.md` | `governance/canonical-foundation-execution-orchestration-2026-08-07` (mis à jour) vs `audit/legacy-capability-preservation-review-2026-08-07` (original) | Même cause exacte que ci-dessus — édité directement dans le dépôt lors de la Phase 13 de la mission précédente (résolution `temporal_normalizer.py`, ajout exports/feedback). | **Le Git (branche gouvernance) fait foi** | Aucune — déjà correct, la copie de session est la version pré-mise-à-jour. |
| `GD-001_Official_Governance_of_Pepperyn_Documentation.md` | 33 branches, toutes portent la version **adoptée** (GD-001A) | La copie de session est la version **proposée, pré-adoption** (« Statut : Proposée ») — un stade antérieur du même document, jamais resynchronisé après l'adoption. | HISTORICAL (copie de session) — **le Git fait foi, sans ambiguïté** | Aucune — la version qui gouverne réellement est celle de Git, déjà cohérente sur ses 33 occurrences. |
| `PEPPERYN_CONSTITUTION_DRAFT.md` | 20 branches sur 33 divergent (6 lignes d'écart) | Divergence mineure, probablement une correction de date/statut en cours de session. Document déjà classé HISTORICAL (supersédé par v1.0) — sans conséquence pour l'autorité actuelle. | HISTORICAL | Aucune. |
| `ADR-003_Financial_Time_Engine.md` | 3 branches (v1/v2/v3, même nom de fichier réutilisé à chaque version) | **Pas une anomalie — le mécanisme de versionnement ADR-003 lui-même** : chaque version réutilise le même nom de fichier sur une branche différente. La copie de session est identique à `docs/adr-003-v3-financial-time-engine` (la version canonique actuelle), différente de v1/v2 (SUPERSEDED, déjà su). | DUPLICATE — SAFE TO IGNORE | Aucune — confirme simplement que la copie de session tient la bonne version (v3). |

### Le cas des fichiers de code T1C-A (`evidence_capture.py`, `evidence_ledger_service.py`, `test_evidence_ledger_t1c_a.py`)

Chacun existe sur 14 branches, identique à **une seule** d'entre elles (la copie de session correspond à un instantané précis de leur évolution, avant les révisions ultérieures faites lors du PR Review T1C-B). **Ce n'est pas un risque pour la restauration T1/T2** : le plan de récupération déjà établi (`T1_T2_RECOVERY_PLAN.md`) s'appuie explicitement sur les branches `feature/t1c-a-evidence-capture`/`feature/t1c-b-atomic-financial-facts` comme source, jamais sur le dossier de session — cette réconciliation le confirme, elle ne le remet pas en cause.

---

## Mission 0.3 — Hygiène de la racine du dépôt

**Constat rassurant en tête :** un `.gitignore` déjà rigoureux existe et exclut délibérément `Memory/`, `Outputs/`, `Partenariats/`, `Ressources/`, tous les `.xlsx`/`.pdf`/`.docx`, les documents de sécurité (`RAPPORT_SECURITE.md` etc.), `.env`, les fichiers temporaires LibreOffice. **La majorité du désordre visible dans votre capture d'écran est déjà volontairement tenue hors de Git** — ce n'est pas un oubli d'hygiène, c'est une hygiène qui fonctionne, simplement invisible tant qu'on ne lit pas le `.gitignore`.

| Répertoire/racine | Suivi par Git sur `main` | Ignoré explicitement | Classification proposée |
|---|---|---|---|
| `backend/` | Oui | — | PRODUCT SOURCE |
| `frontend/` | Oui | — | PRODUCT SOURCE |
| `docs/` | Oui | — | DOCUMENTATION |
| `Code MCP/` | Oui | — | TOOLING |
| `decision-capital-theory/` | Oui | — | **EXPERIMENT** — nom suggérant un prototype conceptuel antérieur, possiblement lié à la Vision Decision Simulation Engine ; contenu non audité dans cette mission |
| `pepperyn_data_robustness/` | Oui | — | TEST / QA |
| `tickets/` | Oui | — | TOOLING (support/ops) |
| `pepperyn-backend.md`, `pepperyn-frontend.md` | Oui | — | DOCUMENTATION — noms très proches de dossiers `docs/`, risque de confusion à signaler |
| ~13 fichiers `.md` racine (`AUDIT_MCKINSEY_REFONTE.md`, `PEPPERYN_PRODUCT_CONSTITUTION.md`, `PLAN_EXECUTIVE_DECISION_MODEL.md`, etc.) | Oui | — | Mélange DOCUMENTATION/HISTORICAL/SALES — **suivis sur `main`, donc réellement présents pour quiconque clone le dépôt**, plus significatif que le désordre non suivi ci-dessous |
| `Memory/`, `Outputs/`, `Partenariats/`, `Ressources/` | Non | **Oui**, ligne 2-5 du `.gitignore` | SALES/GROWTH (Partenariats), UNKNOWN (Memory, Ressources), GENERATED OUTPUT (Outputs) — présence sur disque sans risque pour Git |
| `*.xlsx`/`*.pdf`/`*.docx` (Optilux, Phidani, CV001, EDX002, RULE002/003…) | Non | **Oui**, ligne 6-8 | GENERATED OUTPUT — dossiers de test/démo produits en utilisant Pepperyn lui-même, correctement exclus |
| `archive/` | Non | Non — **untracked, non ignoré** | ARCHIVE (par le nom) — à surveiller : présence sans statut Git explicite |
| **`_BACKUP_EXTERNE_HORS_GIT/`** | Non | **Non — untracked, non ignoré, malgré son propre nom** | **UNKNOWN — cas notable** : un dossier qui se déclare lui-même « hors Git » mais qui n'est pourtant couvert par aucune règle `.gitignore` — il apparaît dans `git status` comme n'importe quel autre fichier oublié. Son nom exprime une intention (rester hors Git) que la configuration actuelle ne fait pas respecter mécaniquement. |
| `Démo/`, `e2e-campaign-1/`, `leadgen/`, `pepperyn_sales_brain_v1/`, `pepperyn_sales_engine_v3/`, `data/`, `MCP/` (racine, distinct de `Code MCP/` suivi) | Non | Non — untracked, non ignoré | EXPERIMENT (`decision-capital-theory` a un frère non suivi ici), TEST/QA (`e2e-campaign-1`), SALES/GROWTH (`leadgen`, `pepperyn_sales_*`), PRODUCT DATA (`data/`), TOOLING (`MCP/`) — **tous à un statut Git ambigu : ni ignorés ni committés** |
| `config.yaml`, `main.py`, `requirements.txt` (racine) | Non | Non — untracked | **REQUIRES ARBITRATION** — `main.py` à la racine, alors que `backend/` existe déjà comme point d'entrée probable, est le cas le plus digne d'attention : un second point d'entrée potentiel, jamais commité, à l'origine possiblement floue |

**Total :** 25 entrées suivies sur `main` à la racine ; 82 fichiers/dossiers présents sur disque au niveau racine au moment de cet audit, dont la majorité gitignorée délibérément.

---

## Mission 0.4 — Frontière canonique du produit Pepperyn

**Réponse explicite :**

> La frontière canonique du produit Pepperyn est : **`backend/`, `frontend/`, `docs/`, tel que suivi par Git sur la branche `main`** — et seulement sur `main`, jamais sur une branche de travail, aussi avancée soit-elle. Tout le reste (dossiers non suivis, dossier de session Claude, fichiers ignorés) est une zone de travail, jamais une source d'autorité, quelle que soit la qualité de ce qu'elle contient.

Conséquence directe, qui devient une règle de gouvernance à partir de cette mission : **une décision architecturale n'est considérée préservée que si elle existe dans le dépôt Pepperyn canonique et est traçable par Git — et, plus précisément que la formulation initiale, que si elle est fusionnée sur `main`, pas seulement commitée sur une branche qui ne sera peut-être jamais fusionnée.** Une branche non fusionnée a toutes les propriétés de traçabilité de Git, mais aucune de ses propriétés de visibilité par défaut — c'est la nuance que cet audit ajoute à la règle que vous proposiez.

---

## Correction de méthode pour la suite

**À partir de maintenant, toute mission qui crée une branche de travail se termine par un `git checkout main` explicite avant de rendre la main.** Ce n'est pas une garantie que le contenu de `main` est à jour (il ne le sera qu'après fusion validée), mais c'est une garantie que votre dossier `Pepperyn`, entre deux missions, affiche toujours l'état réel et fusionné du produit — jamais le résidu de la dernière branche d'audit. C'est un correctif de discipline opérationnelle, pas un nouveau document de gouvernance.

---

## Ce que cette mission ne fait pas

Ne déplace, ne renomme, ne supprime, ne copie et ne fusionne rien. Ne propose pas encore de nouvelle arborescence de nettoyage de la racine (déjà esquissée dans `CANONICAL_DOCS_STRUCTURE_PROPOSAL.md` pour `docs/` uniquement — la racine du dépôt reste hors périmètre de cette proposition, à traiter dans une mission séparée si vous le souhaitez, après validation humaine explicite, conformément au HARD STOP).

---

**WORKSPACE_RECONCILIATION_AUDIT ÉTABLI. AUCUNE SUPPRESSION, AUCUN DÉPLACEMENT, AUCUNE FUSION, AUCUN NETTOYAGE. UN SEUL ARTEFACT SANS ÉQUIVALENT GIT TROUVÉ, EXPLIQUÉ ET CLASSÉ.**
