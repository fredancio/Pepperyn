# FOUNDATION_RECOVERY_EXECUTION_ORDER.md

**Nature :** Phase 6. Résout une contradiction documentaire réelle, **produite par cette session elle-même** (pas seulement héritée). Aucun code, aucune migration.

---

## La contradiction, nommée précisément

`T1_T2_RECOVERY_PLAN.md` (Foundation Recovery Sprint) recommande l'ordre **T1C-A → T1C-B → T2A (Engagement)**, justifié par le risque technique (T1C-A/B sont des diffs propres et additifs ; T2A nécessite une extraction ciblée à haut risque). Mais `FOUNDATION_RECOVERY_REVIEW.md`, réponse à la question de Recovery Gate n°7 (« quel chemin minimal permet le cas vertical Phidani/FTE »), écrit : *« Engagement restauré et réellement consommé → Evidence Ledger restauré et réellement consommé → alors seulement, un premier incrément FTE… »* — soit l'ordre inverse.

**Ces deux réponses ont été écrites dans la même session, à quelques missions d'écart, sans qu'aucune ne cite l'autre.** C'est exactement le type de contradiction documentaire que cette mission a pour objet de faire disparaître — elle ne doit pas être répétée une troisième fois par un nouveau document qui choisirait arbitrairement l'un des deux.

---

## Reprise depuis les dépendances réelles, pas depuis les noms « T1 »/« T2 »

**Dépendance technique (git) :** le plan de récupération recommande déjà, pour T2A spécifiquement, une **extraction ciblée de 8 fichiers**, jamais une fusion de branche entière (127 fichiers, 119 hors périmètre). Une extraction ciblée par copie de fichiers ne dépend pas de l'état d'avancement de la fusion T1C-A/B sur `main` — le fait que la branche `feature/t2a-engagement-persistence` soit historiquement construite par-dessus T1C-B dans son arbre Git est **sans conséquence** une fois qu'on a renoncé au `git merge` de la branche entière. **Conclusion : aucune dépendance technique dure n'impose T1 avant T2, contrairement à ce que la structure des branches pourrait laisser croire.**

**Dépendance DDD :** ADR-001A ancre explicitement l'Evidence Ledger sur `Entity` en transition, précisément pour ne **pas** dépendre d'Engagement — c'est la raison d'être de cet ancrage transitoire. L'Evidence Ledger n'a donc **aucune dépendance de domaine** envers Engagement. Symétriquement, Engagement (ADR-002) est un remplacement/enrichissement de la relation Company/Entity — il n'a **aucune dépendance de domaine** envers l'Evidence Ledger non plus. **Conclusion : T1 et T2 sont mutuellement indépendants du point de vue DDD.**

**Ce qui reste, donc, pour trancher : le risque d'exécution et la valeur débloquée — pas une dépendance.**

- **Risque d'exécution :** T1C-A (1 commit, 6 fichiers, 0 suppression) est le cas le plus sûr possible pour valider que le *processus* de récupération lui-même fonctionne (fusion, tests, non-régression) avant de s'attaquer au cas le plus délicat (T2A, extraction ciblée dans une branche à 93 % de bruit).
- **Valeur débloquée :** Engagement (T2) est cité comme dépendance par davantage de chantiers du `STRATEGIC_DEFERRED_WORK_REGISTER.md` (Enterprise Familiarization, Business History, Decision Follow-up indirectement) que l'Evidence Ledger seul.

**La contradiction se résout ainsi : la réponse de `FOUNDATION_RECOVERY_REVIEW.md` (Engagement avant Evidence) répondait à une question de valeur à long terme pour le cas vertical FTE — elle n'aurait jamais dû être lue comme une recommandation de séquencement de récupération immédiate. `T1_T2_RECOVERY_PLAN.md` répondait à une question de risque d'exécution — c'est la question pertinente pour décider quoi merger en premier, cette semaine.** Ce sont deux questions différentes, pas deux réponses concurrentes à la même question — l'erreur de cette session a été de ne pas nommer cette différence explicitement au moment de la deuxième réponse.

---

## Ordre retenu, définitif pour cette mission

**1. T1C-A → 2. T1C-B → 3. T2A (Engagement, extraction ciblée) → 4. Correction Trust Boundary (parallèle, aucune dépendance) → 5. Normalisation temporelle minimale (FTE, après recoupement `temporal_normalizer.py`, voir Phase 8) → 6. Walking Skeleton Phidani.**

Justification unique et suffisante : **risque croissant, exécuté du plus sûr au plus délicat**, cohérent avec la règle « le consommateur réel doit être livré dans le même incrément que la restauration » déjà posée dans `FOUNDATION_RECOVERY_REVIEW.md` — chaque étape valide le processus de récupération avant d'aborder l'étape suivante, plus risquée.

**Ce que cet ordre ne prétend pas :** il ne prétend pas qu'Engagement est moins important que l'Evidence Ledger — `STRATEGIC_DEFERRED_WORK_REGISTER.md` le contredirait directement. Il affirme seulement que **l'ordre de récupération technique** et **l'ordre d'importance stratégique** sont deux questions distinctes, et que cette mission tranche la première, pas la seconde.

---

**FOUNDATION_RECOVERY_EXECUTION_ORDER ÉTABLI. CONTRADICTION RÉSOLUE PAR LES DÉPENDANCES RÉELLES, PAS PAR L'ORDRE HISTORIQUE DES SPRINTS.**
