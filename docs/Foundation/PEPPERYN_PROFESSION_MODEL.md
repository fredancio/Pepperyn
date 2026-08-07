# PEPPERYN PROFESSION MODEL v1.0

**Statut :** Proposé, document fondateur — au-dessus de la Constitution dans la hiérarchie documentaire
**Nature :** réflexion de modélisation du métier. Aucun code, aucun écran, aucune technologie, aucun LLM n'est mentionné ci-dessous comme critère de décision.
**Sources autorisées pour sa rédaction :** Pepperyn Constitution v1.0 · Ideal Domain Model · Current Domain Model · Transformation Blueprint · ADR-001/001A/002/003(v1-v3) · l'ensemble des sprints produit antérieurs

---

## Préambule — pourquoi ce document existe

Chaque document de gouvernance de Pepperyn répond à une question différente. La Constitution répond à *ce que Pepperyn s'engage à faire et à ne jamais faire*. Le Domain Model répond à *comment ces engagements se traduisent en objets et frontières DDD*. Le Blueprint répond à *comment on passe de l'état actuel à cet état cible*. Aucun de ces documents ne répond à une question antérieure à toutes les autres : *de quel métier humain Pepperyn est-il la modélisation ?*

Ce document comble ce vide. Il ne décrit pas Pepperyn — il décrit le métier que Pepperyn tente de comprendre puis d'amplifier. Il se situe au-dessus de la Constitution parce que la Constitution elle-même en est déjà, sans le nommer explicitly, une conséquence : l'Article II (Le Jugement Humain), l'Article IV (les six objets permanents du domaine), l'Article VII (l'Attention comme ressource rare) ne sont pas des choix arbitraires — ce sont des observations sur le métier de CFO, formalisées en principes normatifs. Ce document rend cette origine explicite, et devient la référence à laquelle la Constitution elle-même doit rester fidèle si le métier venait à être mieux compris.

**Hiérarchie documentaire révisée :** PEPPERYN_PROFESSION_MODEL.md (ce document) → Constitution → Ideal/Current Domain Model → Blueprint → ADR → code.

---

## Chapitre 1 — L'hypothèse North Star, challengée

**L'hypothèse posée :** *Pepperyn n'est pas conçu à partir d'une liste de fonctionnalités. Pepperyn est la modélisation informatique du métier de CFO — pas d'un CFO particulier, des invariants du métier.*

### 1.1 — Cohérence avec ce qui existe déjà

Un examen honnête de l'historique architectural de ce projet montre que cette hypothèse n'est pas une nouvelle direction — c'est le nom qui manquait à une direction déjà prise, à plusieurs reprises, sans être théorisée comme telle :

- Le Current Domain Model (Phase 1D) a diagnostiqué le système *avant* toute refonte comme « un pipeline de transformation centré sur l'événement *une analyse* », sans concept de relation suivie dans la durée. Ce diagnostic est exactement celui d'un système pensé en fonctionnalités (upload → résultat), pas en métier.
- Introduire Engagement (ADR-002) comme objet permanent, qui « précède et dépasse chaque intervention ponctuelle » (Constitution Article IV), n'est pas une décision technique — c'est la reconnaissance qu'un CFO ne travaille jamais sur un fichier isolé, il porte une relation continue avec une organisation. C'est un fait du métier, traduit en architecture.
- L'Evidence Ledger et sa discipline « absence ≠ zéro » (ADR-001) ne sont pas un choix de structure de données — c'est la reproduction exacte du réflexe professionnel qui refuse de confondre une donnée manquante avec une valeur nulle, un réflexe qui distingue un CFO rigoureux d'un CFO négligent.
- Le cycle complet de la Recommandation (Constitution Article VI : proposée → discutée → acceptée/rejetée/différée → exécutée → confrontée au réel) modélise le cycle de jugement d'un CFO, pas un statut de ticket.
- Le Financial Time Engine (ADR-003, toutes versions) part explicitement de l'axiome « aucune donnée financière n'a de sens hors de sa dimension temporelle » — c'est une description du raisonnement d'un CFO, formalisée en Value Objects.

**Conclusion : l'hypothèse est cohérente, et elle est meilleure que le cadre implicite précédent — non pas parce qu'elle change la direction du projet, mais parce qu'elle donne un critère explicite et testable à une intuition qui, jusqu'ici, ne s'exprimait que projet après projet, ADR après ADR, sans jamais être écrite comme principe directeur.**

### 1.2 — Ce qui doit néanmoins être corrigé dans l'hypothèse telle qu'énoncée

Deux réserves sérieuses, à ne pas taire :

**Première réserve — « le métier de CFO » est une simplification qui cache deux métiers.** Un CFO en interne, responsable d'une seule organisation, et un CFO externe/fractional gérant un portefeuille de plusieurs organisations simultanément, n'exercent pas le même métier au sens strict. Le premier n'a jamais besoin de *prioriser entre organisations* — cette compétence n'existe même pas dans son répertoire. Le second en a besoin en permanence, et c'est très exactement ce que Portfolio Attention & Prioritization (Core) modélise. Réduire Pepperyn au métier du CFO unique reviendrait à perdre de vue la moitié de ce que Pepperyn a déjà construit. Ce document retient donc deux profils professionnels, pas un — voir Chapitre 4.

**Deuxième réserve — le critère doit toujours être lu avec le garde-fou de l'Article II.** « Que ferait un excellent CFO » et « quelles parties de ce raisonnement un logiciel peut-il reproduire ou amplifier » ne suffisent pas seuls à empêcher Pepperyn de glisser vers la prise de décision elle-même — reproduire l'ACTE (rédiger une phrase qu'un CFO écrirait) n'est pas la même chose que reproduire la RESPONSABILITÉ (porter l'engagement et le risque de ce qui est dit). Cette distinction n'est pas secondaire : elle est développée en détail au Chapitre 6, parce que sans elle, le critère peut être détourné pour justifier presque n'importe quoi.

Avec ces deux réserves intégrées plutôt qu'ignorées, l'hypothèse est retenue comme fondement de ce document.

---

## Chapitre 2 — Les responsabilités invariantes du métier de CFO

Repartant du métier seul, sans penser à Pepperyn, douze responsabilités se dégagent — organisées en trois familles, pas une liste plate, parce que leur nature diffère.

**Famille A — les fondations (sans elles, rien d'autre n'est fiable) :**
1. **Comprendre** — construire une représentation exacte de la réalité financière de l'organisation, distinguer ce qui est su de ce qui est incertain ou manquant.
2. **Contextualiser** — ne jamais lire un chiffre dans l'absolu ; le situer dans le temps, en comparaison, en historique.
3. **Se familiariser** — construire une connaissance de l'organisation elle-même (son histoire, ses personnes, ses habitudes) avant de pouvoir bien exercer les autres responsabilités.
4. **Garantir l'intégrité** — ne jamais laisser une affirmation non sourcée passer pour un fait ; vérifier avant d'avancer.

**Famille B — l'action (ce qu'un CFO fait de cette compréhension) :**
5. **Questionner** — détecter ce qui ne colle pas, exiger une explication, refuser le silence sur une anomalie.
6. **Prioriser** — allouer une attention rare (la sienne, celle du dirigeant, celle du conseil) à ce qui compte le plus, maintenant.
7. **Décider / Juger** — prendre position sous incertitude, recommander une direction, en porter la responsabilité.
8. **Anticiper** — voir venir une échéance, un risque, un besoin, avant qu'il ne devienne urgent.

**Famille C — la relation (ce qui fait qu'un CFO reste utile dans la durée) :**
9. **Mémoriser et apprendre** — se souvenir de ce qui a été décidé, confronter la décision au réel, ajuster le jugement futur.
10. **Communiquer / traduire** — adapter la même vérité à des audiences différentes sans jamais la déformer.
11. **Accompagner** — être un partenaire de confiance, pas seulement un rapporteur de chiffres.
12. **Négocier / représenter** — engager la parole de l'organisation face à un tiers (banque, investisseur, administration).

---

## Chapitre 3 — Cartographie complète

| # | Responsabilité | Fondamentale ? | Modélisée par Pepperyn ? | Composant |
|---|---|---|---|---|
| 1 | Comprendre | Oui | Oui | Financial Evidence & Truth / Evidence Ledger |
| 2 | Contextualiser | Oui | Oui | Financial Time Engine |
| 3 | Se familiariser | Oui | **Non — hypothèse à l'étude** | Enterprise Familiarization (voir Ch. 5) |
| 4 | Garantir l'intégrité | Oui | Oui, le plus mature des douze | Evidence Ledger (absence ≠ zéro, hiérarchie de provenance, Article III) |
| 5 | Questionner | Oui | **Nommé mais non planifié** | Exception & Reconciliation (Core dans le Modèle Idéal, absent des phases T0-T6 du Blueprint) |
| 6 | Prioriser | Oui | Conçu, pas construit | Portfolio Attention & Prioritization / Attention Score (T4) |
| 7 | Décider / Juger | Oui | Volontairement partiel | Recommendation (T3) — Pepperyn propose, ne décide jamais (Article II) |
| 8 | Anticiper | Oui | Oui, renforcé récemment | Financial Time Engine — `FutureBusinessMoment` (ADR-003 v3) |
| 9 | Mémoriser et apprendre | Oui | Oui | Decision Memory / `DecisionArc` (code réel existant) + Knowledge Model / `BusinessHistory` |
| 10 | Communiquer / traduire | Oui | Oui, partiellement | Reporting & Deliverables, futur lexique temporel (ADR-003 v3 §4) |
| 11 | Accompagner | Oui | Minimalement | Chat / Conversation Engine — explique, ne recalcule jamais ; le partenariat proactif reste à construire |
| 12 | Négocier / représenter | Oui | **Non, et ne doit jamais l'être** | Hors périmètre par principe |

Deux constats se dégagent de cette cartographie, et ce sont les plus importants de tout ce document : **la responsabilité n°5 (Questionner) est nommée dans le Modèle Idéal depuis le début mais n'a jamais reçu de phase d'implémentation dans le Blueprint** — c'est un vrai manque, pas un détail. Et **la responsabilité n°3 (Se familiariser) n'a jamais eu de composant du tout avant cette mission** — voir Chapitre 5.

---

## Chapitre 4 — Deux métiers, pas un

Le Chapitre 1 a posé la réserve : « le CFO » recouvre deux professions distinctes, et les responsabilités 1 à 12 ne se répartissent pas identiquement entre elles.

**Le CFO en interne** exerce les douze responsabilités envers **une seule organisation**. Sa priorisation (responsabilité 6) porte sur les sujets internes à cette organisation — quel projet financer, quel risque traiter en premier — jamais sur un choix entre plusieurs organisations.

**Le CFO fractional / le cabinet gérant un portefeuille** exerce les mêmes douze responsabilités, mais la responsabilité 6 change radicalement de nature : elle devient un arbitrage **entre organisations**, sous une contrainte de temps partagé qu'un CFO interne ne connaît jamais. C'est précisément ce que Portfolio Attention & Prioritization modélise, et c'est un besoin qui n'existe dans aucun manuel du métier de CFO interne.

Pepperyn modélise les deux, mais son différenciateur réel — celui déjà validé par les sprints produit antérieurs, celui pour lequel un marché a été confirmé — est spécifiquement la seconde profession. Le North Star doit donc se lire ainsi : *les invariants du métier de CFO, exercés dans un contexte de portefeuille*, pas *le métier de CFO en général*. Cette précision n'affaiblit pas l'hypothèse — elle l'empêche de dériver vers un produit générique de CFO-en-interne, un marché déjà jugé plus encombré et moins différenciable par les sprints Vision antérieurs.

---

## Chapitre 5 — Enterprise Familiarization

### 5.1 — L'idée, challengée

Le parallèle proposé (un nouveau CFO ne reste jamais six mois inactif ; il commence immédiatement à apprendre) est juste, mais il porte un risque réel : que « Familiarization » ne devienne qu'un nom marketing pour le même pipeline d'ingestion de fichiers, exécuté plus tôt. Pour que l'idée soit une vraie responsabilité métier et non une fonctionnalité déguisée, elle doit produire quelque chose de qualitativement différent d'une analyse — pas un jugement, mais une accélération de la connaissance disponible avant qu'un jugement ne soit possible.

Testée contre cette exigence, l'idée tient : contrairement au rythme habituel (une nouvelle période arrive, une analyse est jugée pertinente — voir ADR-003 v2 §4.8), la Familiarization ingère plusieurs années d'historique en une seule fois. C'est une différence de nature, pas seulement de vitesse : le mécanisme de détection de motif du Knowledge Model (`BusinessHistory`, seuil de trois occurrences, INV-HISTORY-1) peut, pour la première fois, être satisfait dès la première session plutôt qu'après trois mois d'attente — sans qu'aucun invariant n'ait besoin d'être modifié pour cela. C'est une bonne indication que l'idée s'insère naturellement dans le modèle déjà construit plutôt que de le forcer.

### 5.2 — Où elle s'insère

Ce n'est pas un nouveau Bounded Context. C'est une **phase de vie de l'Engagement** — voir Chapitre 6. Son propriétaire naturel reste Engagement (au même titre que l'Evidence Ledger et le Knowledge Model), pas un composant séparé : la Familiarization ne fait qu'accélérer le remplissage de ce qu'Engagement possède déjà.

---

## Chapitre 6 — Les phases de vie de l'Engagement, revues

**Un Engagement ne commence jamais à la première analyse.** Il commence à l'engagement de la relation elle-même — avant qu'aucune donnée financière n'ait été échangée.

1. **Prospect** (déjà modélisé, ADR-002) — évaluation de l'adéquation, avant tout engagement réel.
2. **Familiarization** (nouvelle phase, identifiée par cette mission) — l'engagement est réel, mais le régime n'est pas encore celui du cycle périodique : ingestion intensive de l'historique, rencontre des personnes clés, remplissage accéléré du Knowledge Model. Se distingue de Prospect (un engagement réel existe déjà) et d'Active (le rythme n'est pas encore celui d'un cycle périodique).
3. **Active** (déjà modélisé) — le cycle stable : nouvelle donnée, jugement de pertinence temporelle, analyse, recommandation, revue.
4. **Paused** (déjà modélisé, ADR-002) — relation suspendue sans être rompue, le Knowledge Model est conservé.
5. **At-risk** — signal dérivé, pas une phase à part entière (choix déjà fait par ADR-002, confirmé ici plutôt que rouvert).
6. **Churned** (déjà modélisé) — fin de la relation.

**Une septième phase mérite d'être nommée sans être priorisée maintenant :** une phase de *transition/passation*, entre Active et Churned, où un CFO sortant transmet formellement sa connaissance à un successeur — un CFO professionnel ne quitte jamais un poste sans passation structurée. Cette phase n'a aujourd'hui aucune preuve de besoin concret dans Pepperyn ; elle est consignée ici comme hypothèse à surveiller, pas comme décision.

---

## Chapitre 7 — La loi de conception, challengée et complétée

**La loi proposée :** chaque capacité doit (1) reproduire fidèlement une responsabilité réelle d'un excellent CFO, ou (2) l'amplifier grâce à une force propre aux systèmes logiciels (mémoire, rapidité, cohérence, disponibilité, vision historique).

**Test de robustesse — la loi rejette-t-elle vraiment quelque chose ?** Une capacité de gamification (badges, séries de complétion) ne reproduit ni n'amplifie aucune des douze responsabilités du Chapitre 2 — la loi la rejette correctement. Une capacité de « rédiger l'e-mail à la banque à la place du CFO » reproduirait en apparence la responsabilité 12 (Négocier/représenter) — et c'est précisément là que la loi, prise seule, est dangereuse : elle confond reproduire l'*acte* (des mots) et reproduire la *responsabilité* (l'engagement et le risque qui vont avec ces mots).

**Complément nécessaire, sans lequel la loi n'est pas fiable :** la loi ne s'applique jamais à la substance *décisionnelle* ou *représentative* d'une responsabilité — seulement à sa substance *informationnelle et mécanique*. Reformulée complètement :

> *Une capacité a sa place dans Pepperyn si elle reproduit fidèlement, ou amplifie grâce aux forces propres d'un système logiciel, la partie compréhensive, mémorielle, comparative ou préparatoire d'une responsabilité réelle d'un excellent CFO — jamais la partie où ce CFO engage son jugement, sa signature ou la parole de l'organisation face à un tiers.*

Avec ce complément, la loi devient un principe fondateur recommandé. Sans lui, elle reste une belle phrase que n'importe quelle fonctionnalité peut rhétoriquement satisfaire.

---

## Chapitre 8 — Ce que Pepperyn ne fera jamais

Directement dérivé de la cartographie (Chapitre 3) et de la loi complétée (Chapitre 7) :

- Décider à la place du CFO (responsabilité 7 reste humaine dans son cœur — Pepperyn propose, Article II tranche).
- Négocier ou représenter l'organisation face à un tiers (responsabilité 12, entièrement humaine).
- Construire la confiance relationnelle profonde qui fonde l'accompagnement (responsabilité 11) — Pepperyn peut y contribuer, jamais s'y substituer.
- Transformer un constat (pertinence temporelle, récurrence d'un motif) en jugement de priorité comparatif sans base factuelle traçable — déjà protégé par INV-TIME-9 (ADR-003), maintenant justifié aussi au niveau du métier, pas seulement de l'architecture.

**Une précision devenue nécessaire depuis la mise en place de la validation par les résultats (voir PEPPERYN_MODEL_FIDELITY_PROTOCOL.md, Outcome Validation) :** une preuve d'impact positif, aussi solide soit-elle, ne déplace jamais ces limites. Un résultat observé ne peut jamais servir à justifier une décision automatique non autorisée, une causalité inventée au-delà de ce qu'un proxy honnête peut soutenir, un transfert implicite de responsabilité de l'humain vers Pepperyn, ou une optimisation d'un indicateur au détriment de l'intégrité (Article III). La validation par les résultats mesure si Pepperyn aide bien — elle ne redéfinit jamais ce que Pepperyn a le droit de faire.

---

## Chapitre 9 — Comment utiliser ce document

Toute nouvelle capacité proposée à Pepperyn doit répondre, dans l'ordre :

1. À laquelle des douze responsabilités du Chapitre 2 se rattache-t-elle ? Si aucune, elle est probablement hors périmètre.
2. Reproduit-elle la partie informationnelle/mécanique de cette responsabilité, ou l'amplifie-t-elle par une force logicielle réelle (Chapitre 7) ? Si ni l'un ni l'autre, elle n'a pas sa place.
3. Touche-t-elle à la partie décisionnelle, relationnelle-profonde ou représentative de cette responsabilité (Chapitre 8) ? Si oui, elle doit rester une préparation pour l'humain, jamais une substitution.

Ce test ne s'applique qu'aux capacités qui prétendent différencier Pepperyn sur le métier lui-même — pas aux fonctions opérationnelles nécessaires au produit (facturation, authentification, export technique) qui n'ont pas vocation à passer ce filtre et ne doivent pas être forcées à le faire.

Ce test à trois questions établit la **Profession Validity** d'une capacité — répond-elle au métier. Il ne dit rien de si Pepperyn la traduit correctement (**Product Validity**) ni si elle améliore réellement un résultat (**Outcome Validity**). Les trois niveaux sont nécessaires ensemble et ne se remplacent jamais l'un l'autre — leur définition complète vit dans PEPPERYN_MODEL_FIDELITY_PROTOCOL.md pour éviter de dupliquer la méthode ici.

---

## Chapitre 10 — Auto-critique sévère

**Nous sommes-nous trompés depuis le début, ou modélisions-nous déjà le métier sans le savoir ?** Ni l'un ni l'autre pris seul. Le Current Domain Model a documenté, sur le code réel, un système initialement construit comme un pipeline de fonctionnalités — cinq représentations concurrentes du même « résultat d'analyse », aucune notion de relation suivie. C'est la preuve que le point de départ réel était bien du côté du logiciel-produit, pas du métier. Mais chaque correction architecturale menée depuis (Engagement, Evidence Ledger, cycle de la Recommandation, Financial Time Engine, Knowledge Model) s'est faite, sans exception, dans la direction du métier — sans que cette direction soit nommée avant aujourd'hui. La honnête conclusion : nous avons commencé du mauvais côté, et corrigé la trajectoire projet après projet vers celui-ci, sans le théoriser jusqu'à cette mission.

**Risques réels de cette North Star, sans complaisance :**

- **Rigidité potentielle.** Une application trop littérale du filtre du Chapitre 9 pourrait rejeter une innovation authentique qu'aucun CFO n'a jamais pu concevoir précisément parce qu'aucun humain ne pouvait la faire — le risque existe même si la branche « amplification » du Chapitre 7 est censée l'absorber. Seule une application disciplinée, pas mécanique, évite ce piège.
- **Biais d'archétype.** « Un excellent CFO » n'est pas une figure universelle — le métier varie fortement selon le secteur, la taille, la culture de l'organisation. Ce document reflète nécessairement une vision partielle, probablement plus proche du profil déjà rencontré dans les sprints produit précédents que d'un CFO universel. Ce biais n'est pas corrigé ici ; il est signalé.
- **Oubli du marché.** La fidélité au métier n'est pas un substitut à la validation commerciale — une capacité peut être une reproduction fidèle d'une responsabilité de CFO et rester commercialement inutile. Les deux tests (fidélité au métier, viabilité commerciale) doivent continuer à être appliqués séparément ; ce document n'en remplace aucun.
- **Dérive de catégorie d'utilisateur.** Le Chapitre 4 a déjà nommé ce risque explicitement : recentrer trop fortement sur « le CFO » générique pourrait diluer ce qui différencie réellement Pepperyn aujourd'hui — le métier du portefeuille, pas celui d'un seul CFO.
- **Sur-justification rhétorique.** Un critère aussi englobant que « que ferait un excellent CFO » peut, mal appliqué, justifier presque n'importe quoi a posteriori. Sa valeur dépend entièrement de la rigueur adversariale avec laquelle il est appliqué à chaque nouvelle proposition — exactement comme les tests de conformité de la Constitution (Article XI) ne valent que par leur application honnête, jamais par leur seule existence.

---

## Chapitre 11 — Principe de non-dogmatisme

Aucune responsabilité professionnelle n'est considérée comme définitivement acquise. Ce modèle reste une représentation provisoire du métier, continuellement confrontée à la pratique, aux résultats observés et aux professionnels de terrain. Toute responsabilité peut être enrichie, raffinée, déplacée ou retirée si les preuves l'exigent — y compris les douze responsabilités du Chapitre 2, y compris la cartographie du Chapitre 3, y compris la loi du Chapitre 7.

Ce principe est un garde-fou méthodologique, pas une posture rhétorique. Il existe pour empêcher quatre dérives précises : la fossilisation du modèle (traiter les douze responsabilités comme une liste close plutôt que comme la meilleure compréhension actuelle) ; l'autorité excessive des documents (traiter ce document comme une preuve en soi plutôt que comme une hypothèse organisée) ; la défense d'une décision par ancienneté (« c'est dans le modèle depuis longtemps donc c'est vrai ») ; la confusion entre cohérence interne et vérité terrain (un modèle peut être parfaitement cohérent avec lui-même et pourtant faux — la cohérence ne remplace jamais la confrontation au réel, voir PEPPERYN_MODEL_FIDELITY_PROTOCOL.md).

**La révisabilité n'est pas l'instabilité.** Une responsabilité qui a atteint le palier « Validée » du protocole de validation n'est pas remise en cause par un retour isolé, aussi convaincant soit-il en apparence — c'est précisément le rôle du système de paliers de preuve (Hypothèse → Corroborée → Validée) de protéger une responsabilité établie contre une réécriture prématurée, tout en restant ouverte à une révision réelle lorsque la preuve s'accumule véritablement. La mécanique complète — quels signaux déclenchent une révision, qui peut la proposer, quel niveau de preuve est requis — est définie dans PEPPERYN_MODEL_FIDELITY_PROTOCOL.md.

---

## Chapitre 12 — La question de clôture

**Si Pepperyn suivait cette North Star pendant dix années supplémentaires, deviendrait-il le meilleur logiciel de finance, ou quelque chose que les catégories actuelles ne décrivent pas correctement ?**

Pas le meilleur logiciel de finance au sens des catégories existantes (BI, EPM, FP&A) — cette voie a déjà été examinée et écartée par les sprints Vision antérieurs, précisément parce qu'elle mène vers un marché encombré (« océan rouge ») où la différenciation est difficile. Ce que cette North Star construit, si elle est suivie avec la rigueur que ce document exige, n'est structurellement pas un outil de reporting ni une plateforme de visualisation — c'est une **mémoire professionnelle durable et cumulative, au service d'une relation suivie dans le temps**. Aucun des objets les plus significatifs bâtis jusqu'ici — Engagement comme relation permanente, Decision Memory, Knowledge Model, BusinessHistory — n'appartient au vocabulaire du BI ou de l'EPM. Ils appartiennent au vocabulaire de la relation professionnelle et du jugement accumulé.

Dix ans de fidélité à cette North Star mèneraient donc probablement à quelque chose que la catégorie actuelle « logiciel de finance » décrit mal — plus proche, dans sa nature, d'une mémoire et d'un jugement professionnels externalisés que d'un tableau de bord, aussi sophistiqué soit-il. Cette affirmation reste, par construction, une projection non vérifiée — seule l'exécution réelle, confrontée à des utilisateurs réels sur plusieurs années, pourra la confirmer ou l'infirmer.

---

**PEPPERYN_PROFESSION_MODEL v1.0 READY FOR REVIEW. AUCUN CODE, AUCUNE ARCHITECTURE TECHNIQUE, AUCUNE FONCTIONNALITÉ N'EST DÉCIDÉE PAR CE DOCUMENT.**
