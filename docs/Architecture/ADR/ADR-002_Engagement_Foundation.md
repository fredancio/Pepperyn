# ADR-002 — Engagement Foundation

**Phase :** T2 du Transformation Blueprint
**Statut :** **ACCEPTED** (2026-08-02) — **cardinalité Entity:Engagement amendée le 2026-08-07, voir §0**
**Sources autorisées :** Pepperyn Constitution v1.0 · Current Domain Model · Ideal Domain Model · Transformation Blueprint (§B ligne 2, §C.1, **§E Phase T2**) · ADR-001 (Evidence Foundation) · ADR-001A (Evidence Ownership)
**Nature :** décision d'architecture unique et ciblée. Aucune implémentation, aucune migration, aucune modification de code, aucun changement Supabase n'est exécuté par ce document.

**Historique des révisions :**

| Révision | Date | Motif |
|---|---|---|
| v1 | 2026-08-02 | Version initiale, soumise à revue. |
| v2 | 2026-08-02 | Amendée suite à revue (REQUEST CHANGES) sur trois points : (1) relation Entity:Engagement fixée explicitement à 1:1, durable et permanente, avec règle de reprise après `churned` (§3.3, §3.5, §3.14) ; (2) statut initial du backfill dérivé d'un signal réel (existence d'une Analysis) plutôt que d'une hypothèse `active` par défaut (§3.5, §3.10) ; (3) `company_id` retiré de l'agrégat `Engagement`, résolu par jointure vers `Entity` plutôt que dénormalisé (§3.2, §3.3, §3.10, §3.12). Aucune section validée par ailleurs n'a été rouverte. |
| v2 — **ACCEPTED** | 2026-08-02 | Statut passé à ACCEPTED. Quatre notes de revue complémentaires, non normatives pour l'ADR (elles ne modifient aucune décision déjà prise ci-dessus) et intégrées directement dans `docs/Architecture/blueprint/T2A_Implementation_Plan.md` : (1) le statut du backfill est une initialisation déterministe, pas une vérité commerciale certifiée ; (2) le backfill doit être strictement idempotent (créer seulement les Engagements absents, ne jamais dupliquer, ne jamais modifier ni recalculer un Engagement existant) ; (3) tous les chemins réels de création d'Entity doivent être couverts, pas seulement un endpoint supposé principal ; (4) vérifier si `ScopeDefinition` apporte une information au-delà de `entity_id` en T2 avant de construire quoi que ce soit — ne pas dupliquer la vérité. |
| v3 — **cardinalité amendée** | 2026-08-07 | Suite à l'implémentation réelle de T2A et à une revue adversariale pré-fusion, la question de la cardinalité Entity:Engagement a été rouverte à dessein et arbitrée depuis le métier plutôt que depuis le code existant (voir §0). Le statut ACCEPTED de cette ADR n'est pas remis en cause ; seule l'affirmation de permanence de §3.3/§3.14 Alternative 4 est corrigée. Aucune autre section n'est rouverte. |

---

## 0. Amendement canonique — cardinalité Entity:Engagement (2026-08-07)

**Ceci est la position canonique actuelle. Elle prévaut sur toute affirmation de permanence trouvée plus bas dans ce document (§3.3, §3.5, §3.12, §3.14 Alternative 4), qui reste conservée telle quelle pour sa valeur historique mais qui n'est plus autoritaire sur ce point précis.**

**Ce qui a changé :** l'implémentation de T2A a rendu concrète une question que la version v2 avait tranchée trop tôt et pour de mauvaises raisons. Une revue adversariale pré-fusion, puis une arbitration dédiée partant du métier plutôt que du code, ont établi que §3.14 Alternative 4 avait fusionné deux problèmes distincts : un problème de **modèle du domaine** (plusieurs Engagements peuvent-ils légitimement exister pour une même Entity ?) et un problème de **migration de données historiques** (peut-on répartir rétroactivement les faits déjà enregistrés entre plusieurs Engagements ?). Seul le second justifiait une contrainte technique — le premier a été tranché par erreur en même temps que le second.

**Position canonique actuelle, remplaçant §3.3/§3.14 Alternative 4 sur ce point uniquement :**

- Une Organisation (aujourd'hui portée par `Entity`) **peut avoir plusieurs Engagements au cours de sa vie**. La permanence 1:1 affirmée en v2 n'est plus tenue pour vraie.
- L'identité d'un Engagement suit la continuité du **mandat professionnel**, pas la durée de vie de l'Organisation. Un changement de périmètre à l'intérieur d'un mandat continu (`ScopeDefinition`) ne crée pas un nouvel Engagement ; un mandat qui se termine puis qu'un mandat réellement nouveau commence, même sans interruption, en crée un.
- `paused` signifie que la relation existe toujours mais est suspendue. `churned` signifie que l'Engagement s'est réellement terminé — pas qu'il est en sommeil.
- Un mandat réellement nouveau **peut** créer un nouvel Engagement pour une Entity qui en a déjà eu un.
- La connaissance organisationnelle historique doit rester accessible à travers les Engagements successifs d'une même Entity — un nouvel Engagement ne doit jamais signifier une mémoire effacée.
- La contrainte SQL `UNIQUE(entity_id)` sur `engagements` (migration v19) reste en place **aujourd'hui**, mais est reclassée : ce n'était pas un invariant de domaine correctement établi, c'est une **contrainte d'implémentation transitoire**, tolérée uniquement parce qu'aucun chemin de code réel ne crée aujourd'hui un second Engagement pour une Entity existante.
- Cette contrainte ne doit donc plus jamais être invoquée comme preuve d'un invariant métier dans une décision future. Le déclencheur de sa révision et la direction technique préférée sont enregistrés dans `docs/Audit/STRATEGIC_DEFERRED_WORK_REGISTER.md`.

**Ce que cet amendement n'autorise pas :** aucune implémentation de cardinalité multiple, aucune suppression de `UNIQUE(entity_id)`, aucun `previous_engagement_id`, aucune logique de réactivation ou de nouveau mandat. Ce sont des incréments futurs, déclenchés par un besoin réel démontré (Article IX), pas par cet amendement lui-même.

---

## 1. Contexte

T1 a construit l'Evidence Ledger sans pouvoir le rattacher à son propriétaire conceptuel définitif, faute pour ce propriétaire d'exister physiquement. ADR-001A a tranché la question par anticipation : « la propriété conceptuelle de l'Evidence Ledger est l'Engagement, dès aujourd'hui et de façon définitive [...] avec obligation de réattribution explicite au moment où l'Engagement existe » (ADR-001A §4). Le T1 Completion Report (§9) et la rétrospective T1 (§3) désignent tous deux ce point comme le point de reprise naturel de T2, et demandent explicitement que le plan de réattribution soit clarifié dès l'ADR d'ouverture — pas découvert en cours de route.

L'Engagement est par ailleurs déjà nommé comme objet permanent du domaine par la Constitution (Article IV) et détaillé comme agrégat racine par le Modèle Idéal (§E.1). Le Blueprint (§B ligne 2, §C.1, §E) a déjà tranché la stratégie de haut niveau : `Entity` **EVOLVE** vers `Engagement` par enveloppe additive, un Engagement par Entity existante, sans casser la hiérarchie actuelle.

Ce que T1 laisse en suspens et que T2 doit clore : **comment fait-on exister physiquement l'Engagement, sans rien casser de ce qui existe, et comment l'Evidence Ledger honore-t-il l'obligation de réattribution posée par ADR-001A ?**

---

## 2. Problème

Le domaine actuel s'organise en hiérarchie stricte `Company → Workspace → Entity`, toutes les clés étrangères étant `NOT NULL ON DELETE CASCADE` (`entities.workspace_id`, `entities.company_id`). `Entity` porte aujourd'hui un attribut `relation_type` (`filiale` | `client` | `NULL`) qui, selon le Current Domain Model (§M, dette n°4), « porte seul le poids conceptuel de "client externe suivi" » — réduit à une valeur d'enum optionnelle, sans durée, sans cadence, sans cycle de vie.

Trois objets consomment déjà `entity_id` sans passer par un objet de relation continue :
- `analyses.entity_id` (table pré-migrations, confirmée active dans `routers/analyze.py`) ;
- `evidence_ledger_entries.entity_id` (v18, **nullable**, `ON DELETE SET NULL`) — l'ancrage transitoire posé par ADR-001A ;
- `decision_arcs.entity_id` (v16, **nullable**, `ON DELETE SET NULL`) — même motif transitoire, jamais formalisé par une ADR jusqu'ici.

Deux objets ignorent complètement `Entity` et raisonnent uniquement au niveau `Company` : la Mémoire (`financial_metrics`, `company_profile`, v5) et le Billing (`usage_limits`, v2 — clé primaire composite `(company_id, year_month)`, aucune colonne `entity_id`).

Le problème n'est donc pas de choisir *si* l'Engagement doit exister — le Blueprint l'a déjà tranché — mais de définir précisément sa forme, ses relations, son cycle de vie, et surtout **comment il honore l'obligation de réattribution de l'Evidence Ledger sans violer l'invariant d'immutabilité que T1 vient d'établir** (le trigger PostgreSQL de `evidence_ledger_entries` bloque inconditionnellement tout `UPDATE`, y compris pour backfiller une colonne nouvellement ajoutée).

---

## 3. Décision

**L'Engagement devient un agrégat racine permanent du domaine, introduit par enveloppe additive autour de chaque Entity existante. La réattribution de l'Evidence Ledger promise par ADR-001A est honorée par résolution — jamais par réécriture des lignes déjà écrites.**

Le détail de chacun des dix-sept points suit.

---

### 3.1 Définition exacte d'un Engagement

Conformément à la Constitution (Article IV) : l'Engagement est **le lien continu entre le professionnel (l'utilisateur de Pepperyn agissant pour le compte d'une Company) et l'organisation dont il a la charge**. Il précède et dépasse chaque intervention ponctuelle ; il porte une durée, des obligations, un contexte et une mémoire propres ; il ne se réduit jamais à un seul examen isolé.

Concrètement pour T2 : l'Engagement est l'objet qui répond à la question *« qui, précisément, Pepperyn suit-il dans la durée ? »* — question à laquelle `Entity` ne répond aujourd'hui que par un attribut optionnel (`relation_type`), jamais par un objet à part entière.

### 3.2 Racine d'agrégat

`Engagement` est son propre agrégat racine (`EngagementId`), au sens du Modèle Idéal §E.1 — il n'est ni fusionné dans `Entity`, ni un simple attribut ajouté à la table `entities`. Cette séparation est un choix délibéré (voir §3.14, alternative rejetée n°3) : `Entity` reste un conteneur d'accès et de facturation (Current Domain Model : « jamais lu par la logique de génération du contenu décisionnel ») ; `Engagement` porte la relation métier elle-même, avec son propre cycle de vie et ses propres événements.

Attributs de l'agrégat pour T2 (strictement ceux nécessaires à l'enveloppe additive décrite par le Blueprint §C.1/§E — aucune anticipation de T3+) :
- `id` (`EngagementId`)
- `entity_id` (référence vers l'Entity enveloppée, `NOT NULL UNIQUE` — voir §3.3)
- `status` (`EngagementStatus` : prospect | active | paused | at_risk | churned — voir §3.5 pour la règle de backfill)
- `cadence` (`ReviewCadence` : mensuelle par défaut, prescrite par le Blueprint §E)
- `scope` (`ScopeDefinition` : l'entité elle-même, par défaut, prescrite par le Blueprint §E)
- `created_at`, `updated_at`

**Amendement (revue) — pas de `company_id` sur `Engagement`.** Aucun consommateur ne lit encore `engagements` en production (§3.10) et aucune nécessité de dénormalisation n'est démontrée aujourd'hui (Article IX) ; la stocker aurait exigé soit un invariant documenté mais non garanti techniquement, soit un mécanisme de validation dédié — les deux ajoutant une complexité non justifiée par un besoin actuel (Article XII, simplicité). `engagement.company_id` se résout, quand nécessaire, par une jointure unique et sans ambiguïté : `engagements.entity_id → entities.company_id`. Une seule colonne porte cette information dans tout le domaine — celle qui existe déjà sur `entities` ; aucune seconde source de vérité n'est créée.

### 3.3 Relation avec Company, Entity et Workspace

`Company` et `Workspace` ne sont pas modifiés — le Blueprint les classe **KEEP** (§B ligne 1). L'Engagement ne remplace ni n'absorbe la hiérarchie existante ; il s'y insère au niveau `Entity` :

- **[Amendé le 2026-08-07, voir §0 — la permanence affirmée ci-dessous n'est plus la position canonique.]** La relation Entity:Engagement est 1:1 *dans l'implémentation actuelle*. `entity_id` porte une contrainte `UNIQUE` sur `Engagement`, aujourd'hui non relâchée faute de besoin démontré — mais reclassée comme contrainte transitoire, pas comme invariant de domaine permanent (§0).
- `Workspace` n'est pas référencé directement par `Engagement` : la relation `Workspace → Entity` existante suffit à situer l'Engagement dans le bon Workspace par transitivité, sans dupliquer cette référence.
- `Engagement.company_id` n'existe pas comme colonne propre (§3.2) — la Company d'un Engagement se lit toujours via `entities.company_id`, jamais dupliquée.

**Reprise d'une relation après `churned`.** Une Entity ne disparaît jamais et n'est jamais recréée pour représenter la reprise d'une relation avec la même organisation réelle : recréer une Entity fragmenterait l'historique d'analyses d'une même entreprise entre deux lignes disjointes, ce qu'aucune source ne justifie et que rien ne permet de démontrer nécessaire. La reprise d'une relation réactive donc le même Engagement (transition `churned → active`), jamais un nouvel agrégat. Cette transition n'est pas explicitement dessinée dans le diagramme de cycle de vie du Modèle Idéal (§E.1), mais ne le contredit pas non plus : elle en est la lecture la plus fidèle, au sens de l'Article IV de la Constitution, qui définit l'Engagement comme « le lien continu [...] qui précède et dépasse chaque intervention ponctuelle » — porter la continuité de la relation, y compris après une interruption, est précisément ce pour quoi l'Engagement existe. T2 ne construit aucun mécanisme pour déclencher cette transition (aucune interface, aucun trigger — cohérent avec la « fondation invisible » du Blueprint §E) ; ce paragraphe fixe uniquement la règle de modélisation, pour qu'une future PR ne réintroduise pas par erreur une relation 1:N.

**Conséquence pour la résolution historique.** Parce que la relation reste 1:1 pour toute la durée de vie d'une Entity, la jointure `entity_id → engagements.entity_id` (§3.4, §3.8) reste déterministe et sans ambiguïté pour toujours — y compris pour les Evidence et Analyses passées d'une Entity ayant traversé plusieurs cycles `active ↔ paused ↔ churned`. Aucune Evidence ni Analysis, historique ou future, ne peut jamais avoir plus d'un Engagement candidat pour une même Entity. C'est cette garantie de permanence, et non la seule commodité du schéma, qui justifie de fixer 1:1 comme règle durable plutôt que comme simplification de départ (voir §3.14, alternative 4, pour la comparaison avec une succession d'Engagements).

### 3.4 Propriété sur l'Evidence Ledger

C'est le point que la rétrospective T1 demandait de clarifier dès l'ouverture de T2. Décision : **la propriété conceptuelle de l'Evidence Ledger devient effectivement résolvable via l'Engagement, sans qu'aucune ligne déjà écrite dans `evidence_ledger_entries` ne soit modifiée.**

Mécanisme retenu — **réattribution par résolution, pas par réécriture** :
- `evidence_ledger_entries` n'est pas altérée. Aucune colonne `engagement_id` n'y est ajoutée, aucun `UPDATE` n'y est exécuté.
- La propriété d'une entrée existante est obtenue par une jointure déterministe et à sens unique : `evidence_ledger_entries.entity_id → engagements.entity_id` (contrainte d'unicité garantissant une réponse unique).
- Cette résolution satisfait intégralement l'obligation posée par ADR-001A §4 (« obligation de réattribution explicite au moment où l'Engagement existe ») : dès que ce document est adopté, tout Evidence Ledger devient réattribuable de façon déterministe — sans qu'un seul octet du registre déjà écrit n'ait besoin d'être touché.

Cette décision est en réalité imposée par T1 lui-même : le trigger PostgreSQL de `v18_evidence_ledger.sql` bloque inconditionnellement tout `UPDATE` sur `evidence_ledger_entries`, y compris pour backfiller une colonne nouvellement ajoutée sur des lignes existantes. Tenter une réécriture physique violerait l'invariant d'immutabilité qu'ADR-001 a posé. La résolution par jointure n'est donc pas seulement la solution la plus simple — c'est la seule qui respecte l'architecture déjà en place.

### 3.5 Cycle de vie

Repris du Modèle Idéal §E.1, avec une seule précision ajoutée (amendement, voir §3.3) : la transition `churned → active` est explicitement autorisée, pour représenter la reprise d'une relation avec la même Entity — sans quoi la règle 1:1 durable obligerait soit à contourner le modèle, soit à recréer une Entity pour la même organisation réelle.

```
prospected → active → (paused ↔ active) → churned → (reprise) → active
```

`at_risk` est un état parallèle **dérivé** (calculé, aujourd'hui via une future Attention Score — hors périmètre de T2), jamais une transition manuelle.

**Invariant de transition** (Modèle Idéal §E.1, repris intégralement) : un Engagement ne peut passer à `active` sans au moins une `ScopeDefinition` et une `ReviewCadence` définies.

**Statut initial du backfill — règle corrigée (amendement suite à revue).** L'hypothèse initiale (« `active` par défaut ») est retirée : rien ne démontre qu'une Entity existante représente une relation actuellement active plutôt que, par exemple, une Entity créée puis jamais réellement exploitée, ou une relation aujourd'hui interrompue en pratique sans que le domaine actuel ne l'enregistre nulle part (`relation_type` ne porte aucune notion de statut, seulement de type). Convertir cette absence d'information en `active` aurait été exactement le type d'erreur que l'Article X interdit (« ne convertira jamais une absence de donnée en zéro », et par extension, en une valeur positive non démontrée).

Le seul signal réellement disponible et vérifiable dans le code existant est l'existence d'au moins une `Analysis` déjà réalisée pour cette Entity (`analyses.entity_id`, confirmé actif dans `routers/analyze.py`) : une Analysis passée est un fait constaté, pas une supposition — elle démontre qu'un travail a réellement eu lieu sur cette Entity. Règle de backfill retenue, déterministe et rejouable :

- **Entity avec au moins une Analysis existante → `Engagement.status = active`.** L'existence d'une analyse est une preuve directe d'activité réelle, suffisante pour justifier `active` sans hypothèse supplémentaire.
- **Entity sans aucune Analysis → `Engagement.status = prospect`.** `prospect` est déjà le premier état du cycle de vie défini par le Modèle Idéal — cette règle n'introduit donc aucune valeur nouvelle dans `EngagementStatus`, elle réutilise l'état qui précède, par définition, toute relation active. C'est la lecture la plus fidèle du cycle de vie existant pour « aucune preuve d'activité constatée à ce jour », pas une invention.

`cadence = mensuelle` et `scope = l'entité elle-même` restent appliqués à tout Engagement créé en T2, quel que soit son statut initial : ce sont des valeurs explicitement prescrites par le Blueprint §E (« cadence par défaut = mensuelle »), pas des hypothèses sur l'état réel de la relation — la distinction que la revue demandait de faire.

Pour les Engagements backfillés au statut `active` : l'invariant de transition est satisfait par construction (`ScopeDefinition` et `ReviewCadence` sont déjà posées au moment de la création, avant tout passage effectif à `active`). Pour ceux backfillés au statut `prospect` : l'invariant ne s'applique pas — il ne gate que la transition *vers* `active` — donc aucune violation non plus.

### 3.6 Cadence

`ReviewCadence` (Value Object, Modèle Idéal §E.1) : rythme contractuel de revue, valeur `mensuelle` par défaut pour tout Engagement créé en T2 — instruction explicite du Blueprint §E (« cadence par défaut = mensuelle »). Le jour cible n'est pas fixé par ce document (aucune donnée source ne permet de le déduire pour les Entity existantes) ; il reste `NULL`/non défini jusqu'à ce qu'un utilisateur ou une PR ultérieure le précise.

### 3.7 Période de revue

La période de revue est un **concept défini mais non encore appliqué** en T2. Le Modèle Idéal (glossaire) la décrit comme ce que la Cadence détermine : quand une nouvelle période s'ouvre. Le mécanisme visé à terme — « c'est le calendrier qui déclenche, jamais un utilisateur qui uploade » — appartient à une phase ultérieure du Blueprint, non listée dans le périmètre explicite de T2 (« Aucune interface utilisateur ne change encore ; c'est une fondation invisible »).

T2 introduit donc l'attribut `cadence` sur `Engagement` (permettant de calculer une période à tout moment) **sans** modifier le déclenchement des analyses, qui reste piloté par l'upload utilisateur exactement comme aujourd'hui. Câbler le déclenchement calendaire est explicitement hors périmètre de ce document.

### 3.8 Relation avec les analyses existantes

`analyses.entity_id` n'est pas modifié : aucune colonne `engagement_id` n'est ajoutée à `analyses`. La relation entre une Analysis et son Engagement est, comme pour l'Evidence Ledger (§3.4), résolue par jointure via `entity_id` — et puisque la relation Entity:Engagement est 1:1 et permanente (§3.3, amendement), cette résolution est déterministe et sans ambiguïté pour toute Analysis, passée ou future, sans limite de durée.

Ce choix reste délibérément minimal même une fois la permanence du 1:1 actée : ajouter une colonne `engagement_id` directement sur `analyses` dupliquerait une information déjà résolvable sans ambiguïté par jointure, sans qu'aucun besoin de lecture fréquente ou de performance ne le justifie aujourd'hui (aucun consommateur ne lit encore `engagements` en production, §3.10). Introduire cette colonne sans nécessité démontrée violerait le principe de simplicité (Article XII) au même titre que la dénormalisation de `company_id` écartée en §3.2.

### 3.9 Relation avec la mémoire et les futures recommandations

**Non touchée par T2.** `financial_metrics` et `company_profile` (v5) restent scopés au seul `company_id`, plus grossier que le niveau Engagement. Cette convergence est identifiée par le Blueprint comme une décision **EVOLVE** distincte (ligne « memory_service »), qui n'appartient pas au périmètre explicite de la Phase T2 (§E ne mentionne que l'introduction de l'agrégat Engagement). Reconnecter la Mémoire au niveau Engagement est donc explicitement reporté à une ADR ultérieure.

Les futures Recommendations (Blueprint, décision C.5, phase T3) sont conçues pour être scopées par `engagement_id` dès qu'elles existeront. T2 ne construit pas cette relation, mais la rend possible : l'Engagement existe désormais comme cible stable à référencer.

### 3.10 Stratégie de migration additive

Conforme à l'enveloppe additive prescrite par le Blueprint §C.1/§E. **Ce document décrit la stratégie ; il ne l'exécute pas** (aucune migration n'est jouée par cette ADR — voir Nature en en-tête).

Stratégie décrite pour la PR qui suivra :
1. Une seule table nouvelle : `engagements`. Aucune table existante n'est altérée (ni `entities`, ni `analyses`, ni `evidence_ledger_entries`, ni `decision_arcs`).
2. Contraintes (amendées suite à revue — plus de colonne `company_id`) : `entity_id UUID NOT NULL UNIQUE REFERENCES entities(id) ON DELETE CASCADE`. La `Company` d'un Engagement se résout par jointure vers `entities.company_id`, jamais stockée séparément (§3.2).
3. Backfill (règle corrigée, §3.5) : une ligne insérée pour chaque `entities` existante, avec `cadence = 'mensuelle'` et `scope = <l'entité elle-même>` (valeurs prescrites par le Blueprint, appliquées quel que soit le statut), et `status` déterminé par un signal réel : `active` si au moins une `Analysis` existe déjà pour cette Entity, `prospect` sinon. Un `INSERT` uniquement, jamais un `UPDATE` sur une table existante.
4. Toute nouvelle Entity créée après l'adoption de cette stratégie reçoit son Engagement au même moment (même transaction), pour ne jamais laisser d'Entity orpheline d'Engagement — statut initial déterminé par la même règle qu'au point 3 (`prospect` dans la quasi-totalité des cas, une Entity tout juste créée n'ayant par définition encore aucune Analysis).
5. Aucune interface utilisateur ne change. Aucun consommateur (renderer PDF/PPTX/Excel, routeur, service) n'est modifié pour lire `engagements` — la table est écrite mais non encore lue en production, exactement comme l'Evidence Ledger à l'issue de T1 (même logique de croissance parallèle, ADR-001 §9).

### 3.11 Compatibilité avec les utilisateurs et données existants

Totale. Aucune Entity existante n'est modifiée, aucune Analysis existante n'est modifiée, aucune ligne de `evidence_ledger_entries` ou `decision_arcs` n'est modifiée. Le backfill est purement additif (des lignes nouvelles dans une table nouvelle). Un utilisateur qui se connecte le lendemain de la fusion de T2 ne constate aucune différence — conforme à la promesse du Blueprint §E : « Produit à la fin de T2 : identique pour l'utilisateur ».

### 3.12 Invariants métier

En plus de l'invariant de transition déjà énoncé (§3.5), ce document pose :

- **Unicité 1:1 durable** (amendement) : une Entity ne peut jamais avoir plus d'un Engagement, à aucun instant de son cycle de vie (contrainte `UNIQUE` sur `entity_id`, permanente — pas une simplification de départ, voir §3.3 et §3.14).
- **Absence de duplication de la Company** (amendement, remplace l'ancien invariant de cohérence référentielle) : `Engagement` ne stocke pas `company_id` (§3.2) ; il n'existe donc structurellement aucune possibilité de divergence entre la Company d'un Engagement et celle de l'Entity qu'il enveloppe, puisqu'une seule colonne porte cette information dans tout le domaine (`entities.company_id`). Rien à garantir techniquement en plus, puisqu'il n'y a rien à dupliquer.
- **Immutabilité de l'Evidence Ledger préservée** : aucune stratégie de réattribution ne doit jamais impliquer un `UPDATE` sur `evidence_ledger_entries` (§3.4) — cet invariant d'ADR-001 n'est ni affaibli ni contourné par ce document.
- **Absence ≠ zéro** (Constitution, Article X) : un Engagement sans cadence explicite (jour cible non défini) reste `NULL`, jamais coercé à une valeur par défaut arbitraire au-delà de la cadence elle-même. Le statut initial d'un Engagement backfillé n'est jamais posé par hypothèse (amendement, §3.5) : il découle d'un signal vérifiable (existence d'une Analysis) ou, à défaut de signal, du premier état du cycle de vie (`prospect`) — jamais d'un état supposant une activité non démontrée.
- **One New Truth Rule** (pratique déjà en vigueur depuis T1) : `Entity.relation_type` n'est ni supprimé ni réécrit par ce document. Il continue d'exister, inchangé, comme projection narrative historique — la vérité sur la relation continue devient portée par `Engagement`, sans qu'aucune vérité ne soit dupliquée entre les deux objets.

### 3.13 Risques

- **Heuristique de backfill imparfaite** (nouveau, amendement §3.5) : une Entity ayant eu une Analysis ancienne, même si la relation réelle est aujourd'hui interrompue en pratique, sera backfillée `active` — le seul signal disponible (existence d'une Analysis) ne distingue pas « a été actif un jour » de « est actif aujourd'hui ». Risque assumé et documenté : c'est le seul signal vérifiable disponible dans le domaine actuel (aucune notion de statut n'existe ailleurs que `relation_type`, qui ne porte pas cette information). Un affinement futur (par exemple fondé sur la récence de la dernière Analysis, ou sur la future Attention Score, T4) pourra corriger ce statut sans rien casser — changer le `status` d'un Engagement déjà créé est une opération additive, jamais une réécriture d'Evidence ou d'Analysis.
- **Granularité Mémoire/Billing non résolue** : Mémoire et Billing restent au niveau Company, plus grossier que l'Engagement (§3.9). Risque de confusion pour un futur travail T3 qui supposerait, à tort, que toute donnée du domaine est déjà scopée par Engagement. Documenté explicitement pour éviter cette hypothèse implicite.
- **Absence de câblage** : tant qu'aucun consommateur ne lit `engagements`, une erreur de backfill (par exemple une Entity orpheline) resterait invisible jusqu'à ce qu'un futur consommateur tente la résolution. Mitigation prévue pour la PR d'implémentation : un test d'acceptation dédié (§3.15) vérifie l'exhaustivité et la cohérence du backfill avant toute fusion.

### 3.14 Alternatives rejetées

**Alternative 1 — Engagement = Company.** Rejetée pour le même motif qu'ADR-001A Option B : une Company peut être liée à plusieurs Entities/relations distinctes ; un Engagement au niveau Company mélangerait des relations sans rapport entre elles.

**Alternative 2 — Engagement = Workspace.** Le Workspace est, selon le Current Domain Model, un conteneur technique nommé au sein d'une Company — jamais présenté par aucune source comme porteur d'une relation métier. Aucun appui dans la Constitution ni le Modèle Idéal.

**Alternative 3 — Fusionner Engagement dans Entity (ajouter `cadence`/`status` directement sur `entities`).** C'est l'alternative la plus tentante en apparence (moins de tables), et pourtant rejetée : `Entity` est explicitement qualifiée par le Current Domain Model de conteneur d'accès et de facturation, « jamais lu par la logique de génération du contenu décisionnel ». Y ajouter un cycle de vie métier (avec ses propres événements — `EngagementActivated`, `EngagementPaused`, `EngagementCadenceChanged`, `EngagementChurned`) mélangerait deux responsabilités que le Modèle Idéal sépare délibérément en deux agrégats distincts (§E.1). Le Blueprint lui-même choisit le mot « enveloppe » (§C.1), pas « fusion » — cette alternative contredirait directement la décision de plus haut niveau déjà prise.

**Alternative 4 — Succession de plusieurs Engagements par Entity dans le temps (option B soumise en revue).** [Amendé le 2026-08-07, voir §0 — ce rejet n'est plus tenu pour définitif. La raison (a) ci-dessous est un problème de migration de données historiques, pas un problème de modèle de domaine ; les deux ont été fusionnés à tort dans cette rédaction initiale.] Rejetée *dans l'implémentation T2A*, plus « de façon définitive et pas seulement pour T2A ». Cette option exigerait une règle temporelle déterministe pour rattacher chaque Analysis et chaque Evidence Ledger historique au bon Engagement parmi plusieurs candidats possibles pour une même Entity — par exemple une correspondance par plage de dates (`Analysis.created_at` compris entre le début et la fin d'un Engagement donné). Deux problèmes rendent cette règle non démontrable aujourd'hui : (a) aucune donnée existante ne porte de date de début/fin de relation au niveau Entity — la construire rétroactivement pour les Entities déjà existantes serait une invention, pas une lecture des faits ; (b) même avec une telle règle, une Analysis produite pendant une période ambiguë (chevauchement, relation reprise le même jour qu'une analyse existante) resterait intrinsèquement ambiguë, ce qu'aucune règle temporelle ne peut garantir d'éliminer totalement. Retenir 1:1 durable (§3.3) évite structurellement cette classe de problème : la résolution `entity_id → engagement_id` est triviale et sans ambiguïté par construction, pour toute Evidence ou Analysis, passée ou future, sans dépendre d'aucune règle temporelle. C'est l'option la plus simple compatible avec la Constitution (Article XII) et avec le produit à court terme (aucun besoin actuel de suivre plusieurs relations successives pour une même Entity) — exactement le critère demandé en revue.

**Alternative 5 — Backfiller physiquement `engagement_id` sur `evidence_ledger_entries`.** Rejetée : le trigger d'immutabilité de v18 bloque inconditionnellement tout `UPDATE`, y compris sur une colonne nouvellement ajoutée. Contourner ce trigger pour ce backfill violerait l'invariant même qu'ADR-001 a posé. La résolution par jointure (§3.4) obtient le même résultat fonctionnel sans ce risque.

**Alternative 6 — Conserver `company_id` sur `Engagement`, documenté comme invariant (option soumise en revue).** Rejetée : un invariant seulement documenté (« doit toujours être identique à celui de l'Entity ») sans mécanisme technique de validation n'est pas une garantie, seulement une intention — exactement ce que la revue a demandé de ne pas laisser en l'état. Le rendre techniquement garanti (contrainte `CHECK` inter-lignes ou trigger de validation) est possible mais ajoute une complexité que rien ne justifie aujourd'hui, puisqu'aucun consommateur ne lit encore `engagements` (§3.10) — l'exigence de nécessité démontrée (Article IX) n'est pas remplie. Retenue à la place : ne pas stocker `company_id` du tout (§3.2), et le résoudre par jointure vers `entities.company_id` — la seule option qui élimine la question de cohérence plutôt que de la déplacer vers un mécanisme à construire.

### 3.15 Tests d'acceptation

Prescrits pour la PR d'implémentation qui suivra cette ADR (non exécutés ici) :
1. Chaque Entity existante possède, après migration, exactement un Engagement — aucune Entity orpheline, aucun doublon (garanti par la contrainte `UNIQUE` sur `entity_id`).
2. `engagement.entity_id` correspond exactement à l'Entity enveloppée ; `entities.company_id`, résolu par jointure depuis `engagement.entity_id`, retourne toujours une Company unique et cohérente (aucune colonne `company_id` à comparer, puisqu'elle n'est plus dupliquée — §3.2).
3. Statut du backfill (amendement, §3.5) : tout Engagement dont l'Entity a au moins une Analysis existante a `status = active` ; tout Engagement dont l'Entity n'a aucune Analysis a `status = prospect` — vérifié sur un échantillon couvrant les deux cas. `cadence = mensuelle` et `scope = l'entité elle-même` pour tout Engagement, quel que soit son statut.
4. Zéro ligne modifiée dans `evidence_ledger_entries`, `decision_arcs`, `analyses`, `entities` (comparaison de comptage et de contenu avant/après migration — même méthodologie que l'Evidence Count Invariant de T1C-B).
5. Résolution Evidence Ledger → Engagement : pour un jeu de test, toute entrée `evidence_ledger_entries.entity_id` non nulle résout vers exactement un Engagement.
6. Permanence de la résolution 1:1 (amendement, §3.3) : pour une Entity simulée traversant `active → churned → active` (reprise), toute Analysis et toute Evidence, produites avant ou après la reprise, résolvent vers le même et unique Engagement — aucune ambiguïté introduite par le changement de statut.
7. Suite de tests complète : zéro régression (même discipline que T1 — comparaison au baseline immédiatement avant migration).
8. Aucun renderer (PDF/PPTX/Excel), aucune route, aucun export ne change de comportement observable.

### 3.16 Rollback

Trivial par construction. `DROP TABLE engagements` — aucune autre table ne référence `engagements` en T2 (§3.8 et §3.4 résolvent par jointure depuis `evidence_ledger_entries`/`analyses` vers `engagements`, jamais l'inverse ; supprimer `engagements` casse ces résolutions mais aucune donnée n'est perdue ni corrompue). Aucun consommateur de production ne lit `engagements` à l'issue de T2 — un rollback est donc sans impact utilisateur, à l'image du rollback d'ADR-001 pour l'Evidence Ledger.

### 3.17 Conformité à la Constitution

| Article | Application |
|---|---|
| **Article IV** (Le Modèle Métier — Engagement) | Ce document exécute littéralement la définition déjà adoptée ; il ne la modifie pas et n'en crée pas de nouvelle. |
| **Article V** (La Mémoire) | Non affecté par T2 (§3.9) — la convergence Mémoire/Engagement est explicitement reportée, pas ignorée. |
| **Article IX** (L'Évolution) | La succession de plusieurs Engagements par Entity est rejetée de façon définitive, pas seulement reportée (§3.14 alternative 4) — aucune règle temporelle déterministe ne peut être démontrée sur les données actuelles. Ce qui reste réellement différé faute de nécessité démontrée aujourd'hui : `engagement_id` sur `analyses`, câblage de la période de revue, dénormalisation de `company_id`. |
| **Article X** (Les Interdictions — deux vérités, absence ≠ zéro) | `Entity.relation_type` n'est pas dupliqué avec `Engagement.status` ; l'Evidence Ledger n'a jamais deux propriétaires possibles ; aucune valeur par défaut ne remplace une absence de donnée (cadence sans jour cible reste non définie). |
| **Article XII** (Simplicité, représentation unique) | Un seul agrégat nouveau, une seule table nouvelle, aucune table existante modifiée ; résolution par jointure préférée à toute duplication de référence. |

---

## 4. Traçabilité (GD-001 §3ter)

- **Section du Blueprint concernée :** §E « Phase T2 — Introduire `Engagement` en enveloppe additive », en cohérence avec §B (ligne 2, correspondance `Entity (+ relation_type) → Engagement`, décision EVOLVE) et le détail §C.1.
- **Articles de la Constitution concernés :** IV (définition), V (limite explicite du périmètre), IX (nécessité démontrée pour chaque extension écartée), X (interdictions), XII (principes d'architecture).
- **ADR précédentes engagées par ce document :** ADR-001 §9 (méthode de croissance parallèle, réappliquée à `engagements`), ADR-001A §4 (obligation de réattribution, honorée par résolution — §3.4 du présent document).

---

## 5. Questions ouvertes

1. *(Retirée en v2 — était : « à quel moment assouplir la contrainte 1:1 ? ». La revue a demandé une décision définitive plutôt qu'une question ouverte ; §3.3 et §3.14 alternative 4 tranchent désormais que la contrainte 1:1 est permanente, pas provisoire.)*
2. Quelle ADR future rapprochera la granularité de la Mémoire (Company) de celle de l'Engagement (§3.9) — et à quelle phase du Blueprint cela correspond-il exactement ?
3. Quand un premier consommateur de production commencera-t-il à lire `engagements` (jour cible de cadence, calcul de période de revue, câblage du déclenchement calendaire) — question symétrique à celle laissée ouverte par ADR-001 pour l'Evidence Ledger.
4. *(Nouvelle, v2)* L'heuristique de backfill du statut (§3.5 : `active` si Analysis existante, `prospect` sinon) devra-t-elle être recalculée une fois la future Attention Score (T4) disponible, ou le statut backfillé initial reste-t-il figé comme point de départ historique une fois la migration jouée ? Question à trancher au moment où l'Attention Score sera conçue, pas avant.

---

**ADR-002 AMENDED AND READY FOR REVIEW.
AUCUN CODE MODIFIÉ.**
