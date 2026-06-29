# PEPPERYN — AUDIT VALEUR PERÇUE MVP
**Perspective : CEO / CFO / Membre du Conseil d'Administration**
**Version 1.0 — Juin 2026**
**Statut : Plan de bataille commercial — Aucune implémentation**

---

## CONTEXTE DE L'AUDIT

Cet audit ne répond pas à la question "Qu'est-ce qui manque dans le code ?".
Il répond à la question : **"Pourquoi un CEO déciderait-il de garder Pepperyn après avoir vu ses trois livrables ?"**

La grille d'évaluation est celle d'un dirigeant sous pression temporelle, pas celle d'un ingénieur. Un CEO lit un rapport en 4 minutes. Un CFO cherche immédiatement les chiffres. Un membre du CA évalue si le contenu est présentable à des tiers.

**Constat préliminaire important :** Le modèle de données ExecutiveCaseJSON est remarquablement riche. Les champs `cost_of_inaction`, `tension_phrase`, `structural_loss_statement`, `urgency_level`, `value_creation_statement`, `inaction_risk` existent tous. Ce n'est pas un problème de données manquantes. C'est un problème de mise en scène. Les munitions existent. Elles ne sont pas encore tirées au bon endroit, dans le bon ordre, avec la bonne force.

---

## LES 10 AMÉLIORATIONS CLASSÉES PAR IMPACT COMMERCIAL

---

### #1 — LE COÛT DE L'INACTION COMME PREMIER CHIFFRE VU

**Le problème (perspective CEO)**

Un CEO ouvre le PDF. Il voit la cover, puis une page dense de KPIs, puis les destructeurs, puis les décisions. À quel moment ressent-il l'urgence d'agir ? Probablement jamais, ou trop tard dans le document.

Le champ `cost_of_inaction.monthly` existe dans le modèle. C'est le chiffre le plus puissant que Pepperyn possède. Il transforme une analyse en une menace quantifiée.

**La correction**

En ouverture du PDF (page 2 ou bandeau de la cover) et en slide d'accroche du PPTX, afficher un seul chiffre en très grand format :

> *"Chaque mois d'inaction coûte actuellement **X €** à [Entreprise]."*

Ce chiffre doit être le premier chiffre qu'un CEO voit. Pas le health score. Pas le confidence score. Le coût de ne rien faire.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★★ — Crée l'urgence immédiate. Un CEO qui voit -83K€/mois ne referme pas le document. |
| **Coût technique** | Très faible — `cost_of_inaction.monthly` existe. Repositionnement visuel uniquement. |
| **Risque de régression** | Faible — Ajout d'un élément visuel, rien de supprimé. |
| **Priorité** | **P0 — Premier sprint commercial** |

---

### #2 — UN CEO ONE-PAGER DÉTACHABLE (PAGE 2 DU PDF)

**Le problème (perspective CEO)**

Un CEO lit 4 minutes. S'il trouve quelque chose de valeur, il le transfère à son CFO ou à son DG. Aujourd'hui, il n'existe aucune page du PDF qui puisse être extraite et partagée en l'état.

**La correction**

La page 2 du PDF (immédiatement après la cover) devient le CEO One-Pager. Elle contient exactement et uniquement :

1. La `tension_phrase` — la formulation-choc de la situation en une ligne
2. Trois chiffres-héros : situation actuelle / valeur en jeu / coût d'inaction mensuel
3. Les 2-3 décisions prioritaires — libellé + impact annuel + timeline
4. Une ligne : "Votre prochaine action d'ici vendredi : [action concrète]"

Cette page est conçue pour être photographiée et envoyée par WhatsApp à l'équipe de direction.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★★ — C'est la page qui circule. C'est la page qui vend Pepperyn à d'autres dirigeants. |
| **Coût technique** | Moyen — Nouvelle page PDF à builder. Toutes les données existent déjà. |
| **Risque de régression** | Faible — Page additionnelle, rien de retiré. |
| **Priorité** | **P0 — Premier sprint commercial** |

---

### #3 — LA COHÉRENCE NARRATIVE PARFAITE ENTRE LES TROIS LIVRABLES

**Le problème (perspective Conseil d'Administration)**

Un CEO reçoit les trois documents. Il lit la décision #1 dans le PDF : "Provisionner et liquider le stock obsolète avant la clôture de septembre." Il ouvre le PPTX. La même décision est formulée légèrement différemment. Il ouvre l'Excel. Le chiffre associé est présenté différemment.

Chaque incohérence, même mineure, déclenche la même pensée chez un Board member : *"Si le texte n'est pas cohérent, les chiffres le sont-ils ?"* La confiance s'effondre avant même la première question.

**La correction**

Garantir que les libellés exacts des décisions, les noms exacts des destructeurs, et les chiffres clés soient identiques mot pour mot dans les trois renderers. ExecutiveCaseJSON est déjà la source unique de vérité (RULE en place). Audit des templates pour s'assurer qu'aucun renderer ne reformule, ne tronque, ne paraphrase.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★★ — Une incohérence détruit instantanément la crédibilité. La cohérence est la crédibilité. |
| **Coût technique** | Faible à moyen — Audit des trois renderers, pas de nouveau code métier. |
| **Risque de régression** | Moyen — Toute modification d'un renderer doit être vérifiée dans les deux autres. |
| **Priorité** | **P0 — Premier sprint commercial** |

---

### #4 — LE RAISONNEMENT EN PREMIER, LES CHIFFRES EN SUPPORT

**Le problème (perspective CEO)**

EDX-001 a implémenté le raisonnement exécutif. Mais dans la page Décisions du PDF, le raisonnement apparaît *après* le tableau des décisions. Un CEO lit dans l'ordre : tableau → raisonnement. Ce n'est pas l'ordre d'un conseil stratégique. C'est l'ordre d'un rapport d'analyse.

Un conseil stratégique dit : *"Voici pourquoi vous devez agir maintenant. Voici l'impact. Voici ce qu'il en coûte de ne pas agir."* Les chiffres viennent confirmer, pas précéder.

**La correction**

Pour chaque décision dans les trois livrables, l'ordre d'affichage devient :

1. **Pourquoi maintenant** (`why_this_decision`) — le raisonnement causal
2. **L'action recommandée** (`decision`) — la décision
3. **L'impact** (`annual_impact`) — ce que ça rapporte
4. **Le risque d'inaction** (`inaction_risk`) — ce qu'il en coûte de différer
5. **La confiance** (`decision_confidence`) — la solidité de la recommandation

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★☆ — Transforme une liste d'actions en livrable de conseil. Le CEO lit comme s'il écoutait un Partner McKinsey. |
| **Coût technique** | Moyen — Restructuration de l'affichage des décisions dans les trois renderers. |
| **Risque de régression** | Moyen — Modification de la page la plus critique du PDF et de la slide principale du PPTX. |
| **Priorité** | **P1 — Deuxième sprint commercial** |

---

### #5 — LE LANGAGE DU DIRIGEANT, PAS DE L'ANALYSTE

**Le problème (perspective CEO)**

"Value Destroyer." "DSO." "BFR." "Score de confiance Pepperyn." Ces termes créent une distance imperceptible mais réelle avec un CEO non-financier. Ils signalent : *"Ce document a été produit par un algorithme."* À l'inverse, un consultant senior utilise le vocabulaire que le CEO emploie dans ses propres réunions.

**La correction**

Dans les renderers, remplacer les labels génériques par le registre d'un directeur financier senior :
- "Value Destroyer" → "Facteur de destruction de valeur" ou directement le nom métier
- "Score de confiance : 83%" → "Recommandation fondée sur X mois de données — Fiabilité élevée"
- "DSO" → conserver pour les CFO, mais ajouter en sous-titre "délai moyen de paiement client"
- Les titres de sections → reformuler en verbes d'action et en enjeux, pas en catégories analytiques

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★☆ — Le langage est la première preuve de compréhension. Un CEO qui reconnaît son propre vocabulaire fait davantage confiance au diagnostic. |
| **Coût technique** | Faible — Ajustements des labels dans les renderers et dans les prompts LLM. |
| **Risque de régression** | Faible — Modifications de surface, aucune logique métier touchée. |
| **Priorité** | **P1 — Deuxième sprint commercial** |

---

### #6 — LE PPTX VRAIMENT PRÉSENTABLE AU CONSEIL D'ADMINISTRATION

**Le problème (perspective Membre du CA)**

Le Board Deck existe. Mais est-ce qu'un Directeur Général peut ouvrir le fichier, passer à la slide suivante, et la présenter à ses administrateurs sans aucune modification préalable ?

Deux défauts structurels d'un Board Deck non-pensé pour la présentation : (1) les titres de slides décrivent le contenu au lieu d'annoncer la conclusion, et (2) il n'y a pas de notes de présentateur pour guider l'oral.

**La correction**

Deux modifications ciblées :

**Titres de slides → conclusions** : au lieu de "Les Décisions Prioritaires", écrire "Trois décisions qui libèrent 920 K€ en 90 jours." Le titre dit ce que le CEO doit retenir, pas ce que la slide contient.

**Notes de présentateur** : chaque slide du PPTX reçoit 2-3 phrases de notes. Ce que le présentateur doit dire à voix haute, les chiffres à citer, la transition vers la slide suivante. Ces notes sont générées par le LLM à partir du contenu du JSON.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★☆ — Un CEO qui présente Pepperyn à son CA devient un ambassadeur actif du produit. C'est le meilleur vecteur d'acquisition. |
| **Coût technique** | Moyen — Notes de présentateur via LLM + reformulation des titres de slides. |
| **Risque de régression** | Faible — Additions, rien de retiré. |
| **Priorité** | **P1 — Deuxième sprint commercial** |

---

### #7 — LA PROCHAINE ACTION DANS LES 7 JOURS

**Le problème (perspective CEO)**

Un CEO lit le rapport. Il est convaincu. Il referme le PDF. Deux heures plus tard, il est dans une autre réunion. Le lundi matin, l'urgence du quotidien reprend. Rien ne s'est passé.

La friction entre la lecture d'un livrable et le premier geste d'implémentation est le principal ennemi du ROI d'un rapport de conseil.

**La correction**

En dernière page du PDF et en dernière slide du PPTX, un encadré unique :

> **Votre prochaine action d'ici vendredi**
> [Action très concrète, formulée avec un verbe, un nom, et un délai]
> *Exemple : "Convoquer DAF + Directeur Logistique pour valider le plan de liquidation du stock avant le 15 juillet."*

Une ligne. Un verbe. Un responsable. Une date.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★☆ — Réduit la friction entre lecture et action. Un CEO qui agit dans les 7 jours devient un utilisateur récurrent. |
| **Coût technique** | Faible — Nouveau champ LLM + affichage dans les renderers PDF et PPTX. |
| **Risque de régression** | Faible — Ajout en fin de document, rien de déplacé. |
| **Priorité** | **P1 — Deuxième sprint commercial** |

---

### #8 — L'EXCEL COMME OUTIL DE SIMULATION, PAS DE REPORTING

**Le problème (perspective CFO)**

Un CFO ouvre l'Excel. Il voit les données présentées proprement. Il cherche immédiatement à tester une hypothèse : *"Et si j'améliorais le DSO de 87j à 65j au lieu de 55j ? Quel serait l'impact ?"* Aujourd'hui, il ne peut pas. Il ferme l'Excel.

Le CFO est souvent le sponsor économique de Pepperyn dans une organisation. Si l'Excel ne l'engage pas activement, Pepperyn reste un outil pour le CEO seulement.

**La correction**

Dans la feuille Scénarios, 3 à 5 cellules d'hypothèses modifiables (surlignées en bleu selon le standard financier). Chaque modification recalcule en cascade : impact sur le BFR, sur l'EBITDA, sur la trésorerie projetée. Pas un modèle complet — uniquement les leviers issus des décisions prioritaires.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★★☆ — Un CFO qui simule dans l'Excel devient co-auteur du plan d'action. L'adhésion interne est garantie. |
| **Coût technique** | Élevé — Logique de simulation à builder dans excel_export.py. Formules Excel conditionnelles. |
| **Risque de régression** | Moyen — Feuille existante modifiée substantiellement. Tests nécessaires. |
| **Priorité** | **P2 — Troisième sprint commercial** |

---

### #9 — LA CONFIANCE TRADUITE EN PREUVES, PAS EN POURCENTAGE

**Le problème (perspective CEO)**

"Confiance Pepperyn : 83%." Un CEO expérimenté se pose immédiatement la question : *"83% basé sur quoi ?"* Sans réponse, le pourcentage paraît arbitraire, voire généré aléatoirement.

**La correction**

Remplacer "83%" par une formulation qui expose la méthode :

> *"Recommandation de haute fiabilité — Fondée sur 18 mois de données, 4 indicateurs convergents, aucune anomalie structurelle détectée."*

Ou sous forme courte dans les tableaux :
> *Fiabilité : Élevée (18 mois · 4 signaux · 0 anomalie)*

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★☆☆ — Renforce la confiance dans la méthodologie. Transforme un score en argument vérifiable. |
| **Coût technique** | Faible — Reformulation dans les renderers. Les données sources existent déjà (data_quality, anomalies). |
| **Risque de régression** | Faible — Modification de surface. |
| **Priorité** | **P2 — Troisième sprint commercial** |

---

### #10 — L'INVITATION À PROGRESSER (DATA QUALITY → NEXT SESSION)

**Le problème (perspective CEO)**

Le score de qualité des données (81/100 pour Optilux) est affiché. Un CEO voit ce score et ne sait pas quoi en faire. Il n'a pas les clés pour l'améliorer.

**La correction**

Transformer le score en appel à l'action pour la prochaine session :

> *"Pour affiner votre prochain diagnostic et porter votre score de fiabilité à 95+, Pepperyn recommande de fournir : [liste des 3 données les plus impactantes manquantes]."*

Ce n'est pas un reproche sur la qualité des données. C'est une invitation à construire une relation continue.

| Dimension | Évaluation |
|---|---|
| **Impact commercial** | ★★★☆☆ — Ancre Pepperyn dans une logique de partenariat continu, pas d'analyse ponctuelle. Réduit le churn. |
| **Coût technique** | Faible — Conditionnel sur les anomalies déjà identifiées dans `data_quality.anomalies`. |
| **Risque de régression** | Faible — Ajout en fin de document. |
| **Priorité** | **P3 — Quatrième sprint commercial** |

---

## PLAN DE BATAILLE — SÉQUENÇAGE RECOMMANDÉ

### Sprint Commercial 1 — "L'urgence visible" (P0)
*Objectif : Un CEO comprend en 30 secondes pourquoi il ne peut pas attendre.*

| # | Amélioration | Impact | Coût |
|---|---|---|---|
| 1 | Coût de l'inaction en premier chiffre | ★★★★★ | Très faible |
| 2 | CEO One-Pager détachable | ★★★★★ | Moyen |
| 3 | Cohérence narrative parfaite entre les 3 livrables | ★★★★★ | Faible |

---

### Sprint Commercial 2 — "La voix du conseil" (P1)
*Objectif : Un CEO partage les livrables avec son équipe sans modification.*

| # | Amélioration | Impact | Coût |
|---|---|---|---|
| 4 | Raisonnement en premier, chiffres en support | ★★★★☆ | Moyen |
| 5 | Langage du dirigeant, pas de l'analyste | ★★★★☆ | Faible |
| 6 | PPTX Board-ready avec notes de présentateur | ★★★★☆ | Moyen |
| 7 | Prochaine action dans les 7 jours | ★★★★☆ | Faible |

---

### Sprint Commercial 3 — "L'adhésion du CFO" (P2)
*Objectif : Le CFO devient sponsor économique de Pepperyn.*

| # | Amélioration | Impact | Coût |
|---|---|---|---|
| 8 | Excel simulation CFO (3-5 leviers actionnables) | ★★★★☆ | Élevé |
| 9 | Confiance traduite en preuves, pas en pourcentage | ★★★☆☆ | Faible |

---

### Sprint Commercial 4 — "La relation longue durée" (P3)
*Objectif : Pepperyn devient un partenaire récurrent, pas un rapport ponctuel.*

| # | Amélioration | Impact | Coût |
|---|---|---|---|
| 10 | Invitation à progresser → next session | ★★★☆☆ | Faible |

---

## VERDICT D'AUDIT

**Ce qui fonctionne aujourd'hui :** L'architecture de données est solide. ExecutiveCaseJSON contient tous les éléments d'un livrable de conseil senior — `tension_phrase`, `cost_of_inaction`, `structural_loss_statement`, `inaction_risk`, `decision_reasoning`. La matière première existe.

**Ce qui manque :** La mise en scène. Les données les plus puissantes ne sont pas au premier plan. L'ordre de lecture ne crée pas l'urgence. Le langage reste parfois analytique là où il devrait être directif.

**La correction est moins coûteuse que ce qu'elle paraît :** 7 des 10 améliorations ont un coût technique faible à moyen. Elles ne nécessitent pas de nouveau moteur cognitif, pas de nouveau modèle de données, pas de nouvelle infrastructure. Elles nécessitent de repositionner ce qui existe déjà au bon endroit, dans le bon ordre, avec le bon registre.

**La question de contrôle pour chaque sprint :**
> *"Après avoir lu ce livrable pendant 4 minutes, un CEO en difficulté sait-il exactement quoi faire demain matin ?"*

Si la réponse est non, le sprint n'est pas terminé.

---

*Audit rédigé en juin 2026.*
*Perspective : CEO / CFO / Membre du Conseil d'Administration.*
*Aucune ligne de code. Plan de bataille orienté valeur client.*
