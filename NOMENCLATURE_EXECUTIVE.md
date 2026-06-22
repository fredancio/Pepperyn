# Nomenclature officielle Pepperyn — Executive Narrative

Convention d'architecture validée par la direction technique. S'applique à partir de l'Executive Narrative (au-dessus de l'Executive Decision Model, adopté à l'Étape A).

## Règle générale

**Langage interne** (code, modèles, classes, champs, marqueurs de prompt, documentation technique) → **anglais**, vocabulaire « Executive » systématique.

**Langage visible par l'utilisateur** (landing page, rapports destinés aux dirigeants francophones, UI) → **français naturel, orienté métier**, sans anglicisme.

Cette séparation prépare une future internationalisation sans jamais avoir à réécrire la logique : seul l'habillage (libellés) change selon la langue cible.

## Glossaire de référence

| Terme interne (anglais, code) | Terme visible (français, client) |
|---|---|
| Executive Decision | Décision prioritaire |
| Executive Summary | Résumé exécutif |
| Executive Priorities | Priorités d'action |
| Executive Confidence | Niveau de confiance |
| Executive Report | Rapport exécutif |
| Executive Board Deck | Présentation Comité de Direction |
| Executive Financial Model | Modèle financier interactif |
| Executive Narrative | (terme interne uniquement — pas de traduction visible, c'est un concept d'architecture) |

## Structure de l'Executive Narrative (ordre canonique, immuable)

Tous les exports (PDF, PowerPoint, futurs Dashboard/Email/Copilot) suivent cet ordre. Aucun export ne réorganise ses propres sections.

1. **Executive Decision** — la décision la plus importante, seule, présentée de façon très visuelle. Le dirigeant doit la comprendre en moins de 10 secondes. Remplace l'ancienne page d'ouverture « Executive Summary ».
2. **Executive Summary** — bandeau de KPI (EBITDA, Cash, Health Score, Executive Confidence).
3. **Business Context** — secteur, modèle économique, taille de l'entreprise (donnée de profil, pas d'analyse).
4. **Financial Impact** — destructeurs de valeur + coût de l'inaction.
5. **Executive Decisions** — tableau des décisions prioritaires triées par impact (anciennement « Top Decisions »).
6. **Strategic Levers** — leviers de croissance/structurels.
7. **Execution Roadmap** — plan 90 jours + carnet d'exécution.
8. **Future Projection** — scénarios avant/après + trajectoire 6-12 mois.
9. **Executive Follow-up** — page de suivi (non commerciale).
10. **Confidential Copilot Note** — note confidentielle du copilote financier.

(Les Annexes & méthodologie restent une section technique en fin de document, hors narration principale.)

## Règle « visibilité IA » (enregistrée maintenant, appliquée à l'Étape C uniquement)

**Ne pas modifier de texte visible pendant les Étapes A et B.** Cette règle est documentée par anticipation ; son application concrète n'aura lieu qu'au moment de la refonte des exports (Étape C).

Principe : *le client n'achète pas une IA, il achète un copilote financier qui l'aide à prendre de meilleures décisions.*

À l'Étape C, dans tous les livrables (Executive Report, Executive Board Deck, Executive Financial Model) :
- réduire fortement les occurrences du terme « IA » ;
- ne conserver « IA » que lorsqu'il est indispensable pour expliquer un mécanisme technique ou un niveau de confiance ;
- privilégier : recommandations, décisions, analyse, copilote financier, diagnostic, plan d'action, trajectoire, pilotage, projection.

Instances déjà identifiées dans `export_pdf_service.py` (non modifiées à ce stade, à corriger à l'Étape C) :
- en-tête de page : *« Analyse IA · Niveau expert »*
- bloc fiabilité : *« Confiance analyse IA »*, *« Qualité du raisonnement IA »*

## Statut d'application (gel des périmètres en cours)

- **Executive Decision Model** (`backend/models/executive_decision_model.py`, `backend/services/executive_decision_model.py`) : renommé selon cette convention dès maintenant (fichiers internes, non encore consommés ailleurs — aucun risque de régression externe).
- **`models/schemas.py`** (`QuickWin`, `PlanActionItem`, etc.) : **non renommé pour l'instant** — ces classes sont consommées par `export_pdf_service.py` et `export_pptx_service.py`, eux-mêmes non encore modifiés (Étapes A/B). Le renommage interviendra naturellement à l'Étape C/D quand ces fichiers seront ouverts.
- **Frontend** (landing page, FAQ, boutons d'export) : **non retouché**. Le vocabulaire français déjà shippé reste tel quel ; il sera vérifié/aligné sur ce glossaire seulement si une future tâche le demande explicitement.
- **Exports actuels** (PDF/PPTX/Excel) : aucun texte visible modifié avant l'Étape C.

## Écarts identifiés par rapport à l'Étape A (à corriger dans le refactor de l'EDM)

- `leviers_croissance` existe dans le dict brut produit par `llm_service.py` mais n'avait pas été repris dans l'EDM à l'Étape A → ajouté comme `strategic_levers`.
- `Business Context` n'a aucune source de données dans l'EDM aujourd'hui (c'est une donnée de profil entreprise, pas une donnée d'analyse). Un champ `business_context` est prévu dans le modèle mais reste `None` tant que cette source n'est pas branchée — décision à prendre séparément (hors scope Étape B).
