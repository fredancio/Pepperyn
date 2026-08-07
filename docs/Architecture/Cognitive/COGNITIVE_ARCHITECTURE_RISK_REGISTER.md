# COGNITIVE_ARCHITECTURE_RISK_REGISTER.md

**Nature :** Mission 8 (risques) + Mission 9 (ordre d'implémentation). Aucun code.

---

## Mission 8 — Risques

| Risque | Statut | Preuve / raisonnement |
|---|---|---|
| Sur-ingénierie | Potentiel | Le comptage de Mission 5 montre que l'architecture cible n'ajoute pas d'appels LLM nets par rapport au pipeline « enhanced » déjà existant — mais rien n'empêche une dérive future si chaque nouvelle capacité (Attention, Exception, apprentissage) ajoute son propre agent sans repasser par le test à trois questions. |
| Contamination entre agents | **Déjà réalisé, pas seulement potentiel** | Preuve directe : Call 2 (vérification) reçoit aujourd'hui `cfo_decisions_str`, les décisions du Strategic CFO — contamination avérée du chemin de vérification actuel. |
| Biais corrélés (Analyst A / Analyst B) | Potentiel, à mesurer | Si les deux analystes utilisent la même famille de modèle, un biais partagé du modèle affecterait les deux simultanément sans que la divergence de surface ne le révèle — d'où la proposition de profils « High Assurance » avec familles de modèles différentes (chapitre 18 du briefing), pertinente précisément pour ce risque. |
| Explosion des coûts | Potentiel, borné | Le comptage Mission 5 montre un total stable (6 appels) par rapport à l'existant — le risque n'est pas dans l'architecture proposée telle que bornée ici, mais dans une dérive ultérieure non gouvernée par le test à trois questions. |
| Contexte trop long | Potentiel | Le `CognitiveCaseFile` doit rester sélectif (Context Assembly Engine) — sans discipline de sélection stricte, chaque nouvelle faculté enrichirait le dossier jusqu'à noyer le signal utile. |
| Mémoire non pertinente | Potentiel | Même risque que ci-dessus côté mémoire — sans critère de pertinence explicite (Mission 4), le dossier grossit sans discrimination. |
| Apprentissage incorrect | Potentiel, garde-fou déjà posé | Le contrat `LearningProposal` exige preuve + niveau de confiance + périmètre — une hypothèse mal qualifiée qui se glisse dans Decision Memory sans ce contrat serait un apprentissage silencieusement incorrect. |
| Transfert de connaissance entre clients | Potentiel, garde-fou déjà posé | Distinction stricte apprentissage local / global déjà établie (chapitre 14 du briefing), cohérente avec le Model Fidelity Protocol existant — le risque est réel seulement si cette distinction n'est pas techniquement imposée (pas seulement documentée). |
| Double vérité | **Déjà réalisé, pas seulement potentiel** | `financial_truth.py` (dormant) et Evidence Ledger (T1, non fusionné) sont déjà deux registres de vérité financière distincts, documentés dans le Foundation Recovery Sprint. `temporal_normalizer.py`, découvert dans l'audit Legacy, est un doublon potentiel non résolu avec la doctrine FTE. |
| Agents qui reconstruisent des calculs déterministes | Réel, déjà nommé dans le briefing lui-même (chapitre 6 : « les agents ne doivent jamais lire directement des cellules Excel ») | À vérifier au moment de l'implémentation : le contrat `EvidenceContext` doit être la seule source de faits pour les agents, jamais un accès direct au fichier. |
| Sécurité | Voir Trust & Platform | Couvert par la couche déjà nommée dans `LEGACY_CAPABILITY_PRESERVATION_POLICY.md` Mission 1. |
| Anonymisation | **Déjà réalisé, pas seulement potentiel** | `ANONYMIZATION_CAPABILITY_REVIEW.md` — le chemin de chat V2 (Conversation Engine) envoie aujourd'hui l'essentiel d'un dossier en clair. C'est directement pertinent ici : si l'architecture cognitive cible réutilise ce même chemin sans corriger le contournement, le nouveau pipeline hériterait d'une faille déjà prouvée. |
| Accès Internet non contrôlé | Potentiel, garde-fou déjà proposé | External Knowledge Gateway (chapitre 16) — à vérifier techniquement au moment de l'implémentation, aucun connecteur externe n'existe aujourd'hui dans le code réel (confirmé par les cartographies antérieures). |
| **Risque additionnel, non listé par le briefing : Case Framer comme pré-ancrage caché** | Nouveau, identifié dans cette revue | Voir `MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md` — si le Case Framer introduit du jugement interprétatif plutôt que de la seule organisation factuelle, il devient un ancrage invisible pour Analyst A et B, reproduisant le défaut initial sous une forme plus difficile à détecter (parce que non visible dans le désaccord mesuré entre A et B). |
| **Risque additionnel : incohérences internes du briefing lui-même propagées dans le code** | Nouveau, identifié dans cette revue | `COGNITIVE_CONTRACTS_PROPOSAL.md` documente deux incohérences de nommage (`KnowledgeContext` vs `OrganizationContext`, `ExceptionContext` vs `OpenExceptions`) et une omission (`BehavioralContext`, `AttentionDecision` absents de la liste de gel) — si le code est écrit à partir du texte brut du briefing sans passer par les contrats corrigés ici, ces incohérences se propageraient directement dans l'implémentation. |

---

## Mission 9 — Ordre d'implémentation

Aucune date attribuée, conformément à la consigne. Ordre relatif uniquement, cohérent avec `FOUNDATION_RECOVERY_REVIEW.md`, `PRODUCT_BOARD_CANONICAL_ARBITRATION.md` et `STRATEGIC_DEFERRED_WORK_REGISTER.md` déjà établis :

1. **Fondation documentaire canonique** — validation de `CANONICAL_DOCUMENT_SET_PROPOSAL.md`, résolution de l'arbitrage Product Board, import documentaire (Phase 3, encore non exécutée).
2. **Engagement (T2A)** — récupération ciblée des ~8 fichiers pertinents, jamais fusion de branche entière.
3. **Evidence Ledger (T1C-A puis T1C-B)** — récupération, consommateur réel livré dans le même incrément.
4. **Correction du contournement d'anonymisation (Conversation Engine V2)** — **en parallèle des étapes 1-3, pas après** : aucune dépendance technique ne l'attache à la séquence Engagement/Evidence, et son report prolonge un écart déjà prouvé entre la promesse de confidentialité et le comportement réel.
5. **Normalisation temporelle minimale (FTE limité à `PeriodObservation`/`FiscalPeriod`)**, avec recoupement obligatoire de `temporal_normalizer.py` avant tout premier incrément — risque de doublon déjà nommé, à lever avant, pas après.
6. **Walking skeleton Phidani** (`PHIDANI_WALKING_SKELETON.md`) — première preuve de bout en bout, tranche minimale.
7. **Cette revue d'architecture des agents (déjà faite ici)** — sert de référence, pas une étape future.
8. **Nouveau pipeline de raisonnement** — recâblage d'Analyst A/B en indépendance réelle, Adjudicator, Executive CFO à scope borné, Quality Gate déterministe remplaçant le score LLM actuel.
9. **Capacités ultérieures** — Recommendation Engine enrichi, Attention Score, Enterprise Familiarization, Exception & Reconciliation au-delà du minimum — dans l'ordre déjà posé par `STRATEGIC_DEFERRED_WORK_REGISTER.md`.

**Aucun développement cognitif ne doit contourner les étapes 1-3**, conformément à l'interdiction déjà posée dans le Foundation Recovery Sprint. L'étape 4 est la seule exception explicitement autorisée à avancer en parallèle, parce qu'elle est techniquement indépendante et que son risque de report dépasse son risque d'anticipation.

---

**COGNITIVE_ARCHITECTURE_RISK_REGISTER ÉTABLI. AUCUN CODE ÉCRIT.**
