# PEPPERYN_COGNITIVE_ARCHITECTURE_REVIEW.md

**Nature :** synthèse de l'Architecture Synchronization Review. Aucun code, aucune migration, aucun prompt système modifié. Document de conception uniquement, sur branche dédiée non fusionnée.

**Réserve de méthode :** cette revue a été fondée, chaque fois que possible, sur une lecture directe du code réel de `main` plutôt que sur le seul texte du briefing — en particulier `backend/services/llm_service.py::run_full_pipeline` (Pipeline v4), qui existe déjà et anticipe partiellement l'architecture décrite. Les écarts entre le pipeline réel et l'architecture proposée sont un élément de preuve central de cette revue, pas une hypothèse.

---

## Ce que le pipeline réel révèle avant même de discuter du modèle cible

Avant de challenger les huit facultés, un fait de code change la nature de la discussion : le problème d'ancrage que le briefing décrit comme un risque théorique de l'architecture actuelle **existe déjà, prouvé par le code**, et il est plus précis que « les agents lisent la conclusion précédente ».

`run_full_pipeline` (Pipeline v4) exécute, dans l'ordre : classification (Haiku) → Evidence Graph agent (Sonnet, inventaire de faits traçables) → **si le feature flag `USE_ENHANCED_PIPELINE` est actif** : Financial Analyst pre-pass **puis** Strategic CFO pre-pass, **séquentiels, le second lisant le premier** → Call 1 (Analyse principale, enrichie par les deux pre-pass) → Call 2 (Vérification), qui reçoit explicitement `cfo_decisions=cfo_decisions_str` — **les décisions déjà prises par le Strategic CFO sont transmises telles quelles au « vérificateur »**. Ce n'est pas une vérification indépendante, c'est un contrôle de cohérence d'une chaîne qui a déjà convergé avant que la vérification commence. Le score de sortie (`_score_analysis`, LLM, retry sur Opus si < 8) est un auto-jugement probabiliste, pas un Quality Gate déterministe.

Ce fait change la lecture de toute la suite : l'architecture proposée (Case Framer → Analyst A/B indépendants → Adjudicator → Executive CFO → Quality Gate) n'est pas une invention ex nihilo. Ses briques existent déjà sous d'autres noms (Evidence Graph ≈ proto-Case Framer ; Financial Analyst + Strategic CFO ≈ Analyst A + Analyst B, mais câblés en série au lieu d'en parallèle indépendant). Le vrai travail n'est donc pas d'ajouter des agents, mais de **recâbler des rôles déjà écrits pour restaurer l'indépendance qui manque aujourd'hui** — un chantier plus resserré, et plus vérifiable, que ce que le nombre de documents demandés pourrait suggérer.

---

## Mission 1 — Les huit facultés sont-elles complètes, distinctes, non redondantes, correctement séparées ?

**Verdict global : oui pour l'essentiel, avec deux frontières à préciser et une non-addition à justifier.**

**1. Comprendre l'organisation (faculté 2) vs Se souvenir (faculté 3) — frontière à préciser, pas une redondance.** Le Knowledge Model (faculté 2) et les registres de mémoire (Evidence Ledger, Decision Memory, Business History, Interaction Memory — faculté 3) risquent d'être lus comme deux endroits qui « savent » la même chose. Ce n'est pas le cas si la frontière est posée explicitement : **les registres de faculté 3 sont le journal brut, immuable, source de vérité** ; **le Knowledge Model de faculté 2 est l'état de croyance courant, synthétisé, versionné, révisable**, dérivé des registres mais avec ses propres invariants (Fact/Confirmed/Candidate/Unknown/Contradiction) qui ne sont pas de simples projections mécaniques. C'est l'équivalent d'un journal d'événements et d'une vue matérialisée — related mais pas redondants, à condition que cette relation soit nommée. Elle ne l'est pas dans le briefing actuel — **correction proposée : ajouter explicitement au chapitre 7 que le Knowledge Model est dérivé des registres de la faculté 3, jamais une source concurrente.**

**2. Percevoir (faculté 1) vs Questionner (faculté 5) — frontière à préciser.** Le risque de chevauchement porte sur la détection de données manquantes, mentionnée dans les deux facultés. Ligne proposée : **Percevoir répond « ce fait est-il bien formé et traçable ? »** (un objet `FinancialFact` a-t-il une origine, une période, une valeur) ; **Questionner répond « cet ensemble de faits est-il cohérent et complet par rapport à ce qu'on attendait ? »** (une marge qui augmente pendant que le cash diminue n'est pas un défaut de perception, c'est un signal de jugement). Distinctes, mais Questionner doit consommer des faits déjà correctement perçus — dépendance à sens unique, jamais l'inverse.

**3. Faculté manquante : la restitution/communication n'est délibérément pas une 9e faculté — à justifier, pas à ignorer.** Le briefing ne propose pas de faculté « communiquer » distincte, et c'est correct : produire un livrable (export, réponse de chat) n'est pas un acte de jugement professionnel supplémentaire, c'est la mise en forme de ce que Raisonner et Prioriser ont déjà produit. Ceci est cohérent avec l'Article VIII de la Constitution (« aucun livrable ne calcule ou ne déduit ce qui n'existe pas déjà en amont ») et avec l'audit déjà mené sur les exports (`LEGACY_CAPABILITY_REVIEW_MATRIX.md` — confirmé sans appel LLM). **Réserve à nommer explicitement, pas à ajouter comme faculté : le contrat de ce qui est montré à l'utilisateur (niveau d'incertitude affiché, divergences visibles) est cognitivement structurant, même si l'acte de rendu ne l'est pas — ce contrat doit être fixé au même niveau que les huit facultés, dans `COGNITIVE_CONTRACTS_PROPOSAL.md`, pas oublié parce qu'il n'a pas sa propre faculté.**

**Aucune faculté ne doit être supprimée ou déplacée** — le test de complétude (huit responsabilités cognitives d'un CFO, du signal brut à l'apprentissage) ne révèle aucun trou structurel une fois les deux frontières ci-dessus précisées.

---

## Mission 10 — Question centrale

**Le système décrit constitue-t-il une architecture cohérente de CFO augmenté, ou une collection trop ambitieuse de composants conceptuels ?**

Réponse sans complaisance : **c'est une architecture cohérente dans son raisonnement, mais elle n'a pas encore été stress-testée contre le code réel avant cette session** — et le stress-test qui vient d'être fait (comparaison avec `run_full_pipeline`) est plutôt rassurant : la cible n'invente pas une complexité nouvelle, elle corrige un câblage déjà présent. Le risque réel n'est pas conceptuel, il est **d'exécution** : le nombre de documents et de contrats à figer avant tout code (voir `COGNITIVE_CONTRACTS_PROPOSAL.md`) est significatif, et rien dans cette architecture ne garantit par construction qu'elle sera implémentée dans l'ordre minimal proposé plutôt que dans un Big Bang — c'est une discipline à tenir, pas une propriété acquise du document.

---

## Verdict de clôture

Voir `REASONING_RELIABILITY_AND_REPRODUCIBILITY_FRAMEWORK.md` pour le détail (Mission 31) et le verdict numérique par dimension.

```
COGNITIVE ARCHITECTURE SYNCHRONIZATION REVIEW COMPLETED.

FINAL VERDICT:
B — COGNITIVE ARCHITECTURE COHERENT WITH NAMED RESERVATIONS
```
