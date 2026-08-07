# CAPABILITY DEPENDENCY MAP

**Date :** 2026-08-03
**Type :** document de référence (Niveau B), dérivé de `CAPABILITY_ROADMAP_v1.md`.
**Objet :** démontrer qu'aucune capacité n'est construite prématurément, et identifier le chemin critique jusqu'à une première version commercialisable.

---

## 1. Carte de dépendances (Mission 5)

Convention : `A → B` signifie « B dépend de A » (B ne peut pas atteindre DONE, ni raisonnablement démarrer, tant que A n'est pas au moins substantiellement avancé).

```
┌───────────────────────┐       ┌───────────────────────┐
│ Capability 1            │       │ Capability 2            │
│ Financial Evidence       │       │ Engagement Lifecycle     │
│ STATUS: DONE             │       │ STATUS: DONE             │
└───────────┬────────────┘       └───────────┬────────────┘
            │                                 │
            │         ┌───────────────────────┘
            │         │
            ▼         ▼
┌───────────────────────────────────┐
│ Capability 3                         │
│ Exception & Reconciliation           │
│ STATUS: FOUNDATION                   │
│ depends on: Financial Evidence       │
└───────────┬───────────────────────┘
            │
            │         ┌─────────────────────────────────────┐
            │         │ Capability 2 (Engagement Lifecycle)    │
            ▼         ▼
┌───────────────────────────────────┐       ┌───────────────────────────────────┐
│ Capability 4                         │       │ Capability 5                         │
│ Recommendation Engine                │       │ Monthly Review Engine                │
│ STATUS: FOUNDATION                   │       │ STATUS: READY                        │
│ depends on: Financial Evidence,      │       │ depends on (cible) : Financial       │
│   Engagement Lifecycle,              │──────▶│   Evidence, Engagement Lifecycle,    │
│   Exception & Reconciliation         │ (cible,│   Recommendation Engine              │
│                                       │ non    │ NUANCE : v1 réduite possible sur     │
│                                       │ bloq.) │   Evidence seule (voir §3)           │
└───────────┬───────────────────────┘       └───────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────┐
│ Capability 8                         │
│ Learning Loop                        │
│ STATUS: FOUNDATION                   │
│ depends on: Recommendation Engine    │
└───────────┬───────────────────────┘
            │
            │         ┌─────────────────────────────────────┐
            │         │ Capability 1 (Financial Evidence)      │
            │         │ Capability 2 (Engagement Lifecycle)    │
            │         │ Capability 4 (Recommendation Engine)   │
            ▼         ▼
┌───────────────────────────────────┐
│ Capability 6                         │
│ Attention Score                      │
│ STATUS: FOUNDATION                   │
│ depends on: Financial Evidence,      │
│   Engagement Lifecycle,              │
│   Recommendation Engine (historique),│
│   Learning Loop (repondération)      │
└───────────┬───────────────────────┘
            │
            ▼
┌───────────────────────────────────┐
│ Capability 7                         │
│ Portfolio Intelligence               │
│ STATUS: FOUNDATION                   │
│ depends on: Attention Score          │
└───────────────────────────────────┘
```

**Lecture stricte des flèches, telle que déduite des sources :**

| Dépendance | Source |
|---|---|
| Financial Evidence → Exception & Reconciliation | Ideal Model E.4 : une Exception se détecte sur des Facts ; Blueprint D relations (Financial Evidence → Exception, Customer/Supplier) |
| Financial Evidence → Recommendation Engine | Ideal Model H.3 : « Toute Recommendation cite sa Provenance » |
| Engagement Lifecycle → Recommendation Engine | Ideal Model D : Published Language `engagement_id`, toute Recommendation est scoping par un Engagement |
| Exception & Reconciliation → Recommendation Engine | Ideal Model D : « une Recommendation cite des Facts et peut répondre à une ou plusieurs Exceptions » |
| Recommendation Engine → Learning Loop | Learning ne s'applique qu'à des Recommendations `executed` (Ideal Model E.6 : `ActualOutcome` ne peut être renseigné que sur une Recommendation déjà exécutée) |
| Financial Evidence, Engagement Lifecycle, Recommendation Engine → Attention Score | Blueprint C.6, explicite : « placée en phase T4, après que sa matière première soit disponible — jamais avant » |
| Learning Loop → Attention Score | Ideal Model workflow F.10 : « ce Learning influence la pondération de l'Attention Score » |
| Attention Score → Portfolio Intelligence | Il n'y a rien à agréger au niveau portefeuille avant que le signal existe au niveau d'un Engagement |
| Financial Evidence, Engagement Lifecycle → Monthly Review Engine (cible) | Ideal Model E.7 : un Deliverable lit `EvidenceLedger` (Evidence) pour une période ouverte par la `Cadence` (Engagement) |
| Recommendation Engine → Monthly Review Engine (cible, non bloquant en v1) | Ideal Model E.7 : « un Deliverable ne fait QUE lire EvidenceLedger + Recommendation déjà clos/acceptés » — voir nuance §3 |

---

## 2. Chemin critique (Mission 6)

**Question posée :** si Pepperyn devait être terminé avec le minimum de travail possible, quelles capacités constituent le chemin critique jusqu'à une première version commercialisable ?

Le chemin critique n'est pas la totalité du graphe — Portfolio Intelligence, par exemple, n'est le prérequis de rien et peut rester en FOUNDATION indéfiniment sans bloquer la valeur commerciale (même logique que la Phase T6 du Blueprint : « un nettoyage, jamais un prérequis fonctionnel »).

**Chemin critique identifié :**

```
Financial Evidence (DONE)
        │
        ▼
Engagement Lifecycle (DONE)
        │
        ▼
Monthly Review Engine (READY → à construire, v1 réduite sur Evidence seule)
        │
        ▼
════════ PREMIÈRE VERSION COMMERCIALISABLE (voir MVP_CAPABILITY_SET.md) ════════
        │
        ▼
Exception & Reconciliation + Recommendation Engine (en parallèle, toutes deux ne dépendent
   que de capacités déjà DONE — aucune dépendance mutuelle stricte au démarrage)
        │
        ▼
Learning Loop
        │
        ▼
Attention Score
        │
        ▼
Portfolio Intelligence (hors chemin critique — extension)
```

**Pourquoi ce chemin est le plus court :**

- Financial Evidence et Engagement Lifecycle sont déjà DONE — le chemin critique démarre donc à Monthly Review Engine.
- Monthly Review Engine est la seule capacité restante dont une version utile (voir nuance §3) ne dépend que de capacités déjà terminées — c'est mécaniquement le prochain maillon disponible, indépendamment de toute préférence.
- Exception & Reconciliation et Recommendation Engine ne dépendent, elles aussi, que de capacités DONE (Financial Evidence, Engagement Lifecycle) — elles peuvent démarrer en parallèle l'une de l'autre, comme T1/T2/T3 l'étaient dans le Blueprint (section F : « le seul point de parallélisation du plan »). Une dépendance logique existe (Exception → Recommendation, une recommandation peut répondre à une exception) mais elle n'empêche pas de démarrer les deux fondations en parallèle.
- Learning Loop et Attention Score sont, comme dans le Blueprint (T4, « le premier point de convergence obligatoire »), les points où le plan **doit** attendre que plusieurs fondations soient posées — elles ne peuvent pas être avancées.
- Portfolio Intelligence reste hors chemin critique : c'est une extension d'Attention Score, jamais un prérequis de la valeur commerciale de base.

---

## 3. Nuance sur Monthly Review Engine — dépendance cible vs. dépendance de lancement

Le modèle cible (Ideal Domain Model E.7) exige qu'un `Deliverable` lise à la fois `EvidenceLedger` et des `Recommendation` closes. Appliqué à la lettre, Monthly Review Engine devrait donc attendre Recommendation Engine (FOUNDATION) avant de démarrer.

**Position retenue dans cette carte :** une version 1 de Monthly Review Engine, strictement sur `EvidenceLedger` (sans citation de Recommendations closes), est un sous-ensemble honnête et non-régressif du modèle cible — pas une violation de la dépendance, une réduction de périmètre assumée et documentée. Elle correspond à ce que le produit sait déjà démontrer de façon fiable (des faits sourcés, une cadence de revue) sans attendre la fusion complète de la mémoire décisionnelle. Une v2 de Monthly Review Engine, enrichie des Recommendations closes, redeviendra alors strictement conforme au modèle cible une fois Recommendation Engine avancée.

Cette nuance est reportée telle quelle dans `MVP_CAPABILITY_SET.md` et `CAPABILITY_TRANSITION_REPORT.md`.

---

**CAPABILITY DEPENDENCY MAP — CARTE ET CHEMIN CRITIQUE PRODUITS.**
