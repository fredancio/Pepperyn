# REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md

**Nature :** Mission 31, obligatoire avant toute conclusion définitive sur le nombre d'agents, températures, modèles ou orchestration. Aucun code. Cette mission peut réviser les conclusions provisoires de `MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md`.

---

## 31.1 — Invariant Map

| Élément | Classification | Pourquoi |
|---|---|---|
| Données financières (montants, faits) | **Déterministe** | Extraits mécaniquement, jamais réinterprétés par un LLM une fois qualifiés `FACT`. |
| Période | **Déterministe** | Produite par le FTE, sans LLM, déjà établi dans ADR-003 v3. |
| Engagement (identité, relation) | **Déterministe** | Donnée structurelle, pas un jugement. |
| Knowledge Model — Confirmed Context | **Déterministe une fois confirmé** | La confirmation elle-même exige validation humaine ou règle explicite (voir Mission 2/3 dans `COGNITIVE_CAPABILITY_MAP.md`) — mais une fois confirmé, le fait ne varie plus d'une exécution à l'autre. |
| Knowledge Model — Candidate Context | **Probabiliste contrôlé** | Par nature hypothétique — sa variation entre exécutions est acceptable tant qu'il reste étiqueté `HYPOTHESIS`, jamais promu silencieusement. |
| Evidence Ledger | **Déterministe** | Registre de faits avec provenance — immuable une fois écrit. |
| Business Moment | **Déterministe** | Produit du FTE. |
| Contexte externe autorisé | **Déterministe dans sa sélection, figé dans son contenu à la date de capture** | La donnée externe elle-même (taux, norme) ne change pas rétroactivement ; seule la décision de l'inclure ou non doit être stable si les critères d'autorisation sont identiques. |
| Hypothèses déjà validées | **Déterministe (elles ne doivent pas être réinterprétées deux fois)** | Une hypothèse validée par un cycle précédent devient une donnée d'entrée stable pour le cycle suivant — pas un objet à re-débattre à chaque exécution. |
| Interprétation causale (« pourquoi ») | **Probabiliste volontaire** | C'est l'espace de jugement explicitement ouvert par le briefing — la variation y est légitime tant qu'elle reste qualifiée et arbitrable. |
| Formulation textuelle (style, tournures) | **Probabiliste volontaire, sans conséquence sur le fond** | Deux formulations différentes d'une même conclusion stable ne sont pas une violation de reproductibilité. |
| Décision de considérer une donnée comme manquante | **Déterministe** | Un contrôle de complétude (« la colonne X attendue est absente ») ne doit pas varier selon l'humeur d'un modèle. |
| Score d'attention (niveau) | **Déterministe (formule)** — cible, pas l'état actuel | Voir `COGNITIVE_CAPABILITY_MAP.md` Mission 3. |

**Principe général qui en découle :** tout ce qui décrit *l'état du monde* doit être déterministe ou strictement contrôlé ; tout ce qui décrit *une interprétation de cet état* peut varier, à condition d'être qualifié.

---

## 31.2 — Hallucination Boundary

| Interdiction | Où elle est structurellement empêchée |
|---|---|
| Inventer un chiffre | Quality Gate : toute valeur numérique dans `ExecutiveRecommendation` doit référencer un `FinancialFact` de l'`EvidenceContext` — absence de référence = échec du Gate. |
| Inventer une période | FTE seul producteur de `TemporalContext` — les agents ne calculent jamais de date eux-mêmes ; contrat d'entrée du `CognitiveCaseFile` l'impose. |
| Transformer une absence de preuve en preuve | Statut `UNKNOWN` obligatoire (Mission 31.3) — le Quality Gate refuse toute affirmation sans statut de confiance associé. |
| Transformer une hypothèse en fait | Propagation obligatoire du statut à travers tout le pipeline (Mission 31.3) — une `HYPOTHESIS` qui perd son étiquette en cours de route est un défaut de contrat, détectable par test automatisé (vérifier que chaque champ qualifié en entrée reste qualifié en sortie d'agent). |
| Transformer une corrélation en causalité sans qualification | Domaine de l'Adjudicator — doit explicitement distinguer divergence causale de divergence factuelle (Mission 31.4) ; Executive CFO ne peut pas produire de lien causal non présent dans l'`AdjudicationResult`. |
| Reconstruire différemment une vérité déjà établie par un kernel déterministe | Contrat d'entrée : les agents reçoivent le résultat du FTE/Evidence Ledger, jamais l'accès aux données brutes qui permettraient de le recalculer eux-mêmes. |
| Écraser silencieusement une contradiction ou une inconnue | `ContradictionRecord` et `UnresolvedQuestions` sont des sections obligatoires du `CognitiveCaseFile`, transmises jusqu'à l'Executive CFO — le Quality Gate vérifie leur présence en sortie si elles étaient présentes en entrée. |
| Introduire une donnée externe sans provenance | External Knowledge Gateway — seul point d'entrée autorisé pour toute donnée externe, avec source/date/juridiction obligatoires (chapitre 16 du briefing). |

---

## 31.3 — Confidence Contract

Statuts retenus : `FACT`, `STRONG_INFERENCE`, `HYPOTHESIS`, `UNKNOWN` — conformes au briefing.

**Propagation à travers le pipeline :**

`Analyst A/B` reçoit des faits déjà qualifiés dans `EvidenceContext` et doit préserver leur statut ; toute nouvelle affirmation qu'il produit doit porter son propre statut, jamais hériter par défaut du statut le plus fort disponible dans le dossier. → `Adjudicator` compare les statuts des deux analyses point par point — une divergence de statut sur la même affirmation (l'un dit `FACT`, l'autre `HYPOTHESIS`) est elle-même une divergence à signaler, pas à moyenner. → `Executive CFO` ne peut promouvoir un statut (`HYPOTHESIS` → `STRONG_INFERENCE`) qu'en citant explicitement la preuve additionnelle qui justifie la promotion — jamais par simple reformulation plus assertive. → `Quality Gate` rejette toute sortie où une recommandation s'appuie sur une affirmation `HYPOTHESIS` ou `UNKNOWN` sans que ce statut soit visible dans le texte final. → `Recommendation`/`Deliverables` : le statut doit rester lisible par l'utilisateur, au moins pour les affirmations `HYPOTHESIS` — c'est un contrat de restitution, pas seulement interne (rejoint la réserve posée dans `PEPPERYN_COGNITIVE_ARCHITECTURE_REVIEW.md` sur la non-faculté de communication). → `Memory` : une `HYPOTHESIS` persistée dans Decision Memory reste marquée comme telle indéfiniment, jusqu'à ce qu'un cycle ultérieur la confirme ou la réfute explicitement — jamais par simple ancienneté.

**`CONTRADICTION` : 5e statut ou objet orthogonal ?**

**Objet orthogonal — `ContradictionRecord`, pas un 5e statut.** Argumentation : `FACT`/`STRONG_INFERENCE`/`HYPOTHESIS`/`UNKNOWN` sont des propriétés d'une affirmation **unique**, prise isolément. `CONTRADICTION` n'est pas une propriété d'une affirmation isolée — c'est une **relation entre au moins deux affirmations** qui ne peuvent pas être vraies simultanément. Faire de `CONTRADICTION` un cinquième statut créerait une erreur de catégorie : on ne peut pas étiqueter une affirmation seule comme « contradictoire », seulement dire qu'elle contredit une autre affirmation précise. Un `ContradictionRecord` doit donc référencer explicitement les deux (ou plus) affirmations en tension, chacune conservant son propre statut individuel (une `FACT` peut contredire une autre `FACT` — cas le plus grave — tout comme une `HYPOTHESIS` peut contredire une `FACT`, cas différent en sévérité). Cette distinction a une conséquence pratique directe pour l'Adjudicator (Mission 31.4) : une contradiction entre deux `FACT` doit bloquer (Quality Gate), une contradiction entre une `FACT` et une `HYPOTHESIS` doit probablement se résoudre en faveur du `FACT` sans escalade.

---

## 31.4 — Divergence Protocol

| Type de divergence | Mécanisme |
|---|---|
| Convergence diagnostic + action | Adjudicator suffit — confirme, note le niveau de convergence comme signal (jamais comme preuve de vérité). |
| Convergence diagnostic, divergence action | Adjudicator documente les deux actions comme alternatives légitimes ; Executive CFO les présente comme options, pas comme désaccord à trancher unilatéralement. |
| Divergence causale | Adjudicator qualifie explicitement (« Analyst A attribue à X, Analyst B à Y, preuves disponibles : … ») — reste dans l'espace de jugement, pas d'escalade automatique sauf si la décision qui en découle est classée à fort impact. |
| Divergence diagnostic | Adjudicator signale ; si le diagnostic sous-jacent change la recommandation de façon matérielle, escalade vers Quality Gate pour vérifier qu'aucune des deux versions ne repose sur une erreur factuelle avant transmission à l'Executive CFO. |
| Affirmations factuellement incompatibles | **Quality Gate bloque** — ne doit jamais atteindre l'Executive CFO tel quel ; c'est un `ContradictionRecord` entre deux affirmations de statut `FACT`/`STRONG_INFERENCE`, le cas le plus sévère de la Mission 31.3. |
| Divergence uniquement parce qu'un analyste explore une hypothèse que l'autre n'aborde pas | Adjudicator ne traite pas comme une vraie divergence — note l'hypothèse comme complémentaire, pas comme conflit ; **escalade humaine seulement si l'hypothèse non partagée change matériellement la recommandation**. |

**Principe de fond :** l'Adjudicator gère le jugement et la causalité ; le Quality Gate bloque le factuel incompatible ; l'escalade humaine intervient seulement quand la divergence touche une décision à fort impact ou une incompatibilité factuelle non résolue mécaniquement — jamais pour arbitrer une simple différence de style ou d'accent.

---

## 31.5 — Reproducibility Signal

Dix exécutions sur un état du monde strictement identique. Attendu par dimension :

- **Factual stability** : quasi 100 % — les faits sont déterministes par construction (31.1). Toute variation ici est un défaut, pas une nuance acceptable.
- **Diagnostic stability** : forte mais pas textuelle — le diagnostic de fond (« la marge se dégrade à cause de X ») doit rester stable en substance sur dix exécutions, sans exiger une formulation identique.
- **Causal interpretation stability** : légitimement variable — c'est l'espace de jugement volontairement ouvert ; une variation ici n'est un défaut que si elle change la recommandation finale sans justification nouvelle.
- **Priority stability** : forte, si `AttentionDecision` est bien une formule déterministe (cible posée en 31.1/Mission 3) — une variation de priorité sur un état identique signalerait que le score n'est pas réellement déterministe malgré son statut visé.
- **Recommendation stability** : stable en substance, variable en formulation — la même décision-cadre doit revenir, les alternatives secondaires peuvent varier légèrement.
- **Uncertainty stability** : forte — les mêmes `UNKNOWN` doivent rester `UNKNOWN` d'une exécution à l'autre ; une inconnue qui disparaît sans nouvelle preuve est un défaut grave (résolution artificielle d'incertitude), pas une amélioration.

**Mesure proposée, pas seulement une comparaison textuelle :** un score composite à six facettes (une par ligne ci-dessus), chacune mesurée séparément — jamais agrégée en un seul chiffre de « reproductibilité », pour la même raison que les quatre dimensions de confiance ne doivent jamais fusionner silencieusement (chapitre 2 du briefing).

---

## 31.6 — Golden Cases

**Protocole minimal :** dataset, contexte temporel, contexte organisationnel nécessaire, vérités factuelles attendues, anomalies obligatoirement détectables, conclusions raisonnablement attendues, conclusions possibles mais non obligatoires, affirmations explicitement interdites faute de preuve, inconnues qui doivent rester inconnues.

**Replay tests mesurant :** factual stability, priority stability, recommendation stability, unsupported claim rate, agent disagreement rate, adjudication consistency, uncertainty preservation, provenance preservation — repris tels quels du briefing, cohérents avec 31.5.

**Phidani comme candidat au premier Golden Case — évaluation honnête, pas une confirmation automatique :** tel que spécifié au chapitre 23 du briefing, Phidani définit bien un dataset, un contexte temporel et des conclusions attendues. **Il ne définit pas** encore, explicitement, les « affirmations explicitement interdites faute de preuve » ni les « inconnues qui doivent rester inconnues » — deux champs obligatoires du protocole Golden Case selon ce même briefing. **Verdict : Phidani est un bon point de départ mais n'est pas encore un Golden Case complet** — il doit être enrichi de ces deux listes avant d'être utilisé comme mesure de non-régression, sans quoi le replay test ne pourrait détecter ni une invention de preuve ni une résolution artificielle d'incertitude, ses deux fonctions les plus importantes.

---

## 31.7 — Temperature & Model Configuration

| Rôle | Température proposée | Justification |
|---|---|---|
| `classify_document` | Faible (~0.1) | Tâche de routage, pas de jugement. |
| Case Framer / Evidence Graph (fusionné, Mission 5) | Faible (~0.1-0.2) | Extraction et organisation, pas d'interprétation — cohérent avec `CALL_1_BASE`/`CALL_2_BASE` déjà à 0.2 dans le code réel. |
| Analyst A / Analyst B | Modérée (~0.3-0.4) | Seul point de l'architecture où une variabilité volontaire est explicitement recherchée (espace des hypothèses) — mais bornée, jamais dans l'espace des faits (31.1). |
| Adjudicator | Faible (~0.1-0.2) | Tâche de comparaison logique, pas de créativité. |
| Executive CFO | Faible-modérée (~0.2-0.3) | Latitude de formulation et de priorisation relative, jamais d'invention factuelle. |
| Quality Gate | **Déterministe, idéalement sans LLM du tout** | Les contrôles structurants (schéma, traçabilité, citation obligatoire) sont mécaniques par nature — un LLM n'y apporte qu'un risque de faux négatif. Un usage LLM secondaire et non bloquant (détecter une formulation « qui sonne » non soutenue) est acceptable en soft-check, jamais en logique principale du Gate. |

**Rappel explicite (déjà posé par le briefing, confirmé ici) :** une température faible n'est jamais, à elle seule, un mécanisme de fiabilité suffisant. Le code réel actuel applique déjà 0.2 sur Call 1 et Call 2 — et contient pourtant l'ancrage prouvé en Mission 5. La fiabilité vient des contrats et des gates, pas du seul réglage de température.

**Rôles à reclasser en composants déterministes/hybrides plutôt qu'agents LLM :** le Quality Gate (déjà couvert ci-dessus) et une partie de la détection d'exceptions (déjà classée déterministe en Mission 3) — aucun autre rôle proposé ne justifie un passage au déterministe pur sans perdre sa fonction.

---

## 31.8 — Failure Test

| Scénario | Cause | Composant responsable | Détection | Prévention | Sévérité | Escalade humaine |
|---|---|---|---|---|---|---|
| Stochastic drift | Variabilité naturelle du LLM à température non nulle | Analyst A/B, Executive CFO | Golden Case replay (31.6) | Bornage de température (31.7) + Quality Gate sur les faits | Moyenne | Non, sauf si la recommandation finale change |
| Prompt sensitivity | Modification non versionnée d'un prompt système | Tous les agents | Golden Case replay avant tout déploiement de prompt | Versionnement explicite des prompts, non couvert par ce document (hors périmètre — aucun prompt système définitif produit ici) | Élevée | Oui si détectée en production sans replay préalable |
| Model-version drift | Changement silencieux de version de modèle par le fournisseur | Tous les agents | Golden Case replay périodique, pas seulement au déploiement | Épinglage explicite de version de modèle quand le fournisseur le permet | Élevée | Oui si un Golden Case échoue après un changement non anticipé |
| Context-selection drift | Le Context Assembly Engine sélectionne des éléments différents d'une exécution à l'autre sur un état identique | Context Assembly Engine | Test de stabilité de sélection (même état → même sélection) | Sélection déterministe par critères explicites (pertinence, confiance, provenance), pas par recherche sémantique seule | Élevée — touche directement factual/diagnostic stability | Non si le test automatisé le détecte avant production |
| Correlated model bias | Analyst A et B utilisent la même famille de modèle | Analyst A/B | Mesure du taux de désaccord (agent disagreement rate, 31.6) anormalement bas | Profil « High Assurance » — familles de modèles différentes pour A et B | Moyenne à élevée selon l'usage | Non, sauf si le taux de désaccord révèle une convergence structurelle jamais interrogée |
| Stale memory | Decision Memory ou Knowledge Model lu sans vérifier sa fraîcheur | Context Assembly Engine, Knowledge Model | `DataFreshness` (déjà un contrat FTE) non respecté par un consommateur | Contrat d'entrée obligeant à vérifier `DataFreshness` avant usage | Moyenne | Non si détecté par test |
| Conflicting memory | Deux registres de mémoire distincts (Evidence Ledger, `financial_truth.py`) divergent silencieusement | Se souvenir (faculté 3) | Déjà un risque nommé, pas hypothétique — voir `COGNITIVE_ARCHITECTURE_RISK_REGISTER.md` | Règle « One New Truth Rule » déjà appliquée à l'Evidence Ledger, à étendre explicitement | Élevée | Oui — nécessite une décision d'architecture, pas un correctif automatique |
| External-data drift | Une donnée externe autorisée change de valeur entre deux analyses (ex. taux officiel révisé) | External Knowledge Gateway | Comparaison de date de capture systématique | Horodatage obligatoire de toute donnée externe (déjà posé chapitre 16) | Faible à moyenne | Non, sauf si la révision change matériellement une recommandation déjà communiquée |
| Adjudicator overconfidence | L'Adjudicator résout une divergence réelle avec une fausse certitude | Adjudicator | Golden Case avec divergence connue et sévérité attendue documentée | Contrat interdisant explicitement la résolution silencieuse (31.4) + test dédié | Élevée | Oui si un Golden Case montre une résolution non conforme au protocole |
| Consensus illusion | Analyst A et B convergent, mais tous deux se trompent | Analyst A/B, Adjudicator | Ne peut pas être détecté par la seule architecture — nécessite un Golden Case avec vérité connue indépendante des deux analystes | Golden Case (31.6) comme seul mécanisme réellement efficace — la convergence seule ne doit jamais être traitée comme preuve (déjà posé chapitre 2 du briefing) | Élevée, et **structurellement la plus difficile à détecter de toute la liste** | Oui, dès qu'un Golden Case le révèle |

---

## 31.9 — Architecture Minimality Test

| Rôle | Capacité irremplaçable | Amélioration attendue | Variance ajoutée | Coût ajouté | Latence ajoutée | Alternative plus simple | **Verdict** |
|---|---|---|---|---|---|---|---|
| Case Framer | Cadrage explicite du mandat | Réduit le bruit de divergence non pertinent entre A/B | Faible si scope respecté | Nul si fusionné | Nul si fusionné | Fusion avec Evidence Graph | **MERGE** dans Evidence Graph |
| Analyst A | Angle financier indépendant | Détection de signaux manqués par une chaîne unique | Modérée, volontaire | +1 appel vs Call 1 seul | +1 appel parallèle (latence faible si parallélisé) | Aucune — c'est la capacité centrale manquante | **KEEP** |
| Analyst B | Angle stratégique/risque indépendant | Idem, angle complémentaire | Modérée, volontaire | +1 appel | Idem, parallèle | Aucune, sous réserve de la mesure de désaccord réel (31.6) | **KEEP, sous réserve empirique** |
| Adjudicator | Comparaison structurée de deux vues indépendantes | Rend l'investissement A/B réellement utile | Faible (tâche de comparaison) | +1 appel | +1 appel séquentiel | Aucune — sans lui, A/B perdent leur valeur | **KEEP** |
| Executive CFO | Traduction de l'arbitrage en langage décisionnel | Nécessaire pour produire un livrable actionnable | Faible si scope borné à l'AdjudicationResult | +1 appel (déjà présent aujourd'hui sous une autre forme) | Neutre par rapport à l'existant | Aucune | **KEEP, scope strictement borné** |
| Quality Gate | Contrôle mécanique de traçabilité et de cohérence | Remplace un auto-score LLM peu fiable par un contrôle vérifiable | Nulle (déterministe) | Quasi nul | Quasi nul | Aucune — c'est déjà la version « plus simple » recherchée | **KEEP, REPLACE le score LLM actuel** |

**Conclusion de la Mission 31.9 :** l'architecture, une fois Case Framer fusionné et le score LLM remplacé par un Gate déterministe, ne compte pas plus de rôles générateurs que le pipeline « enhanced » déjà existant (voir comptage détaillé dans `MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md`). **Aucune réduction supplémentaire n'est recommandée** — chaque rôle restant a un verdict KEEP justifié par une capacité qui manque aujourd'hui de façon prouvée (contamination Call 2, absence d'indépendance réelle, absence de Gate déterministe). Les conclusions provisoires de Mission 5 sont donc **confirmées, pas révisées**, à l'exception de la réserve empirique sur Analyst B (désaccord réel à mesurer par Golden Case avant confirmation définitive).

---

## 31.10 — Verdict

### REASONING RELIABILITY VERDICT

| Dimension | Note /10 | Justification |
|---|---|---|
| Factual reliability | **8/10** | Structurellement bien fondée (kernels déterministes, contrat de provenance obligatoire) — retenue à 8 et non 10 parce que le Quality Gate déterministe et le remplacement du score LLM actuel restent à implémenter, pas encore vérifiés en pratique. |
| Temporal reliability | **8/10** | FTE déjà spécifié déterministe et sans état dans ADR-003 v3, cohérent avec ce briefing — retenue à 8 à cause du doublon non résolu avec `temporal_normalizer.py`, qui doit être levé avant toute implémentation. |
| Reasoning stability | **6/10** | Le mécanisme (Confidence Contract, Divergence Protocol) est bien conçu sur le papier, mais aucune donnée empirique n'existe encore sur le taux de désaccord réel entre deux analystes indépendants — note prudente tant que 31.6 n'a pas produit de premier Golden Case complet. |
| Hallucination containment | **7/10** | Les interdictions (31.2) sont précises et chacune a un point d'application nommé — mais plusieurs de ces points d'application (Quality Gate déterministe notamment) n'existent pas encore dans le code réel. |
| Divergence handling | **7/10** | Protocole clair et non-arbitraire (31.4), argumentation solide sur `ContradictionRecord` — note retenue parce que la distinction la plus difficile (Consensus Illusion, 31.8) n'a par nature aucun mécanisme de détection interne à l'architecture, seulement les Golden Cases. |
| Reproducibility | **5/10** | Le cadre de mesure (31.5) est complet et bien pensé, mais **aucune mesure réelle n'existe** — c'est un plan de mesure, pas une propriété vérifiée. Note délibérément prudente. |
| Auditability | **7/10** | La propagation du Confidence Contract à travers tout le pipeline, si respectée, donne une traçabilité forte — mais cette propagation elle-même n'a pas de mécanisme de vérification automatique proposé au-delà d'un test manuel suggéré en 31.2. |
| Architecture minimality | **8/10** | Confirmée par comptage réel contre le pipeline existant (31.9) — pas seulement une intuition. Retenue à 8, pas 9-10, parce que la réserve empirique sur Analyst B reste ouverte. |

**Aucune dimension n'obtient 10/10** — chacune conserve un risque nommé, cohérent avec la discipline déjà établie dans cette session (ADR-003 v3 : « auto-critique, jamais 10/10 sans démonstration »).

**Risques restants, listés explicitement :**
1. Consensus Illusion (31.8) — structurellement indétectable sans Golden Case, quelle que soit la qualité de l'architecture.
2. Doublon `temporal_normalizer.py` non résolu — bloquant pour la note Temporal reliability tant qu'il n'est pas audité.
3. Golden Case Phidani incomplet (31.6) — deux champs obligatoires manquants avant utilisation comme mesure de non-régression.
4. Contournement d'anonymisation du Conversation Engine V2, non corrigé — hérité tel quel si le nouveau pipeline de raisonnement réutilise ce chemin sans correction préalable.
5. Réserve empirique sur Analyst B — la valeur réelle du deuxième analyste indépendant reste à démontrer par la mesure du taux de désaccord, pas seulement par argumentation.

---

**REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK ÉTABLI. AUCUN CODE ÉCRIT. LES CONCLUSIONS PROVISOIRES DE MISSION 5 SONT CONFIRMÉES AVEC UNE RÉSERVE EMPIRIQUE NOMMÉE.**
