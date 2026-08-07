# PROFESSION_MODEL_FOUNDATION_CLOSURE.md

**Statut :** Clôture d'un sprint architectural. Constate un état, n'en ouvre aucun nouveau.
**Nature :** document court. Aucun code, aucune migration, aucune API, aucun composant logiciel n'est produit ou modifié par cette clôture.

---

## Ce qui a été établi

**North Star retenue :** Pepperyn est la modélisation computationnelle des invariants du métier de CFO, exercés dans un contexte de portefeuille — pas d'un CFO particulier, pas du métier de CFO interne seul (PEPPERYN_PROFESSION_MODEL.md, Chapitres 1 et 4).

**Méthode de modélisation retenue :** douze responsabilités invariantes, dérivées du métier seul puis cartographiées contre l'architecture existante ; une loi d'acceptation des capacités complétée d'un garde-fou explicite contre la confusion entre reproduire un acte et reproduire une responsabilité (Chapitres 2, 3, 7).

**Trois niveaux de validation, jamais interchangeables :** Profession Validity (le métier le reconnaît-il), Product Validity (Pepperyn le traduit-il et est-il utilisé comme prévu), Outcome Validity (cela améliore-t-il réellement un résultat) — PEPPERYN_MODEL_FIDELITY_PROTOCOL.md §6.

**Caractère falsifiable :** quatre scénarios explicitement nommés comme capables de réfuter le modèle, en tout ou partie, avant même toute méthode de validation (protocole §0).

**Model Gap Register :** registre permanent des écarts de fidélité au métier, avec paliers de preuve (Hypothèse → Corroborée → Validée → Intégrée), créé et vide — MODEL_GAP_REGISTER.md.

**Validation par l'impact :** couche Outcome Validation ajoutée, avec proxys explicitement challengés (forts et faibles distingués) plutôt que repris mécaniquement, et un registre séparé — PROFESSION_MODEL_EVIDENCE_LOG.md, créé et vide (protocole §7, §9).

**Principe de non-dogmatisme :** intégré comme Chapitre 11 du Profession Model — aucune responsabilité n'est définitivement acquise, la révisabilité protégée contre l'instabilité par le même système de paliers de preuve qui permet la révision.

**Version minimale de gouvernance à maintenir, non négociable :** quatre entretiens par an (un par profil), le Model Gap Register et PROFESSION_MODEL_EVIDENCE_LOG.md tenus à jour en continu, une revue annuelle du Profession Model — protocole §12.

**Limites encore ouvertes, non résolues par cette clôture :** aucune vague d'entretien réelle n'a encore eu lieu — les deux registres sont vides par construction ; le biais de sélection des CFO accessibles à l'équipe n'est pas corrigé, seulement rendu mesurable dans le temps ; l'écart entre ce qu'un CFO raconte en entretien et ce qu'il fait réellement reste hors de portée de ce protocole ; le proxy « réduction des contradictions entre analyses » reste aspirationnel, sans mécanisme de détection encore défini.

---

## Constat de suffisance

**La fondation méthodologique est désormais suffisante pour guider le produit. Elle n'a besoin d'aucun enrichissement supplémentaire avant de rencontrer le terrain.**

À partir de cette clôture, aucun nouveau sprint abstrait sur cette méthode n'est autorisé sans l'un des quatre déclencheurs suivants, et aucun autre : un signal issu d'un utilisateur réel, un résultat observé et consigné dans PROFESSION_MODEL_EVIDENCE_LOG.md, un écart atteignant le palier « Validée » dans MODEL_GAP_REGISTER.md, ou une contradiction rencontrée en développement que le modèle actuel ne permet pas de résoudre (protocole §8). Une intuition, même excellente, n'en fait pas partie.

---

## Prochaine étape — retour au logiciel

Pas une nouvelle théorie. Une capacité produit déjà ouverte, déjà planifiée, reliée à un usage utilisateur réel : **reprendre l'Incrément 2 de la Capability 3 — Decision Follow-up**, dont le plan est prêt et qui attend un GO (mémoire projet, 2026-08-05).

Ce choix n'est pas arbitraire : il est directement corroboré par cette clôture elle-même. « Moins de recommandations sans suivi » est l'un des proxys forts d'Outcome Validity retenus au protocole §7.2, et Decision Follow-up est précisément la capacité qui produirait cette évidence en pratique — sur `DecisionArc`, code réel déjà existant. C'est la première capacité que ce nouveau cadre méthodologique pourra réellement observer, pas seulement théoriser.

---

## Auto-critique finale

**Le protocole est-il assez léger pour être réellement utilisé ?** Non, dans sa forme complète — deux vagues par an, dix entretiens, double codage indépendant est un effort réel pour une petite équipe. Seule sa version minimale (§12) l'est, et c'est elle qui doit être tenue pour vraie, pas la version complète.

**Qu'est-ce qui risque de devenir bureaucratique ?** La mesure du taux d'accord inter-codeurs, la couverture systématique des cinq profils à chaque vague, et la tenue exhaustive de tous les champs du Gap Register pour une entrée mineure — ce sont les premiers éléments à simplifier sous contrainte de temps, jamais la méthode de récit elle-même.

**Version minimale non négociable :** quatre entretiens par an, les deux registres tenus à jour en continu, une revue annuelle — rien de moins, sans quoi les niveaux A et C de validation (§6) deviennent purement déclaratifs.

**Ce qui ne doit surtout pas être mesuré :** le temps gagné comme métrique primaire (confondu trop facilement avec l'expérience croissante de l'utilisateur) ; le volume d'utilisation comme proxy de valeur (l'usage n'est pas l'impact, protocole §6-B) ; la satisfaction générale envers Pepperyn comme substitut à la fidélité au métier (confond le confort du produit avec la justesse du modèle).

**Premier signe que la méthode devient une fin en soi :** un sprint planifié pour « améliorer le Profession Model » sans qu'aucune entrée des deux registres ni aucun signal terrain ne le motive — la violation directe de l'interdiction posée plus haut dans ce document, et donc le signal le plus facile à détecter, à condition de vouloir le voir.

**Conditions pour rouvrir ce sprint architectural :** une entrée du Model Gap Register atteignant le palier « Validée » avec un cas d'irréductibilité réel ; un signal de dérive confirmé sur deux vagues consécutives (protocole §4) ; une contradiction de développement que le modèle ne résout pas. Jamais parce que cela fait longtemps, jamais parce que ce serait intéressant à revisiter.

---

```
PROFESSION MODEL FOUNDATION CLOSURE COMPLETED.

FINAL VERDICT:
PROFESSION MODEL FOUNDATION COMPLETE WITH MINOR RESERVATIONS
```
