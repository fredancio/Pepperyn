# MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL.md

**Nature :** Mission 5. Conclusions **provisoires** — Mission 31.9 (`REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md`) peut les réviser, conformément à la consigne du briefing. Aucun prompt système définitif produit ici. Aucun code.

---

## Référence : ce qui existe réellement aujourd'hui

Avant de challenger la proposition, l'état réel du pipeline (`llm_service.py::run_full_pipeline`, vérifié par lecture directe) :

1. `classify_document` (Haiku) — routage.
2. Evidence Graph agent (Sonnet) — inventaire de faits traçables, **avant toute rédaction**.
3. *(si `USE_ENHANCED_PIPELINE` actif)* Financial Analyst pre-pass → Strategic CFO pre-pass — **séquentiels**, le second consomme le premier.
4. Call 1 — Analyse principale, enrichie par le pre-pass.
5. Call 2 — Vérification, recevant explicitement les décisions du Strategic CFO (`cfo_decisions_str`).
6. `_score_analysis` (LLM, 0-10) — retry sur Opus si score < 8.

Ce pipeline existant est le point de comparaison de chaque agent proposé ci-dessous — pas une page blanche.

---

## Test à trois questions, par agent proposé

### Case Framer
1. **Capacité manquante ?** Partiellement — rien aujourd'hui ne formalise explicitement le mandat, les questions, les contraintes et les horizons applicables comme un objet distinct. Mais l'Evidence Graph agent fait déjà 80 % du travail adjacent (inventaire de faits traçables avant rédaction).
2. **Améliore la décision ?** Oui, si son rôle reste strictement l'organisation de ce qui est déjà connu — un mandat mal cadré ferait diverger Analyst A et Analyst B pour de mauvaises raisons (interprétations différentes du périmètre, pas du fond), ce qui pollue le signal de convergence recherché plus loin.
3. **Fiabilité nette positive ?** Oui, à une condition stricte : le Case Framer ne doit jamais introduire de jugement interprétatif — sinon il devient un pré-ancrage caché, invisible pour Analyst A et B, qui reproduirait exactement le défaut qu'il est censé corriger.

**Verdict provisoire : MERGE avec l'Evidence Graph agent existant**, étendu pour inclure mandat/contraintes/horizons — pas un agent supplémentaire. Réduit le nombre d'appels plutôt que de l'augmenter.

### Analyst A / Analyst B
1. **Capacité manquante ?** Oui, décisivement — aucune analyse véritablement indépendante n'existe aujourd'hui. Le Financial Analyst et le Strategic CFO actuels sont séquentiels, pas indépendants.
2. **Améliore la décision ?** Oui, **à condition que l'indépendance soit structurellement garantie** (appels séparés, aucune visibilité mutuelle, aucun contexte partagé au-delà du `CognitiveCaseFile`) — pas seulement documentée comme intention.
3. **Fiabilité nette positive ?** Conditionnelle. Le briefing lui-même prévient que la convergence n'est pas une preuve de vérité — la valeur réelle de deux analystes dépend entièrement de la façon dont Convergence Signal est utilisé en aval (jamais comme un score de confiance autonome). Coût : au moins deux appels LLM là où il y en avait un.

**Verdict provisoire : KEEP.** Mais il s'agit d'un **REPLACE** du couple Financial Analyst/Strategic CFO existant, pas d'un ajout net — leurs angles proposés (A : rentabilité/cash/coûts ; B : modèle économique/risques/exécution) recouvrent presque exactement les rôles déjà écrits aujourd'hui sous ces deux noms. Le changement réel est le câblage (parallèle et indépendant au lieu de séquentiel), pas la création de rôles nouveaux. **Point à vérifier empiriquement avant confirmation définitive (Golden Cases, Mission 31.6) : est-ce que deux analystes avec des angles différents produisent réellement des vues indépendantes en pratique, ou convergent-ils systématiquement vers un même style de sortie « CFO générique » quel que soit le prompt d'angle ?** Si le taux de désaccord mesuré est structurellement bas, l'agent B n'achète pas de diversité épistémique réelle, seulement du coût.

### Adjudicator
1. **Capacité manquante ?** Oui — rien aujourd'hui ne compare deux points de vue indépendants. Le Call 2 actuel vérifie une seule chaîne contre les faits, il n'arbitre pas entre deux analyses.
2. **Améliore la décision ?** Oui, directement — c'est le composant qui rend l'investissement dans Analyst A/B rentable. Sans lui, deux analyses indépendantes ne sont que deux opinions non réconciliées.
3. **Fiabilité nette positive ?** Oui, sous réserve stricte de ne jamais forcer un consensus artificiel (déjà interdit explicitement par le briefing) — c'est cette règle qui distingue un vrai Adjudicator d'un simple LLM de synthèse.

**Verdict provisoire : KEEP — composant le plus directement justifié de toute l'architecture proposée.**

### Executive CFO
1. **Capacité manquante ?** Partiellement — aujourd'hui Call 1 fait déjà une bonne partie de cette synthèse directement, sans étape de transformation distincte d'un résultat déjà arbitré.
2. **Améliore la décision ?** Oui, **si et seulement si** son entrée est strictement l'`AdjudicationResult`, jamais le `CognitiveCaseFile` brut — sinon il redevient une troisième analyse quasi-indépendante qui réintroduit de l'ancrage à la dernière étape, exactement le défaut initial mais déplacé.
3. **Fiabilité nette positive ?** Oui, avec ce garde-fou de scope explicite.

**Verdict provisoire : KEEP, avec un contrat d'entrée strictement borné** — risque de dérive de périmètre nommé, pas supposé absent.

### Quality Gate
1. **Capacité manquante ?** Oui, largement — `_score_analysis` aujourd'hui est un auto-jugement LLM (0-10), pas un contrôle déterministe. Aucun composant actuel ne vérifie mécaniquement schéma/traçabilité/absence de recommandation sans preuve.
2. **Améliore la décision ?** Oui, directement — c'est exactement le type de garde-fou déterministe que le principe transversal du briefing (« une température faible ne suffit jamais ») appelle.
3. **Fiabilité nette positive ?** Oui, décisivement, et à coût quasi nul (déterministe, pas d'appel LLM pour l'essentiel des contrôles).

**Verdict provisoire : KEEP, et REPLACE le mécanisme de score LLM actuel** — les deux ne doivent pas coexister indéfiniment (cohérent avec la leçon « risque de conservatisme » déjà posée dans `LEGACY_MIGRATION_REVIEW_REPORT.md` Mission 9 : ne pas laisser deux mécanismes de qualité concurrents cohabiter sans échéance).

---

## Bilan de comptage — l'architecture cible est-elle plus lourde que l'existant ?

| | Pipeline réel aujourd'hui (enhanced actif) | Architecture cible (après merge Case Framer) |
|---|---|---|
| Appels LLM de routage/inventaire | classify (Haiku) + Evidence Graph (Sonnet) = 2 | classify (Haiku) + Case Framer/Evidence Graph fusionné (Sonnet) = 2 |
| Appels d'analyse | Financial Analyst + Strategic CFO (séquentiels) + Call 1 = 3 | Analyst A + Analyst B (parallèles, indépendants) = 2 |
| Appels de vérification/synthèse | Call 2 (vérification anchorée) = 1 | Adjudicator + Executive CFO = 2 |
| Contrôle qualité | `_score_analysis` (LLM) + retry Opus conditionnel | Quality Gate (déterministe, ~0 coût LLM) |
| **Total LLM (hors retry)** | **6** | **6, mais avec indépendance réelle au lieu d'un ancrage prouvé** |

**Conclusion factuelle, pas supposée : l'architecture cible n'est pas plus coûteuse en nombre d'appels que le pipeline « enhanced » déjà existant.** Le vrai changement est qualitatif (indépendance réelle, gate déterministe) et non quantitatif — un argument fort en faveur de la faisabilité, à condition de ne pas laisser le nombre d'agents dériver au-delà de ces six rôles sans repasser par le même test à trois questions.

---

**MULTI_AGENT_REASONING_ARCHITECTURE_PROPOSAL ÉTABLIE — CONCLUSIONS PROVISOIRES, SOUMISES À MISSION 31.9. AUCUN PROMPT SYSTÈME DÉFINITIF PRODUIT.**
