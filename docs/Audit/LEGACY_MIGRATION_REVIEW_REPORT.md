# LEGACY_MIGRATION_REVIEW_REPORT.md

**Nature :** Missions 8, 9 et clôture (Mission 10). Synthèse et verdict final de la Legacy Capability Preservation & Migration Review. Aucun code modifié.

---

## Mission 8 — Frontières UI

La proposition initiale (conserver sidebar/header/settings/compte/abonnements/historique/gestion des organisations/chrome générique ; faire évoluer le contenu central) est globalement saine, mais elle répète l'imprécision déjà relevée sur l'Article XX Shell Stability Principle (tour précédent de cette session) : elle classe « historique » et « gestion des organisations » comme du chrome, alors que ce sont, à des degrés variables, des capacités qui portent du sens métier.

Distinction affinée, par capacité :

- **Chrome générique stable, réellement Shell** : sidebar, header, boutons génériques, système de design. Aucune ambiguïté — confirmé par le code, ces éléments ne connaissent rien du Domain.
- **Composition d'écran spécifique au Domain, à ne jamais figer par la règle de stabilité Shell** : la disposition du Portefeuille (cockpit, bandeau « Aujourd'hui »), la structure d'un Review Briefing, la présentation d'un dossier dans le chat — tout cela s'exprime visuellement à l'intérieur du chrome, mais la décision de composition appartient au Domain. Geler ces compositions au nom de la stabilité du Shell serait exactement l'erreur que la réserve posée sur l'Article XX anticipait.
- **Capacité de sécurité transversale, à sortir de la discussion Shell/Domain et à rattacher à Trust & Platform** : anonymisation (déjà traitée), isolation inter-organisations des tables de correspondance et des caches en mémoire (`_anonymization_cache`, `_export_cache`, `_analysis_result_cache` — tous identifiés dans `LEGACY_CAPABILITY_INVENTORY.md` comme partageant la même fragilité d'isolation multi-instance).
- **Vocabulaire à harmoniser, ni Shell ni Domain, juste une dette de nommage** : « historique » (terme Shell générique) recouvre en réalité deux capacités distinctes de nature différente — l'historique d'analyses (mécanique, proche Shell) et la mémoire décisionnelle (`decision_memory.py`, contenu métier, clairement Domain). Le mot unique masque la frontière réelle ; à corriger dans le vocabulaire avant qu'une règle de stabilité ne s'applique par erreur à la mauvaise moitié.
- **Comportement qui doit être remplacé, pas seulement composé différemment** : le Chat V2 tel qu'audité (Mission 6) — ce n'est pas un problème de frontière UI, c'est un problème de frontière de sortie de données (Trust & Platform), qui ne se résout pas en déplaçant du composant dans l'interface.

**Principe retenu pour éviter qu'une règle de stabilité Shell bloque une évolution Domain légitime :** la règle de stabilité doit s'appliquer au *contrat visuel* (où sont le header, la sidebar, les actions génériques) jamais au *contenu* qui s'affiche à l'intérieur de ce contrat. Une capacité Domain peut changer sa composition interne sans jamais être bloquée par l'Article XX, tant qu'elle ne redéfinit pas elle-même la navigation globale ou le chrome partagé.

---

## Mission 9 — Risque de conservatisme de l'élimination progressive

La stratégie de préservation sélective (strangler fig) a un vrai risque, illustré concrètement par ce qui vient d'être trouvé dans le code, pas seulement en théorie :

- **Maintenir deux modèles concurrents sans le savoir** : `financial_truth.py` (dormant) et `Evidence Ledger` (T1, non fusionné) sont déjà deux registres de vérité financière distincts — le Foundation Recovery Sprint avait déjà posé la garantie de ne jamais les faire converger silencieusement. `temporal_normalizer.py`, découvert dans cette mission, ouvre un risque équivalent avec le futur FTE, non résolu.
- **Créer des chemins de sécurité parallèles** : c'est exactement ce que l'audit de l'anonymisation vient de démontrer — le chemin legacy du chat anonymise, le chemin V2 préféré ne le fait pas. Deux chemins vers le même LLM, avec deux garanties différentes, est la définition même du risque que Mission 9 demande d'identifier.
- **Augmenter la dette en attendant la bonne occasion** : les caches en mémoire (`_export_cache`, `_analysis_result_cache`, `_anonymization_cache`, `rate_limiter`) forment une famille de dette homogène — tous partagent la même fragilité (non-persistance, non-partage multi-instance) mais aucun n'a été traité comme un chantier unique parce que chacun a été découvert dans un contexte différent (export, chat, anonymisation, anti-abus). Une conservation capacité-par-capacité, sans vue d'ensemble, risque de résoudre ces quatre cas séparément, quatre fois, au lieu d'une fois.
- **Empêcher une simplification nécessaire** : la coexistence du chemin de chat legacy et V2 illustre ce risque directement — conserver les deux « au cas où » retarde la décision de faire du V2 le seul chemin, ce qui serait la vraie simplification, mais qui suppose d'abord de corriger sa faille d'anonymisation (séquence : corriger avant de trancher, pas trancher pour éviter de corriger).

**Critères de bascule vers une suppression franche, plutôt que la préservation progressive :**
1. Le mécanisme legacy est un chemin de sécurité parallèle actif au mécanisme cible (pas seulement redondant en fonctionnalité, mais divergent en garantie) — cas du chat V2/legacy.
2. Le coût de maintenir la coexistence dépasse, de façon démontrable, le coût de la migration complète en une fois (mesurable seulement une fois les deux chemins pleinement inventoriés — pas encore le cas ici pour tout sauf le chat).
3. Le mécanisme legacy n'a plus aucun consommateur réel identifiable — alors la préservation progressive n'a plus d'objet, RETIRE s'applique directement sans étape intermédiaire.
4. Le maintien du legacy empêche de corriger une faille de sécurité déjà prouvée — c'est le cas précis du chat V2 : la coexistence des deux chemins n'est pas neutre, elle retarde la correction du contournement d'anonymisation documenté en Mission 6.

---

## Mission 10 — Synthèse

**Livrables produits :** `LEGACY_CAPABILITY_PRESERVATION_POLICY.md`, `LEGACY_CAPABILITY_INVENTORY.md`, `LEGACY_CAPABILITY_REVIEW_MATRIX.md`, `ANONYMIZATION_CAPABILITY_REVIEW.md`, ce rapport, et — mission complémentaire — `STRATEGIC_DEFERRED_WORK_REGISTER.md`.

**Ce que cette revue a changé par rapport à ce qu'on croyait savoir :** le modèle Shell/Domain, présenté au tour précédent comme une distinction élégante et globalement suffisante, s'avère insuffisant sans une troisième discipline explicite (Trust & Platform) pour les capacités qui gardent une frontière de sortie de données — la preuve n'est pas conceptuelle, elle est dans le code : quatre sites d'appel LLM ont chacun pris indépendamment une décision d'anonymisation différente, dont deux incorrectes.

**Ce qui est plus grave qu'attendu :** le chemin de chat aujourd'hui préféré (Conversation Engine V2) envoie l'essentiel du contenu sensible d'un dossier en clair à chaque tour de conversation — un écart concret entre la promesse de confidentialité affichée publiquement et le comportement réel du code.

**Ce qui reste non résolu, nommément :** le statut de `temporal_normalizer.py` face à la doctrine FTE ; le possible doublon entre `feedback.py` et `decision_memory.py` ; l'endroit réel où les fichiers uploadés sont stockés (non identifié cette session) ; la couverture d'anonymisation de `decision_rules.py`, `executive_decision_model.py`, `file_parser.py`, `financial_normalizer.py`, non auditée avec la même profondeur que les quatre chemins déjà traités.

```
LEGACY CAPABILITY PRESERVATION REVIEW COMPLETED.

FINAL VERDICT:
B — SELECTIVE PRESERVATION VALID WITH NAMED RESERVATIONS
```

Ni A (les contournements d'anonymisation prouvés par le code, en particulier sur le chat V2, ne permettent pas d'affirmer que la migration peut procéder sans réserve) ni C (rien ne démontre que l'architecture legacy dans son ensemble est inadéquate — le mécanisme d'anonymisation Layer 1 est correct, le modèle Company/Entity est sain, la majorité des capacités inventoriées obtiennent KEEP sans réserve). Les réserves sont nommées, localisées dans le code, et hiérarchisées par risque — pas des doutes diffus.

---

**LEGACY CAPABILITY PRESERVATION REVIEW COMPLETED.**

**FINAL VERDICT:**
**B — SELECTIVE PRESERVATION VALID WITH NAMED RESERVATIONS**
