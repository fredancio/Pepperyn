# ADR-001 — Evidence Foundation
**Phase :** T1-A du Transformation Blueprint
**Statut :** Proposé, pour signature par comité d'architecture
**Sources autorisées :** Current Domain Model · Ideal Domain Model · Transformation Blueprint · Pepperyn Constitution v1.0
**Nature :** décision d'architecture. Aucun code, aucune migration, aucun modèle, aucun prompt, aucun test n'est modifié par ce document.

---

## 1. Contexte

Le Transformation Blueprint identifie la couche de preuve financière comme le point de levier le plus favorable de toute la transformation (section C.3) : à chaque analyse, le domaine produit déjà un inventaire de faits sourcés (un fait par observation ou déduction directement lisible dans les données), et un modèle de typage rigoureux pour représenter ce type de fait existe déjà, avec ses propres invariants déjà corrects. Ni l'un ni l'autre n'est aujourd'hui conservé au-delà de l'exécution d'une seule analyse : l'inventaire de faits est reconstruit puis jeté à chaque fois, et le modèle de typage n'est branché à aucune persistance ni à aucun consommateur de production.

La Constitution (Article III — La Vérité) exige que toute affirmation importante soit traçable, qu'une absence de donnée ne devienne jamais un zéro, et que toute transformation reste explicable. Ces exigences sont aujourd'hui honorées le temps d'une exécution, mais pas dans la durée : rien dans l'état persistant du domaine ne conserve la preuve elle-même, seulement le texte qui en a été dérivé. Le Modèle Idéal fait de cette couche de preuve un sous-domaine Core à part entière (Financial Evidence & Truth) et un préalable explicite à tout le reste — aucune Recommendation à boucle fermée, aucun futur signal d'attention, ne peut reposer sur des faits qui n'existent nulle part de façon stable.

ADR-001 est la première décision d'architecture de la transformation parce qu'elle conditionne toutes les suivantes : le Blueprint place l'activation de cette couche en phase T1, avant toute autre transformation, précisément parce qu'elle ne dépend de rien d'autre et que tout le reste en dépend.

---

## 2. Problème

Trois dettes précises, déjà documentées, motivent cette décision :

- **La preuve est éphémère.** L'inventaire de faits sourcés produit à chaque analyse n'est jamais conservé au-delà de l'appel qui le produit. Une fois l'analyse restituée, il n'existe plus aucun moyen, dans l'état du domaine, de retrouver sur quelle cellule, quelle période, quelle feuille reposait une affirmation donnée.
- **Un modèle correct existe mais reste inerte.** Le module qui modélise déjà les faits financiers avec provenance, hiérarchie de fiabilité et invariant « absence de donnée ≠ zéro » n'est lu par aucun consommateur de production. La rigueur existe dans le code ; elle n'existe pas dans le comportement réel du produit.
- **Le résultat d'une analyse mélange le fait et le récit.** L'objet qui persiste aujourd'hui une analyse porte simultanément des données factuelles et du contenu narratif dérivé, sans séparation. Cette confusion est identifiée comme une dette de modélisation majeure (Current Domain Model, section M) et empêche toute évolution propre de l'un sans risquer de perturber l'autre.

Sans résoudre ces trois points, aucune étape ultérieure du Blueprint ne peut être construite sur une fondation stable : ni la fusion en une Recommendation à boucle fermée (T3), ni le signal d'attention (T4), ni le recâblage de l'objet central de restitution (T5).

---

## 3. Décision

**Le domaine adopte l'Evidence Ledger comme registre persistant, additif et faisant autorité pour tout fait financier sourcé, construit sur le modèle de typage déjà existant pour la preuve financière.**

Concrètement, ceci signifie :
- ce que la couche de preuve produit déjà à chaque analyse cesse d'être jeté et devient une donnée persistée du domaine ;
- le modèle de typage déjà écrit pour représenter un fait sourcé (montant, période, nature, provenance, niveau de confiance) devient la forme obligatoire de tout nouveau fait entrant dans cette persistance ;
- cette persistance est strictement additive : rien de ce qui existe aujourd'hui (résultat d'analyse, exports, mémoire, recommandations, arcs décisionnels) n'est modifié, supprimé ou redirigé par cette décision.

ADR-001 crée la fondation. Elle ne redirige aucun consommateur existant vers elle — c'est volontaire (voir section 9).

---

## 4. Alternatives étudiées

### Alternative A — Statu quo (ne rien construire)
- **Avantages :** aucun effort, aucun risque immédiat.
- **Inconvénients :** viole durablement l'Article III de la Constitution (traçabilité) ; bloque toute évolution future faute de matière première stable ; laisse s'accumuler la dette déjà documentée.
- **Raison du rejet :** contredit directement plusieurs articles de la Constitution et immobilise l'ensemble du Blueprint.

### Alternative B — Concevoir un nouveau modèle de preuve, sans réutiliser l'existant
- **Avantages :** liberté de conception totale, aucune contrainte héritée.
- **Inconvénients :** le modèle déjà écrit est déjà rigoureux et déjà conforme aux invariants requis ; le reconstruire revient à écarter un actif correct et à introduire un risque de divergence par rapport à des règles déjà éprouvées.
- **Raison du rejet :** viole le principe d'architecture selon lequel la simplicité du domaine prévaut sur la sophistication de l'implémentation (Constitution, Article XII). Reconstruire quand un modèle correct existe déjà est une sophistication inutile.

### Alternative C — Migration en un seul mouvement (introduire Evidence Ledger et recâbler immédiatement l'objet central de restitution et les exports)
- **Avantages :** évite une période où deux systèmes coexistent.
- **Inconvénients :** expose l'objet le plus visible du produit (celui que lisent les trois formats d'export) à un changement non validé indépendamment ; contredit le séquencement du Blueprint, qui place ce recâblage en toute dernière étape précisément pour ne le tenter qu'une fois le reste stabilisé.
- **Raison du rejet :** contredit la stratégie de migration incrémentale retenue dans le Blueprint et le principe prudentiel qui a guidé l'ensemble des travaux précédents.

### Alternative D — Persister l'inventaire de faits tel quel, sans le faire passer par un typage strict
- **Avantages :** mise en œuvre plus rapide, aucune conversion nécessaire.
- **Inconvénients :** aucun invariant protégé (rien n'empêche qu'une donnée absente soit stockée comme un zéro) ; aucune hiérarchie de fiabilité de la provenance.
- **Raison du rejet :** viole directement l'Article III (une donnée absente ne devient jamais un zéro ; une transformation doit rester explicable) et renonce sans raison à la rigueur déjà disponible.

### Alternative E — Retenue : persister l'inventaire de faits en le faisant passer par le modèle de typage déjà existant, de façon strictement additive
Développée en sections 3 et 5.

---

## 5. Nouveau modèle

**Evidence** — un fait financier unitaire : un montant (ou son absence explicite), la période à laquelle il se rapporte, la nature de ce qu'il mesure, sa provenance et son niveau de confiance. Une Evidence ne porte jamais de jugement, jamais de recommandation, jamais d'interprétation. Sa seule responsabilité est de représenter fidèlement ce qui est observable ou strictement déductible des données sources, et de porter la trace de son origine.

**Evidence Ledger** — le registre qui rassemble, dans la durée, l'ensemble des Evidence produites pour une relation suivie. Sa responsabilité est double : garantir que rien de ce qu'il contient n'est réécrit silencieusement une fois enregistré, et servir de référence unique et interrogeable pour tout autre objet du domaine qui a besoin de faits établis — aujourd'hui aucun consommateur, demain la Recommendation et le signal d'attention. L'Evidence Ledger ne contient aucune narration ; il ne produit aucune conclusion par lui-même.

**Financial Truth** — non un objet mais le principe organisateur qui gouverne l'ensemble : toute grandeur financière manipulée par le domaine, quel que soit l'endroit où elle est consommée, obéit aux mêmes règles de traçabilité, de non-invention et de hiérarchie de fiabilité. Financial Truth est le contrat ; l'Evidence Ledger en est le registre persistant ; l'Evidence en est l'unité atomique.

Cette décomposition correspond directement au sous-domaine Core « Financial Evidence & Truth » du Modèle Idéal, et au module déjà existant mais dormant identifié dans le Current Domain Model comme la fondation la plus proche du modèle cible déjà écrite.

---

## 6. Invariants

- Une donnée absente reste absente ; elle n'est jamais convertie en zéro, en hypothèse implicite, ou en valeur par défaut présentée comme observée.
- Un fait dont la provenance n'est pas suffisamment ancrée ne peut jamais contribuer à un total présenté comme certifié — il peut être conservé, mais toujours marqué comme non ancré.
- Une preuve reconstruite après coup (par exemple depuis un texte narratif déjà généré) n'est jamais traitée avec le même niveau de confiance qu'une preuve directement ancrée à sa source ; elle est explicitement distinguée et ne contribue jamais à un total certifié.
- Une Evidence Ledger est immuable une fois sa période close. Toute correction ultérieure crée un nouvel enregistrement explicitement relié au précédent — jamais une réécriture silencieuse.
- Le niveau de confiance attribué à un fait ne peut jamais dépasser ce que sa provenance permet réellement d'affirmer.
- Un regroupement de faits en un même événement économique sous-jacent est identifié de façon déterministe et reproductible, jamais attribué arbitrairement ni laissé à la seule appréciation d'une intelligence artificielle.
- Chaque Evidence appartient à un seul Evidence Ledger faisant autorité ; elle n'est jamais dupliquée dans un second registre qui prétendrait représenter la même vérité.
- Deux Evidence ne peuvent jamais représenter contradictoirement le même fait pour une même période et une même provenance. *(Ajouté par ADR-001A — Evidence Ownership.)*

---

## 7. Impacts

| Objet | Décision | Justification |
|---|---|---|
| **ExecutiveDecisionModel** | **KEEP** *(dans le périmètre de cette ADR)* | Le Blueprint place le recâblage de cet objet en phase T5, délibérément après la stabilisation de l'Evidence Ledger. ADR-001 ne le touche pas : aucune de ses sources, aucun de ses champs, aucun de ses consommateurs ne change. |
| **DecisionArc** | **KEEP** | Continue de référencer les analyses exactement comme aujourd'hui. Sa fusion avec le reste de la mémoire décisionnelle est une décision de la phase T3, hors périmètre de cette ADR. |
| **FinancialTruth** *(module de typage existant)* | **ADAPT** | Passe du statut de type non branché à celui de fondation active de l'Evidence Ledger. C'est l'objet le plus directement concerné par cette décision. |
| **Analysis** *(résultat d'analyse persisté)* | **KEEP** | Continue d'exister et de fonctionner exactement comme aujourd'hui. Devient, en plus de son rôle actuel, l'une des sources qui alimentent l'Evidence Ledger — sans être elle-même modifiée. |
| **Exports** *(PDF, PPTX, Excel)* | **KEEP strict** | Zéro changement, zéro nouvelle dépendance introduite. Voir section 8. |
| **Memory** | **KEEP** | Aucun changement de comportement dans le périmètre de cette ADR. Deviendra, à partir de la phase T4, un consommateur naturel de l'Evidence Ledger — non anticipé ici. |

Aucun objet n'est, dans le périmètre de cette ADR, SPLIT, MERGE ou DELETE. C'est un choix délibéré : ADR-001 construit une fondation sans encore rien démanteler.

---

## 8. Compatibilité

La garantie de non-régression repose sur un principe simple : **dans le périmètre de cette ADR, l'Evidence Ledger est uniquement écrite, jamais lue, par un chemin de production existant.** L'inventaire de faits déjà produit à chaque analyse continue d'alimenter exactement ce qu'il alimente aujourd'hui (le résultat d'analyse et le récit qui en est dérivé) ; il alimente désormais, en plus et en parallèle, l'Evidence Ledger — sans que ce second flux n'interfère avec le premier.

Aucun export, aucun objet de restitution, aucune règle de calcul existante ne référence l'Evidence Ledger à l'issue de cette ADR. La compatibilité ascendante n'est donc pas seulement probable : elle est structurelle, puisque rien de ce qui produit aujourd'hui un export ne dépend de ce qui est introduit ici.

---

## 9. Migration — stratégie retenue

**Stratégie du strangler fig, limitée dans cette ADR à sa phase de croissance parallèle.**

Le strangler fig comporte, par nature, deux mouvements distincts : faire croître la nouvelle implémentation à côté de l'ancienne, puis, seulement une fois la nouvelle validée indépendamment, y rediriger progressivement les consommateurs existants. ADR-001 couvre exclusivement le premier mouvement. Aucun consommateur n'est redirigé vers l'Evidence Ledger dans cette décision — cela fera l'objet d'une ADR distincte, avec ses propres garanties de compatibilité, une fois l'Evidence Ledger éprouvée en production.

Cette stratégie est retenue parce qu'elle est la seule cohérente avec le principe constitutionnel selon lequel le domaine n'évolue pas par préférence mais par nécessité démontrée (Article IX), et avec l'exigence du Blueprint selon laquelle chaque étape doit laisser un produit strictement fonctionnel. Une bascule immédiate des consommateurs aurait exposé le produit à un risque non nécessaire à ce stade.

---

## 10. Tests d'acceptation

ADR-001 est considérée comme correctement implémentée si :

1. Chaque nouvelle analyse produit un Evidence Ledger non vide dès lors que l'inventaire de faits sourcés a lui-même produit au moins un fait.
2. Aucun Evidence Ledger ne contient de valeur zéro substituée à une absence de donnée constatée.
3. Chaque Evidence porte une provenance explicite, ou est explicitement marquée comme non ancrée — jamais l'un sans que l'autre soit visible.
4. Un Evidence Ledger dont la période est close ne peut être modifié par une écriture directe ; seule la création d'un nouvel enregistrement relié est possible.
5. Les trois exports (PDF, PPTX, Excel) produisent, avant et après l'activation de cette ADR, une sortie strictement identique sur un corpus de non-régression donné.
6. La suite de tests existante ne régresse pas : le nombre d'échecs déjà connus n'augmente pas du fait de cette décision.

---

## 11. Rollback

Le rollback est trivial par construction, puisque la décision est strictement additive et non lue par aucun chemin de production existant. Il consiste à cesser le seul point d'écriture ajouté par cette ADR. Aucune donnée existante — résultat d'analyse, exports, mémoire, retours de recommandation, arcs décisionnels — n'est modifiée par cette ADR ; aucune de ces données n'a donc besoin d'être restaurée en cas d'abandon. Le contenu déjà écrit dans l'Evidence Ledger peut être conservé sans risque ou ignoré sans impact, puisque rien d'autre n'en dépend encore à ce stade.

---

## 12. Constitution

| Article | Respect assuré par ADR-001 |
|---|---|
| **III — La Vérité** | Décision qui met directement en œuvre cet article : chaque fait devient traçable de façon persistante, et non plus seulement pendant la durée d'un appel. L'absence de donnée reste absente par invariant explicite (section 6). |
| **IV — Le Modèle Métier** | Introduit formellement « le fait » comme objet permanent du domaine, conformément à sa définition. |
| **V — La Mémoire** | Prépare la fondation factuelle sur laquelle la mémoire des conséquences pourra s'appuyer dans une phase ultérieure ; ne modifie pas la mémoire existante dans le périmètre de cette ADR. |
| **IX — L'Évolution** | La décision est prise par nécessité démontrée (dette documentée dans le Blueprint), non par préférence — conforme à l'exigence de motivation explicite. |
| **X — Les Interdictions** | Respecte en particulier l'interdiction de laisser coexister deux représentations prétendant chacune être la vérité : l'Evidence Ledger absorbe ce que la couche de preuve produit déjà, elle ne le duplique pas conceptuellement, et aucun autre objet n'est autorisé à prétendre représenter la même vérité tant que la migration des lecteurs n'a pas eu lieu. |
| **XII — Principes d'architecture** | « La preuve précède toujours la recommandation » : ADR-001 construit précisément la brique qui doit exister avant toute recommandation à boucle fermée. « La simplicité du domaine prévaut sur la sophistication de l'implémentation » : respecté en réutilisant le modèle déjà écrit plutôt qu'en le réinventant (Alternative B rejetée pour cette raison). |

---

## 13. Questions ouvertes

- ~~En l'absence, à ce stade, d'un Engagement formellement introduit (phase T2 non encore réalisée), à quoi l'Evidence Ledger doit-elle être rattachée de façon transitoire, et selon quelle règle sera-t-elle réattribuée une fois l'Engagement disponible ?~~ **CLOSE par ADR-001A — Evidence Ownership : la propriété conceptuelle est l'Engagement ; rattachement transitoire à l'Entity jusqu'à T2, avec réattribution obligatoire.**
- Quel événement marque, en l'absence d'une Cadence contractuelle formalisée, la clôture d'une période et donc le passage d'un Evidence Ledger à l'état immuable ?
- L'inventaire de faits produit aujourd'hui à chaque analyse est-il suffisamment complet pour renseigner tous les attributs du modèle de typage retenu, ou certains resteront-ils structurellement vides tant que ce qui produit cet inventaire n'évolue pas lui-même — question à trancher avant toute implémentation, mais hors du périmètre de décision d'architecture de cette ADR ?
- Une politique de conservation ou de purge de l'Evidence Ledger est-elle nécessaire, ou la conservation indéfinie est-elle la position par défaut ?
- Quelle instance décide du moment où une ADR ultérieure peut commencer à rediriger un premier consommateur vers l'Evidence Ledger ?

---

**ADR-001 READY FOR IMPLEMENTATION
AUCUN CODE MODIFIÉ.**
