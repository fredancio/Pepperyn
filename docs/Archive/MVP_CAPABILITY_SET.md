# MVP CAPABILITY SET

**Date :** 2026-08-03
**Type :** document de référence (Niveau B), dérivé de `CAPABILITY_ROADMAP_v1.md` et `CAPABILITY_DEPENDENCY_MAP.md`.
**Question posée (Mission 7) :** quel est le plus petit ensemble de capacités permettant de vendre Pepperyn à un premier cabinet comptable ou CFO externalisé ?

---

## 1. MVP Capability Set retenu

| Capacité | Statut requis pour le MVP | Statut actuel |
|---|---|---|
| Financial Evidence | DONE | **DONE** |
| Engagement Lifecycle | DONE | **DONE** |
| Monthly Review Engine | DONE (v1 réduite, voir Dependency Map §3) | READY → à construire |

**Explicitement hors du MVP Capability Set :** Exception & Reconciliation, Recommendation Engine, Attention Score, Portfolio Intelligence, Learning Loop.

---

## 2. Justification, capacité par capacité

### Financial Evidence — requise
Un cabinet comptable ou un CFO externalisé qui engage sa propre crédibilité professionnelle en présentant un chiffre à son client ne peut pas le faire sur la base d'une affirmation non sourcée — c'est littéralement l'Article III de la Constitution : « une affirmation qui ne peut pas [être reliée à sa source] n'est pas un fait ». Sans cette capacité, il n'y a rien à vendre à un professionnel dont le métier repose sur la fiabilité de ce qu'il transmet. Déjà DONE et validée en conditions réelles (Integration Gate 1).

### Engagement Lifecycle — requise
Un cabinet ou un CFO externalisé sert, par définition, plusieurs sociétés. Un outil qui ne raisonne qu'en « un fichier uploadé » (l'état du produit avant cette capacité, Current Domain Model section A) n'est pas vendable à un professionnel dont le métier est structurellement multi-clients — ce serait vendre un outil d'analyse ponctuelle à quelqu'un dont la proposition de valeur est la continuité de la relation. Déjà DONE et validée en conditions réelles.

### Monthly Review Engine — requise, en version réduite
C'est le premier artefact tangible qu'un cabinet peut réellement remettre à son propre client — la Constitution (Article VIII) le définit comme la restitution de ce que le domaine a déjà établi. Sans un Deliverable qui suit le rythme contractuel réel de la relation (`Cadence`), le produit reste un outil que le professionnel doit se souvenir d'utiliser, pas un système qui structure sa pratique. La version retenue pour le MVP est réduite : elle lit `EvidenceLedger` (DONE) sans attendre `Recommendation Engine` (FOUNDATION) — voir la nuance documentée dans `CAPABILITY_DEPENDENCY_MAP.md` §3. Ce n'est pas une version dégradée illégitime : elle correspond exactement à ce que le produit peut aujourd'hui démontrer de façon fiable et sourcée.

### Exception & Reconciliation — non requise pour un premier client
C'est un accélérateur du travail interne du professionnel (Ideal Model E.4 : « le travail réel du Human Middle »), pas une condition de vendabilité. Un premier cabinet peut continuer à investiguer ses écarts manuellement en s'appuyant sur les Facts sourcés déjà fournis par Financial Evidence — moins efficace, mais pas bloquant pour une première vente. Sa valeur croît avec le volume de portefeuille, pas avec la première transaction commerciale.

### Recommendation Engine — non requise pour un premier client, avec réserve importante
Architecturalement FOUNDATION au sens du modèle cible (agrégat `Recommendation` unifié non construit). **Réserve : le pipeline existant (`ExecutiveDecisionModel`, `DecisionArc`, `DecisionFeedback`) produit déjà, aujourd'hui, une expérience de recommandation individuelle fonctionnelle et testée** — ce n'est pas une capacité absente du produit vendable, seulement une capacité qui n'est pas encore construite sur l'agrégat cible. Un premier cabinet peut donc déjà recevoir des recommandations chiffrées et en suivre le devenir via le chemin actuel, sans que cela nécessite d'attendre la fusion architecturale T3. Voir `CAPABILITY_TRANSITION_REPORT.md` pour la distinction complète entre code existant et capacité cible.

### Attention Score — non requise pour un premier client
C'est, par construction (Ideal Model section B, « le cœur différenciant »), la capacité qui devient indispensable quand le portefeuille grandit (15, 30, 50 mandats) — pas pour un premier client isolé, où il n'y a par définition rien à prioriser entre plusieurs Engagements. Elle devient nécessaire pour la rétention et l'expansion vers un cabinet complet, pas pour la première vente.

### Portfolio Intelligence — non requise
Dépend d'Attention Score (voir Dependency Map). Sans objet pour un unique premier client.

### Learning Loop — non requise pour un premier client
Sa valeur (« la preuve que mes recommandations passées ont porté leurs fruits », Ideal Model section G) ne se matérialise qu'après plusieurs cycles de revue avec des recommandations exécutées — elle est un argument de rétention et d'expansion, jamais un argument de première vente où il n'existe encore aucun historique à confronter.

---

## 3. Ce qui n'apparaît pas comme capacité mais conditionne la vente réelle

Deux réserves, hors du périmètre des 8 capacités (documentées ici pour ne pas être perdues, sans les élever au rang de capacité) :

- Le chemin d'ingestion de données reste manuel (upload de fichier) — Ideal Model E.2, Supporting, non traité par ce document. N'empêche pas une première vente (le produit fonctionne déjà ainsi), mais limite la fréquence réaliste de la Cadence tant qu'aucune connexion automatique n'existe.
- La dette de représentations parallèles du « résultat d'analyse » (Blueprint D.1, 5-6 objets concurrents) n'est pas résolue par le MVP Capability Set — elle reste une dette interne qui n'empêche pas la vente mais alourdit chaque capacité future construite sur ces fondations.

---

## 4. Conclusion

Le plus petit ensemble vendable à un premier cabinet comptable ou CFO externalisé est : **Financial Evidence (DONE) + Engagement Lifecycle (DONE) + Monthly Review Engine (à construire, version réduite sur Evidence seule).** C'est aussi, par construction, le chemin critique identifié dans `CAPABILITY_DEPENDENCY_MAP.md` — la coïncidence n'est pas fortuite : le chemin le plus court vers la valeur technique et le chemin le plus court vers la valeur commerciale convergent parce que les deux sont dérivés des mêmes dépendances réelles, pas de deux logiques séparées.

---

**MVP CAPABILITY SET — IDENTIFIÉ ET JUSTIFIÉ.**
