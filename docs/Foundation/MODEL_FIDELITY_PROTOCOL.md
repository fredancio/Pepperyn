# PEPPERYN MODEL FIDELITY PROTOCOL v1.0

**Statut :** Proposé — protocole permanent, compagnon de PEPPERYN_PROFESSION_MODEL.md
**Nature :** méthode de validation, pas un modèle. Ce document ne modifie aucune responsabilité du Profession Model — il définit comment n'importe laquelle d'entre elles pourrait, un jour, être confirmée, corrigée ou retirée.
**Portée temporelle :** conçu pour s'exécuter sur des années, par vagues successives, jamais comme un exercice ponctuel.

---

## §0 — Posture épistémique : ce qui rendrait ce modèle faux

Un modèle qui ne peut pas être contredit n'est pas un modèle, c'est une croyance. Avant toute méthode, il faut donc nommer ce qui, concrètement, prouverait le Profession Model erroné — sans quoi la validation qui suit ne serait qu'un rituel de confirmation.

Le modèle serait falsifié, en tout ou partie, si l'une de ces observations se répétait, indépendamment, sur plusieurs profils :

- Deux des douze responsabilités s'avèrent, dans le vécu réel des CFO interrogés, indistinguables l'une de l'autre (même déclencheur, même comportement, aucune situation où l'une existe sans l'autre) — cela signifierait qu'elles doivent fusionner.
- Une responsabilité listée ne trouve, sur plusieurs vagues successives et plusieurs profils, aucune situation réelle qui l'illustre — cela signifierait qu'elle doit être retirée, quelle que soit la qualité de l'argument théorique qui l'avait justifiée.
- La répartition humain/logiciel/collaboration proposée pour une responsabilité est contredite par le comportement réel des utilisateurs (ils font systématiquement confiance à Pepperyn là où le modèle prédisait qu'un humain resterait nécessaire, ou l'inverse).
- Une capacité explicitement exclue par le Profession Model (Chapitre 8 — décider, négocier, représenter) s'avère être ce que les utilisateurs réels demandent et valorisent le plus.

Ces quatre scénarios sont les hypothèses nulles que ce protocole cherche activement à provoquer, pas seulement à tolérer.

---

## §1 — Critères d'acceptation d'une nouvelle responsabilité

Une treizième responsabilité (ou toute modification substantielle des douze existantes) ne peut entrer dans PEPPERYN_PROFESSION_MODEL.md qu'après avoir franchi quatre portes, dans l'ordre — aucune ne peut être sautée par conviction, même forte :

1. **Irréductibilité.** La responsabilité candidate ne doit pas être une reformulation ou un cas particulier de l'une des douze existantes. Test : peut-on la décrire sans jamais utiliser un mot déjà employé pour décrire une responsabilité existante, et sans que sa description en implique automatiquement une autre ? Si non, elle est absorbée, pas ajoutée.
2. **Formulation en invariant, pas en tâche.** Elle doit survivre à la question « est-ce une façon de faire, ou une nécessité du rôle ? » (voir §2, test de nécessité).
3. **Franchissement des cinq tests d'universalité** (§2) — sans exception favorable accordée par intuition.
4. **Niveau de preuve minimal atteint** — voir la hiérarchie ci-dessous, reprise directement de la discipline déjà établie pour l'Evidence Ledger (jamais une seule source, jamais une confiance supérieure à ce que la preuve permet) :

| Palier | Condition | Statut dans le Model Gap Register |
|---|---|---|
| Hypothèse | Observée chez un seul profil, une seule fois | Ouverte, non actionnable |
| Corroborée | Observée indépendamment chez au moins deux profils différents (§3) | Suivie, toujours hors du modèle canonique |
| Validée | Observée chez au moins trois profils sur les quatre-cinq catégories (§3), sans contradiction non expliquée d'un autre profil | Éligible à intégration |
| Intégrée | Ajoutée à PEPPERYN_PROFESSION_MODEL.md, avec numéro de version, date, et renvoi vers les entrées du Gap Register qui l'ont justifiée | Fermée, historisée |

Aucune responsabilité n'entre au palier « Intégrée » sans être passée, dans l'ordre, par les trois paliers précédents. Une conviction forte de l'équipe, même partagée, plafonne au palier « Hypothèse » tant qu'elle n'a pas rencontré de profils réels.

---

## §2 — Distinguer une responsabilité universelle d'une préférence individuelle

Cinq tests, appliqués systématiquement à chaque candidat — aucun test seul n'est suffisant, la conjonction des cinq l'est :

1. **Test d'invariance de personnalité.** La responsabilité apparaît-elle aussi bien chez un CFO méthodique que chez un CFO intuitif ? Si elle n'apparaît que chez un style de personnalité, c'est un style de travail, pas une responsabilité du métier.
2. **Test d'invariance de secteur et de taille.** Tient-elle chez un CFO de groupe multi-entités, une PME, un cabinet gérant un portefeuille ? Une responsabilité qui ne survit que dans un seul contexte sectoriel est une spécificité de contexte, pas un invariant (rappel du biais d'archétype déjà nommé dans le Profession Model, Chapitre 10).
3. **Test de nécessité contre habitude.** La question posée n'est jamais « faites-vous X ? » mais « si vous cessiez de faire X, que se passerait-il, et pour qui ? ». Une réponse de confort personnel (« je préfère procéder ainsi ») signale une préférence. Une réponse décrivant une conséquence réelle pour un tiers (une décision prise à tort, une confiance perdue, un risque manqué) signale une responsabilité.
4. **Test de reconnaissance négative.** On décrit au CFO interrogé un praticien hypothétique qui n'exerce jamais cette responsabilité, et on demande si ce praticien resterait, à ses yeux, compétent. Une hésitation ou un refus signale un invariant. Une acceptation sans trouble signale une option.
5. **Test de continuité historique.** Cette responsabilité existerait-elle si aucun des outils actuels (tableurs, ERP, tableaux de bord) n'existait ? Une responsabilité qui n'existe qu'à cause d'un outil ou d'une mode d'implémentation particulière est liée à l'exécution, pas au métier — c'est la même discipline que celle déjà imposée au Financial Time Engine (« jamais penser Excel »), appliquée cette fois au métier lui-même plutôt qu'à un composant.

Une responsabilité candidate qui échoue à deux tests ou plus reste au palier « Hypothèse » indéfiniment, quelle que soit la force de conviction de celui qui la propose.

---

## §3 — Méthode de validation auprès de profils différents

### 3.1 — Profils couverts, et une distinction à ne pas perdre

Cinq catégories, pas quatre — la nuance compte : CFO de groupe, CFO de PME, fractional CFO (portefeuille), cabinet comptable / expert-comptable. Cette dernière catégorie est délibérément distinguée du fractional CFO plutôt que fusionnée avec lui : un expert-comptable et un CFO externe partagent une partie de leurs responsabilités (garantir l'intégrité, contextualiser) mais pas toutes (le mandat de conseil et d'accompagnement diffère structurellement d'un mandat de production comptable). Confondre les deux profils produirait un modèle qui décrit correctement ni l'un ni l'autre — un risque déjà identifié en creux au Chapitre 4 du Profession Model, ici rendu explicite.

### 3.2 — Méthode d'entretien : ne jamais demander confirmation directe

Demander « êtes-vous d'accord avec cette responsabilité ? » produit un biais de désirabilité sociale quasi systématique — presque tout CFO interrogé confirmera n'importe quelle responsabilité qui sonne juste. La méthode retenue est donc l'élicitation par récit, pas la confirmation par questionnaire :

- On demande au CFO de raconter trois à cinq situations réelles et récentes (« racontez-moi la dernière fois où vous avez dû... »), sans jamais mentionner les douze responsabilités du modèle pendant l'entretien.
- Les récits sont ensuite codés, après coup, par au moins deux personnes travaillant indépendamment l'une de l'autre, pour vérifier à quelle(s) responsabilité(s) du modèle chaque situation correspond — ou si elle correspond à rien du tout (candidat pour le Gap Register).
- Le taux d'accord entre les deux codeurs est mesuré et conservé. Un désaccord fréquent sur un même type de récit est lui-même un signal à consigner (soit la responsabilité est mal définie, soit la situation est ambiguë et le restera).

### 3.3 — Seuil de validation

Une responsabilité (ou une correction à la cartographie humain/logiciel/collaboration) atteint le palier « Validée » lorsqu'elle est corroborée par au moins trois profils sur les cinq, **et** qu'aucun profil restant ne la contredit sans explication rattachable à une différence de contexte légitime (secteur, taille — voir test 2 du §2). Une contradiction inexpliquée d'un seul profil bloque la validation — elle ne se résout jamais par un vote majoritaire, elle ouvre une enquête.

### 3.4 — Cadence

Une vague structurée d'entretiens deux fois par an, avec un minimum de deux CFO par profil et par vague (dix entretiens minimum par vague). Entre deux vagues, tout signal informel rencontré au fil de l'activité normale (support, ventes, entretiens de départ client) alimente directement le Gap Register sans attendre la prochaine vague — mais ne peut jamais, à lui seul, faire franchir un palier de validation.

---

## §4 — Signaux de convergence et signaux de dérive

**Convergence — le modèle suit la réalité :**
- Les récits recueillis lors d'une nouvelle vague se rattachent de plus en plus facilement aux douze responsabilités existantes, sans qu'aucune nouvelle catégorie ne soit nécessaire pour les classer (saturation — le signal le plus fiable qu'un modèle qualitatif approche sa maturité).
- Le désaccord entre profils sur l'importance relative d'une responsabilité se réduit d'une vague à l'autre plutôt qu'il ne s'élargit.
- La répartition humain/logiciel/collaboration prédite pour une responsabilité se confirme dans le comportement réel des utilisateurs (ils commencent à faire confiance à Pepperyn précisément là où le modèle prédisait une supériorité logicielle, et continuent à solliciter un humain là où le modèle prédisait l'inverse).
- Une capacité écartée par le filtre du Chapitre 9 du Profession Model se révèle, a posteriori, effectivement peu demandée par les utilisateurs réels.

**Dérive — le modèle s'écarte de la réalité :**
- Le Gap Register accumule plusieurs entrées autour du même thème, rejetées ou reportées à chaque fois sans jamais être réellement tranchées — signe d'évitement, pas d'absence réelle de sujet.
- Une responsabilité validée lors d'une vague cesse d'être corroborée lors des vagues suivantes.
- Une équipe interne doit de plus en plus souvent « forcer » un besoin utilisateur réel dans une case existante du modèle plutôt que ce besoin ne s'y range naturellement — ce forçage doit être consigné comme un signal, pas silencieusement accepté.
- L'écart se creuse entre ce que le Profession Model interdit (Chapitre 8) et ce que les utilisateurs valorisent le plus dans les faits — le signal de dérive le plus grave, celui qui doit déclencher une révision du document fondateur lui-même plutôt qu'un simple ajustement du Gap Register.

---

## §5 — Model Gap Register

Registre permanent, jamais purgé — y compris les entrées rejetées, conservées avec leur raisonnement, exactement selon la même discipline d'append-only déjà appliquée à l'Evidence Ledger et à Decision Memory. C'est un backlog conceptuel : chaque entrée pose une question de fidélité au métier, jamais une demande de fonctionnalité.

**Champs de chaque entrée :**

| Champ | Contenu |
|---|---|
| Identifiant, date d'ouverture | — |
| Observation source | Le récit ou signal brut, jamais résumé au point de perdre la situation réelle |
| Profil source | Lequel des cinq profils, combien de sources indépendantes |
| Type | Candidat à une nouvelle responsabilité · correction d'une responsabilité existante · contradiction de la répartition humain/logiciel/collaboration · contradiction du Chapitre 8 · bruit (échoue aux tests du §2) |
| Tests franchis | Lesquels des cinq tests d'universalité (§2) sont passés, lesquels échouent |
| Palier de preuve atteint | Hypothèse · Corroborée · Validée · Intégrée · Rejetée · En pause |
| Responsabilité(s) du modèle concernée(s) | Renvoi explicite au chapitre du Profession Model |
| Décision et raisonnement | Toujours écrit, y compris pour un rejet — jamais une case cochée sans justification |

**Gouvernance :** le registre est revu à chaque vague d'entretiens (§3.4), pas en continu — pour éviter qu'il devienne un flux d'anxiété permanent plutôt qu'un instrument de discipline. Propriété du registre : la direction produit, jamais l'ingénierie seule — cohérent avec le fait que ce registre statue sur la fidélité au métier, pas sur la faisabilité technique.

---

## §6 — Trois niveaux de validation, jamais interchangeables

Le protocole distingue formellement trois questions, parce que les confondre a déjà produit, ailleurs dans ce projet, des erreurs de modélisation coûteuses à corriger (cinq représentations concurrentes du même « résultat d'analyse », documentées dans le Current Domain Model). Aucun des trois niveaux ne remplace les deux autres — une responsabilité peut très bien réussir A et B et échouer C, et c'est une découverte légitime, pas une anomalie à corriger en forçant le résultat.

**A — Profession Validity.** *La responsabilité correspond-elle réellement au métier d'un excellent CFO ?* Preuve : récits qualitatifs codés (méthode §3). Profils : les cinq catégories de CFO/cabinets. Critère de réussite : palier « Validée » (§1/§3.3). Limite : mesure la reconnaissance du métier, jamais si Pepperyn la traduit bien ni si cela améliore quoi que ce soit — une responsabilité peut être parfaitement valide au sens professionnel et rester mal ou jamais implémentée.

**B — Product Validity.** *Pepperyn traduit-il correctement cette responsabilité dans son fonctionnement, et les utilisateurs s'en servent-ils comme prévu ?* Preuve : usage réel observé (adoption, fréquence, complétude du parcours), comparé au comportement attendu défini pour cette responsabilité. Profils : utilisateurs réels de Pepperyn, pas nécessairement les mêmes personnes que celles interrogées pour A. Critère de réussite : le comportement attendu est effectivement observé dans l'usage réel, pas seulement disponible dans le produit. Limite : un usage élevé ne prouve pas un impact réel (une fonctionnalité peut être utilisée par habitude sans rien améliorer) ; un usage faible ne réfute pas non plus la validité professionnelle (l'implémentation peut être maladroite alors que la responsabilité est réelle) — ce niveau ne se lit jamais seul.

**C — Outcome Validity.** *Cette traduction améliore-t-elle réellement une décision, une préparation, un suivi ou un résultat observable ?* Définie en détail au §7. Preuve : proxys prudents observés dans le temps, jamais une démonstration de causalité formelle. Profils : la relation réelle suivie (l'Engagement), pas un échantillon d'entretiens. Critère de réussite : un proxy fort se déplace dans la bonne direction sur plusieurs Engagements et plusieurs périodes, sans contre-exemple non expliqué. Limite : corrélation, jamais causalité prouvée — le niveau le plus fragile des trois, et le plus sujet à sur-interprétation.

---

## §7 — Outcome Validation : la validation par les résultats réels

### 7.1 — Ce que ce niveau ajoute, et ce qu'il ne promet pas

Les niveaux A et B (§6) peuvent tous deux réussir sans qu'aucune amélioration réelle n'en résulte — une responsabilité peut être fidèlement reconnue par le métier et fidèlement traduite dans le produit, et pourtant ne rien changer à la qualité des décisions prises. L'Outcome Validation répond à cette question restante : *la capacité issue du Profession Model améliore-t-elle réellement la qualité de la décision, du suivi ou de l'exécution ?* Elle ne promet jamais de démontrer une causalité parfaite — elle définit des proxys observables et prudents, jamais présentés comme une preuve formelle.

### 7.2 — Proxys, challengés plutôt que repris mécaniquement

**Proxys forts — directement observables via des mécanismes déjà conçus ou déjà en code réel, à privilégier :**
- Réduction du nombre de recommandations sans suivi (observable via la distribution des statuts de `DecisionArc` — abandonné vs clos avec apprentissage).
- Augmentation de la part de décisions reliées à une preuve traçable (observable via le taux de liaison Recommendation → Evidence Ledger).
- Réduction des décisions prises sur des données périmées (observable via `DataFreshness`/`TemporalWarning`, Financial Time Engine — un mécanisme conçu précisément pour produire ce signal).
- Réduction du nombre de sujets sans propriétaire clair.
- Meilleure capacité à expliquer pourquoi une décision a été prise (observable via la complétude de Decision Memory à la relecture).

**Proxys faibles ou à manier avec une prudence explicite — retenus, mais jamais comme signal primaire :**
- *Réduction du temps de préparation d'une revue* — tentant, mais un temps gagné se confond aisément avec l'expérience croissante de l'utilisateur plutôt qu'avec l'apport de Pepperyn ; ne jamais l'utiliser comme preuve isolée.
- *Meilleure détection des anomalies* — tel que formulé, ce proxy est circulaire (c'est Pepperyn qui détecte, donc compter ses propres détections ne prouve rien) ; reformulé, le proxy utile est la **précocité** de la détection avant qu'une mauvaise décision ne soit prise, pas le volume détecté.
- *Moins de contradictions entre analyses* — un proxy légitime en théorie, mais qui exige un mécanisme de détection de contradiction qui n'existe pas encore ; consigné comme aspirationnel, pas actionnable aujourd'hui.
- *Amélioration de la continuité entre deux revues* — réel mais largement qualitatif ; difficile à observer sans jugement humain, donc à traiter comme signal secondaire plutôt que métrique.

### 7.3 — Trois validations, jamais confondues

Il faut nommer explicitement ce que chacune mesure, pour ne jamais les substituer l'une à l'autre : la **validation du modèle professionnel** (A) répond à « cela existe-t-il vraiment dans le métier ? » ; la **validation de l'usage** (B) répond à « Pepperyn le traduit-il et les gens s'en servent-ils ? » ; la **validation de l'impact** (C, cette section) répond à « cela change-t-il quelque chose de mesurable pour de bon ? ». Une capacité peut franchir les deux premières et échouer la troisième — c'est une découverte légitime du protocole, pas un échec du protocole lui-même.

---

## §8 — La boucle complète d'apprentissage

```
Métier réel
↓
Profession Model
↓
Architecture du domaine
↓
Produit
↓
Décisions et comportements
↓
Résultats observés
↓
Retour d'expérience
↓
Révision du Profession Model
```

Le point décisif de cette boucle est qu'elle revient au Profession Model, jamais seulement au backlog produit ou au code — un résultat observé qui contredit le modèle doit pouvoir remettre en cause le modèle lui-même, pas seulement son implémentation.

**Signaux déclencheurs d'une révision** : une entrée du Model Gap Register atteignant le palier « Validée » contre une responsabilité *existante* (correction, pas seulement candidat nouveau) ; un signal de dérive (§4) confirmé sur deux vagues consécutives ; un motif répété dans PROFESSION_MODEL_EVIDENCE_LOG.md (§9) montrant qu'une capacité échoue systématiquement l'Outcome Validity malgré un succès en A et B ; une contradiction rencontrée en développement que le modèle actuel ne permet pas de résoudre.

**Qui peut proposer une révision** : n'importe qui peut *ouvrir* une entrée dans le Gap Register ou le Registre d'impact — un membre de l'équipe, Fred, un futur collaborateur. Seule la direction produit peut *promouvoir* une entrée jusqu'à une révision effective du document — la même séparation de gouvernance déjà posée au §5.

**Niveau de preuve requis** : asymétrique, et volontairement. Ajouter une responsabilité exige le palier complet « Validée » du §1/§3.3 (irréductibilité, cinq tests, trois profils sur cinq sans contradiction). Retirer une responsabilité déjà intégrée exige ce même palier **plus** une conclusion d'Outcome Validity négative répétée (§7, §10) **plus** l'accord explicite de la direction produit — jamais une suppression silencieuse, toujours historisée avec sa date et son raisonnement. Raffiner une responsabilité déjà validée (par exemple ajuster sa répartition humain/logiciel/collaboration) demande un seuil plus léger : deux entrées corroborantes du Registre d'impact pointant dans le même sens suffisent, parce qu'il s'agit d'affiner un fait déjà établi, pas d'en introduire un nouveau.

**Comment éviter qu'un résultat isolé entraîne une réécriture prématurée** : le même système de paliers qui permet la révision la freine aussi. Une seule observation, même frappante, ne peut jamais dépasser le palier « Hypothèse » dans le Registre d'impact. Elle doit être corroborée par au moins une deuxième observation indépendante avant même d'être éligible à discussion — et une réécriture complète (par opposition à un simple raffinement) exige toujours de repasser par la méthode d'entretien multi-profils du §3, jamais par les seules données d'impact. Les données d'impact proposent ; la méthode d'entretien dispose.

---

## §9 — Registre d'impact : PROFESSION_MODEL_EVIDENCE_LOG.md

**Décision : un registre séparé du Model Gap Register, pas une extension.**

Justification par la simplicité et l'usage réel, comme demandé : le Gap Register et ce nouveau registre répondent à deux questions de nature différente (la fidélité du modèle au métier, contre l'efficacité réelle d'une capacité déjà construite), sont alimentés par des sources différentes (récits d'entretiens codés, contre observation continue de l'usage et des résultats), et suivent des rythmes différents (deux vagues par an, contre un flux continu au fil de l'activité). Fusionner les deux forcerait un même champ « Palier de preuve » à porter deux significations différentes selon le type d'entrée — exactement l'ambiguïté que la distinction A/B/C (§6) et la distinction modèle/usage/impact (§7.3) demandent d'éviter. Un registre séparé, mais délibérément minimal, tient les deux exigences ensemble sans jamais devenir un entrepôt de métriques.

**Champs de chaque entrée — rien de plus :**

| Champ | Contenu |
|---|---|
| Responsabilité concernée | Renvoi au Chapitre 2 du Profession Model |
| Capacité produit correspondante | Le composant réel, pas une idée |
| Comportement attendu | Ce que la capacité était censée changer |
| Observation réelle | Le fait constaté, jamais résumé au point de perdre le contexte |
| Résultat | Positif · négatif · ambigu — jamais forcé vers une case propre s'il ne l'est pas |
| Niveau de confiance | Hypothèse · Corroborée · Validée (même échelle que le Gap Register, pour rester lisible d'un registre à l'autre) |
| Contre-exemples | Tenus à jour à côté de l'observation, jamais dans une entrée séparée qui s'oublie |
| Décision prise sur le modèle | Aucune action · raffinement proposé · escaladé vers révision — toujours écrit |

Ce registre n'est jamais un tableau de bord de métriques produit — il ne contient aucune donnée qui n'ait un lien direct et nommé avec une responsabilité du Profession Model.

---

## §10 — Le test de valeur finale

Pour chaque responsabilité modélisée, une question de clôture, à poser périodiquement et jamais isolément : *si cette capacité disparaissait demain, quelle dégradation concrète observerait le CFO, le dirigeant ou l'organisation ?*

Si aucune dégradation claire n'est identifiable, trois lectures sont possibles, à distinguer soigneusement plutôt qu'à traiter comme un verdict unique : la capacité peut être accessoire (utile mais non essentielle — pas nécessairement à retirer) ; le lien entre la capacité et la responsabilité qu'elle prétend servir peut être faible (l'implémentation a dérivé de l'intention) ; ou la responsabilité elle-même peut être mal formulée (le vrai problème remonte au Profession Model, pas au produit). Ce test ne se suffit jamais à lui-même — il sert de dernier filtre, après A, B et C, jamais de premier verdict.

---

## §11 — Frontière humaine, réaffirmée à la lumière de la validation par les résultats

Pepperyn ne devient jamais « meilleur » simplement parce qu'il reproduit davantage d'actes d'un CFO. Il ne prend en charge que ce qui respecte la Constitution, peut être modélisé avec rigueur, peut être amplifié sans créer une responsabilité illégitime, et conserve une frontière claire avec le jugement humain (Chapitre 8 du Profession Model).

La validation par les résultats, aussi convaincante soit-elle, ne justifie jamais : une décision automatique non autorisée par la Constitution ; une causalité inventée au-delà de ce qu'un proxy honnête peut soutenir ; un transfert implicite de responsabilité de l'humain vers Pepperyn (le risque le plus insidieux — de bons résultats répétés créent une tentation réelle de laisser Pepperyn décider « puisque ça marche ») ; une optimisation d'un proxy au détriment de l'intégrité (par exemple, encourager des recommandations plus rapides mais moins vérifiées pour améliorer artificiellement un temps de préparation — un risque directement lié au proxy faible déjà signalé au §7.2).

---

## §12 — Version minimale viable du protocole

Un protocole aussi complet que celui-ci, exécuté avec une rigueur imparfaite ou abandonné après une seule vague, est pire que l'absence de protocole : il donne une fausse impression de validation. Si les ressources ne permettent pas la cadence complète du §3.4, la version minimale suivante doit être maintenue sans exception plutôt que le protocole entier abandonné :

- Au moins quatre entretiens par an (un par profil, cabinet comptable inclus), avec la méthode de récit du §3.2 — jamais remplacés par un questionnaire de confirmation, même en version réduite.
- Le Gap Register tenu à jour en continu, même sans vague formelle — chaque signal informel consigné dans la semaine, jamais différé indéfiniment.
- Une revue annuelle minimale du Profession Model à la lumière du registre, même si aucune promotion au palier « Intégrée » n'a lieu cette année-là.
- PROFESSION_MODEL_EVIDENCE_LOG.md (§9) tenu à jour dès qu'un résultat notable — positif, négatif ou ambigu — est observé sur une capacité liée au Profession Model, sans attendre de cadence formelle. C'est le point le plus facile à laisser filer en pratique ; c'est aussi celui dont l'absence rendrait le niveau C (Outcome Validity) purement théorique.

---

## §13 — Auto-critique

**Taille d'échantillon.** Dix entretiens par vague, cinq profils, est un minimum méthodologiquement défendable pour détecter un signal fort, mais reste trop faible pour trancher des désaccords fins entre profils proches (CFO de PME vs fractional CFO, par exemple, qui se recoupent souvent). Ce protocole ne prétend pas atteindre une rigueur statistique — il prétend seulement rendre le modèle contestable par des faits plutôt que par des intuitions, ce qui est un objectif plus modeste et plus honnête.

**Biais de sélection des CFO interrogés.** Rien dans ce protocole ne garantit que les CFO accessibles à l'équipe (réseau, clients existants) représentent la diversité réelle du métier — le risque de biais d'archétype nommé dans le Profession Model n'est pas résolu par ce protocole, seulement rendu visible et mesurable dans le temps.

**Risque d'abandon.** Le risque le plus concret n'est pas méthodologique, il est organisationnel : ce protocole demande un effort régulier et non commercialement immédiat, en concurrence directe avec le développement produit. Le §12 existe précisément pour cette raison, mais aucun document ne peut garantir qu'il sera exécuté — seule une décision de gouvernance explicite, réaffirmée à chaque vague manquée, peut le protéger.

**Ce protocole valide-t-il vraiment le modèle, ou seulement sa perception ?** Une limite reconnue sans solution ici : ce protocole mesure ce que les CFO interrogés disent et racontent, pas nécessairement ce qu'un observateur extérieur verrait s'il suivait leur travail en continu. L'écart entre récit et pratique réelle n'est pas fermé par ce protocole — seule une observation directe et prolongée le pourrait, hors de portée d'un protocole d'entretiens.

---

**PEPPERYN MODEL FIDELITY PROTOCOL v1.0 READY FOR REVIEW. AUCUN CODE, AUCUNE FONCTIONNALITÉ N'EST DÉCIDÉE PAR CE DOCUMENT.**
