# Plan d'implémentation — Executive Decision Model (EDM)

Ce document remplace la section 6 (« Plan de mise en œuvre ») de `AUDIT_MCKINSEY_REFONTE.md` et intègre le correctif d'architecture validé par la direction technique. Aucune ligne de code n'a été écrite — ce document est soumis pour validation avant développement, conformément à la demande.

---

## 1. Principe d'architecture retenu

```
llm_service.py (Claude — raisonnement, synthèse, rédaction)
        ↓  dict brut (déjà existant aujourd'hui)
executive_decision_model.py  ← NOUVEAU — calcule, classe, formate, dérive
        ↓  ExecutiveDecisionModel (Pydantic, unique source de vérité)
────────────────────────────────────────────────────────────
export_pdf_service.py   → lit le modèle, ne calcule plus rien
export_pptx_service.py  → lit le modèle, ne calcule plus rien
excel_export.py         → (hors scope Phase 2, branché plus tard)
futur : dashboard / emails / Growth Brain / Copilot
```

Règle absolue : **aucune logique métier (calcul, tri, seuils, formules) ne doit se trouver dans `export_pdf_service.py` ou `export_pptx_service.py`.** Ces deux fichiers ne font que de la mise en page à partir d'objets déjà calculés.

`llm_service.py` n'est pas un export — c'est le moteur de raisonnement. Il continue à produire le dict brut qu'il produit déjà (V11). Le nouveau module `executive_decision_model.py` s'intercale juste après, avant les exports. Conformément à la Zero Rewrite Policy déjà appliquée sur ce projet : **un seul fichier neuf**, les fichiers existants ne sont pas réécrits, seulement complétés (prompt additif dans `llm_service.py`) ou adaptés point par point (accès aux données dans les builders d'export, sans toucher à la logique de mise en page qui fonctionne déjà).

---

## 2. Structure proposée de l'Executive Decision Model

Nouveau fichier `backend/models/executive_decision_model.py` (modèles Pydantic), construit par `backend/services/executive_decision_model.py` (fonction `build_executive_decision_model(result: dict) -> ExecutiveDecisionModel`).

```python
class CostOfInaction(BaseModel):
    par_an: Optional[float] = None
    par_mois: Optional[float] = None
    par_semaine: Optional[float] = None
    par_jour: Optional[float] = None
    par_heure: Optional[float] = None

class ValueDestroyer(BaseModel):
    nom: str
    impact_annuel: Optional[float] = None
    impact_mensuel: Optional[float] = None      # 🐍 dérivé
    pct_ca: Optional[float] = None               # 🐍 dérivé (si CA connu)
    tendance: Optional[str] = None               # "hausse" | "baisse" | "stable"
    commentaire: Optional[str] = None            # LLM

class TopDecision(BaseModel):
    decision: str
    impact_annuel: Optional[float] = None
    impact_mensuel: Optional[float] = None       # 🐍 dérivé
    difficulte: Optional[str] = None             # LLM (jugement qualitatif)
    delai: Optional[str] = None
    responsable: Optional[str] = None
    priorite: str                                # 🐍 dérivé (Haute/Moyenne/Faible)
    score_roi: float                              # 🐍 dérivé
    statut: str = "À lancer"                      # 🐍 défaut

class ExecutionItem(BaseModel):
    """Carnet d'exécution — remplace 'Analyse détaillée'."""
    decision: str
    responsable: Optional[str] = None
    impact: Optional[float] = None
    echeance: str                                  # 🐍 dérivé (aujourd'hui + horizon)
    difficulte: Optional[str] = None               # LLM
    score_roi: float                                # 🐍 dérivé
    statut: str = "À lancer"                        # 🐍 défaut
    date_revue: str                                 # 🐍 dérivé

class Phase90j(BaseModel):
    horizon: str            # "30" | "60" | "90"
    libelle_phase: str      # 🐍 "Stabiliser" / "Optimiser" / "Accélérer"
    actions: List[ExecutionItem]

class ExecutiveDecisionModel(BaseModel):
    # 1. Executive Summary
    ebitda: Optional[str] = None
    cash_disponible: Optional[str] = None
    score_sante: Optional[int] = None              # déjà existant (score_global)
    confiance_ia: Optional[int] = None              # déjà existant (score_confiance)
    decision_prioritaire: Optional[TopDecision] = None
    cout_inaction_resume: Optional[CostOfInaction] = None  # pour le bandeau

    # 2. CEO Dashboard
    ceo_dashboard: List[DashboardCard] = []          # déjà existant

    # 3. Destruction de valeur
    destructeurs: List[ValueDestroyer] = []

    # 4. Coût de l'inaction (page dédiée)
    cout_inaction: Optional[CostOfInaction] = None

    # 5. Top Decisions (tableau trié)
    top_decisions: List[TopDecision] = []

    # 6. Plan 90 jours (3 phases)
    plan_90_jours: List[Phase90j] = []

    # 7. Simulations avant/après
    scenarios: List[ScenarioCase] = []               # déjà existant
    serie_do_nothing: List[float] = []                 # 🐍 dérivé/interpolé
    serie_action: List[float] = []                     # 🐍 dérivé/interpolé

    # 8. Projection 6-12 mois
    projection_mensuelle: List[float] = []              # 🐍 dérivé/interpolé

    # 9. Carnet d'exécution
    carnet_execution: List[ExecutionItem] = []

    # 10. Note confidentielle du copilote
    note_copilote: Optional[str] = None               # LLM, nouveau champ cadré

    # 11. Page de suivi (statique + 1-2 faits calculés)
    prochaine_analyse_recommandee: Optional[str] = None  # 🐍

    # 12. Annexes & méthodologie
    data_quality: Optional[DataQualityInfo] = None      # déjà existant
```

---

## 3. Règles de calcul Python déterministes (remplacent toute demande au LLM)

Ces fonctions vivent dans `executive_decision_model.py`, nulle part ailleurs. Elles sont pures (entrée → sortie, aucun effet de bord) pour rester testables unitairement.

**Coût de l'inaction** — division simple de l'impact annuel déjà extrait :
```python
def compute_cost_of_inaction(impact_annuel: float) -> CostOfInaction:
    return CostOfInaction(
        par_an=impact_annuel,
        par_mois=impact_annuel / 12,
        par_semaine=impact_annuel / 52,
        par_jour=impact_annuel / 365,
        par_heure=impact_annuel / (365 * 24),
    )
```

**Priorité** — seuils fixes proposés (ajustables) :
```python
def compute_priorite(impact_annuel: float) -> str:
    if impact_annuel is None:
        return "Non évaluable"
    if impact_annuel >= 500_000:
        return "Haute"
    if impact_annuel >= 100_000:
        return "Moyenne"
    return "Faible"
```

**Score ROI** — composite impact / effort, sans inventer de coût de mise en œuvre (que nous n'avons pas) : on combine l'impact normalisé et la difficulté qualitative (seul élément que le LLM continue de fournir, car c'est un jugement, pas un calcul) :
```python
DIFFICULTE_WEIGHT = {"faible": 3, "moyenne": 2, "élevée": 1, "elevee": 1}

def compute_score_roi(impact_annuel: float, difficulte: str | None) -> float:
    poids = DIFFICULTE_WEIGHT.get((difficulte or "moyenne").lower(), 2)
    impact_norm = min((impact_annuel or 0) / 100_000, 10)  # plafonné à 10
    return round(impact_norm * poids / 3, 1)  # échelle ~0-10
```

**Libellé de phase** — mapping fixe sur l'horizon déjà présent (`PlanActionItem.horizon`) :
```python
PHASE_LABELS = {"30": "Stabiliser", "60": "Optimiser", "90": "Accélérer"}
```

**Échéance et date de revue** — dérivées de la date du jour + horizon :
```python
from datetime import date, timedelta

def compute_echeance(horizon_jours: int) -> str:
    return (date.today() + timedelta(days=horizon_jours)).strftime("%d/%m/%Y")
```

**Tri et classement** — `top_decisions` et `carnet_execution` sont triés par `impact_annuel` décroissant en Python ; le « score ROI global » de la page Top Decisions est la moyenne des `score_roi` individuels.

**% du CA** (destructeurs de valeur) — nécessite un seul nouveau fait extrait par le LLM : `chiffre_affaires_total` (une donnée brute déjà présente dans le fichier source, au même titre que Cash ou EBITDA déjà extraits dans CEO DASHBOARD — ce n'est pas un calcul, c'est une lecture de fait). Une fois ce fait connu :
```python
def compute_pct_ca(impact_annuel: float, ca_total: float | None) -> float | None:
    if not ca_total:
        return None
    return round(100 * impact_annuel / ca_total, 1)
```

**Statut par défaut** — toute nouvelle analyse initialise `statut = "À lancer"`. Aucune information sur l'avancement réel n'existe encore côté produit (pas de tracking d'exécution aujourd'hui) ; ce champ est un point d'extension pour une future fonctionnalité de suivi, pas une donnée que le LLM peut connaître.

**Tendance** (destructeurs de valeur) — si une analyse précédente existe pour la même entreprise (`decision_memory`), comparer l'impact actuel à l'impact précédent en Python (hausse/baisse/stable). Sinon, laisser `None` plutôt que de demander au LLM d'inventer une tendance sans historique. C'est un raffinement V2 — pour la Phase 2, `tendance` reste optionnel et n'est affiché que si calculable.

**Séries de simulation et de projection** — interpolation linéaire en Python entre le point de départ (situation actuelle, déjà connue) et le point d'arrivée (gain final déjà annoncé dans `scenarios[].impact` ou `projection_*`), sur 6 ou 12 points mensuels. Évite de demander au LLM des séries chiffrées détaillées (risque d'invention), tout en produisant un graphique crédible. Aucune nouvelle dépendance : ce sont de simples listes de `float`.

---

## 4. Ce qui change dans le prompt LLM (minimal, additif, jamais de suppression de garde-fou)

**Aucun nouveau champ pour** : priorité, statut, ROI, impact mensuel/hebdo/journalier/horaire, couleurs, classements, tri, phases. Tout cela est désormais interdit de prompt et calculé en Python (section 3).

**Un seul nouveau fait à extraire** dans la section existante `# CEO DASHBOARD` (ajout d'une ligne, pas une nouvelle section) :
```
💵 Chiffre d'affaires total : [montant€ ou "Données insuffisantes"]
```

**Une restructuration légère** de la section `# CE QUI DETRUIT` : au lieu d'une liste de puces libres, demander un format semi-structuré exploitable par un parseur simple (comme `_parse_quick_wins` le fait déjà pour les Quick Wins) :
```
# CE QUI DETRUIT
- [Nom du destructeur] | Impact annuel : [montant€] | Tendance : [hausse/baisse/stable/non applicable] | Commentaire : [1 phrase]
(max 5 lignes, triées par impact décroissant par Claude — le tri final reste recalculé en Python par sécurité)
```
C'est de l'extraction/synthèse (rôle légitime du LLM), pas un calcul.

**Une nouvelle section, cadrée strictement**, remplaçant l'idée de « Lettre du Copilote » :
```
# NOTE CONFIDENTIELLE DU COPILOTE FINANCIER
[Réponds à UNE seule question : "Si j'étais votre Directeur Financier lundi matin,
quelles seraient mes trois premières décisions ?" Ton direct, humain, professionnel,
niveau CFO. Maximum 200 mots, tient sur une page. AUCUN langage marketing, AUCUNE
formule de vente. Termine par "Pepperyn IA — Votre copilote financier".]
```
Ajoutée à la liste immuable de Call 2 (Call 2 ne doit jamais réécrire ce ton en neutre/marketing — règle déjà appliquée aux autres sections).

**Aucun changement** sur le Plan 30/60/90 (le LLM continue de fournir action/responsable/impact_attendu ; la priorité H/M/B est retirée du prompt et recalculée en Python à partir de l'impact).

**Aucun changement** sur `difficulte` (Quick Wins / Top Decisions) : c'est un jugement qualitatif sur la complexité de mise en œuvre, pas un calcul dérivable des chiffres — relève du raisonnement métier que le LLM peut légitimement fournir, conformément à la règle n°3 du correctif (« le LLM produit ce qu'un moteur déterministe ne peut pas produire »).

**Page de suivi** (« Comment Pepperyn continuera à vous accompagner ») : texte en grande partie statique/templated (pas de génération LLM par analyse), avec un seul élément calculé en Python (date de la prochaine analyse recommandée, ex. +30 jours). Pas de nouveau champ de prompt.

---

## 5. Nouvelle structure du PDF (12 sections, lit uniquement l'EDM)

1. Executive Summary — bandeau 4 KPI (EBITDA / Cash / Score santé / Confiance IA) + décision prioritaire géante + coût de l'inaction résumé (mois/jour)
2. CEO Dashboard
3. Destruction de valeur — tableau Top 5 (impact annuel/mensuel/% CA/tendance/commentaire)
4. Combien cela coûte — page dédiée (an/mois/semaine/jour/heure)
5. Top Decisions — tableau trié par impact, score ROI global affiché en tête
6. Plan d'action 90 jours — 3 phases (Stabiliser/Optimiser/Accélérer), priorité H/M/B
7. Simulation avant/après — double courbe DO NOTHING (rouge) vs ACTION (verte)
8. Projection & Trajectoire 6-12 mois — courbe + point de bascule
9. Carnet d'exécution — remplace « Analyse détaillée » (responsable/impact/échéance/difficulté/ROI/statut/date de revue)
10. Note confidentielle du Copilote Financier
11. Comment Pepperyn continuera à vous accompagner
12. Annexes & méthodologie

Les builders déjà écrits en Phase 1 (`_build_summary_scoreboard`, `_build_ceo_dashboard`, `_build_quick_wins`, `_build_plan_30_60_90`, `_build_scenarios`, `_score_table`, le pattern « capture-index / slice / réassemble ») sont **réutilisés tels quels** — seule leur source de données change : ils liront des attributs de l'`ExecutiveDecisionModel` au lieu de `result.get(...)`. C'est un changement d'accès aux données, pas une réécriture de la mise en page.

---

## 6. Nouvelle structure du PowerPoint (deck CODIR, 12-14 slides)

Philosophie : chaque slide = une idée projetable immédiatement, chiffres majeurs uniquement, aucun paragraphe.

1. Cover
2. Executive Summary (grille 2 cartes : Situation actuelle / Notre recommandation — déjà esquissé dans `ReportDemoSection.tsx`)
3. CEO Dashboard (4-6 KPI en grand)
4. Décision prioritaire n°1 (1 chiffre géant + 1 phrase)
5. Destruction de valeur (graphique barres horizontales, Top 5, pas de tableau dense)
6. Combien cela coûte (4 chiffres : an/mois/jour/heure)
7. Top Decisions (cartes ou mini-tableau, 5 lignes max)
8. Plan 90 jours (3 colonnes visuelles : Stabiliser/Optimiser/Accélérer)
9. Simulation avant/après (graphique natif `python-pptx`, 2 courbes)
10. Projection 6-12 mois (graphique natif, 1 courbe + point de bascule annoté)
11. Carnet d'exécution (tableau condensé, 5 lignes max)
12. Note confidentielle du Copilote (texte court, 1 slide, pas de paragraphe dense — extraits/puces courtes)
13. Comment Pepperyn continuera à vous accompagner
14. Slide de clôture / contact

Au moins les slides 5, 9 et 10 utilisent des graphiques natifs `python-pptx` (`CategoryChartData` + `XL_CHART_TYPE.LINE` ou `BAR_CLUSTERED`) — aucune nouvelle dépendance, la librairie est déjà installée (`python-pptx==1.0.2`).

---

## 7. Style des graphiques (PDF et PPTX)

Règle commune aux deux exports, appliquée dans des builders de graphique partagés (un seul jeu de fonctions, appelées par les deux services — par ex. `services/chart_helpers.py`, nouveau fichier, pour ne dupliquer la logique de style nulle part) :

- Jamais de camembert.
- Un graphique = une question = une réponse visuelle (ex. « Est-ce qu'agir change la trajectoire ? » → 2 courbes, rien d'autre).
- Palette sobre : `BLUE_DARK` (#0A2540) et `RED` (#DC2626) pour les comparaisons, `GREEN` pour les gains — déjà les couleurs de marque existantes, pas de nouvelle palette.
- Beaucoup d'espace blanc, pas de grille chargée, pas d'effets 3D/ombres.
- Axes minimalistes, étiquettes uniquement aux points clés (départ, fin, point de bascule).

---

## 8. Fichiers à créer / modifier (Zero Rewrite Policy)

**Nouveaux fichiers (3) :**
- `backend/models/executive_decision_model.py` — modèles Pydantic (section 2)
- `backend/services/executive_decision_model.py` — fonction `build_executive_decision_model()` + toutes les règles de calcul (section 3)
- `backend/services/chart_helpers.py` — builders de graphiques partagés PDF/PPTX (section 7)

**Fichiers complétés (additif uniquement, pas de réécriture) :**
- `backend/services/llm_service.py` — 1 ligne ajoutée à `# CEO DASHBOARD`, restructuration légère de `# CE QUI DETRUIT`, nouvelle section `# NOTE CONFIDENTIELLE DU COPILOTE FINANCIER`, mise à jour de la liste immuable de Call 2.
- `backend/models/schemas.py` — pas de nouveau champ business (tout vit dans le nouveau modèle EDM, pas dans `AnalysisResult`), sauf `chiffre_affaires_total: Optional[str]` si on préfère le stocker aussi sur `AnalysisResult` pour l'UI.

**Fichiers adaptés (accès aux données changé, mise en page conservée) :**
- `backend/services/export_pdf_service.py` — `generate_pdf_report()` appelle `build_executive_decision_model(result)` en première ligne, puis chaque section lit le modèle. Réordonnancement selon la section 5.
- `backend/services/export_pptx_service.py` — même principe, nouvelles fonctions `_slide_*` pour les slides manquantes (section 6), 2 builders de graphique appelés depuis `chart_helpers.py`.

**Fichier non touché dans cette phase :** `backend/services/excel_export.py` (hors scope, traité séparément comme déjà convenu).

---

## 9. Séquencement proposé

1. **Étape A — Modèle de données** : créer les 2 nouveaux fichiers (modèles + builder), avec tests unitaires sur les fonctions de calcul (coût inaction, priorité, score ROI, échéance) — aucune dépendance sur le LLM, testable immédiatement avec des données synthétiques.
2. **Étape B — Prompt LLM** : ajouter le fait `chiffre_affaires_total`, restructurer `# CE QUI DETRUIT`, ajouter `# NOTE CONFIDENTIELLE DU COPILOTE FINANCIER`, mettre à jour la liste immuable Call 2. Smoke test du parsing (comme pour le V11).
3. **Étape C — PDF** : brancher `export_pdf_service.py` sur l'EDM, réordonner les 12 sections, ajouter les 2 graphiques (`chart_helpers.py`). Smoke test PDF complet (comme Phase 1 : génération réelle + extraction `pdfplumber` + vérification de l'ordre des sections).
4. **Étape D — PPTX** : ajouter les slides manquantes, brancher sur l'EDM, ajouter les graphiques natifs. Smoke test PPTX (ouverture avec `python-pptx`, vérification du nombre de slides et de la présence des graphiques).
5. **Étape E — Vérification finale** : `tsc` côté frontend si des champs sont consommés par l'UI (aperçu rapport dans le chat), relecture visuelle des deux exports, commit isolé par étape (comme pour tout le reste du projet).

---

## 10. Compatibilité long terme

L'`ExecutiveDecisionModel` est conçu pour être consommé tel quel par :
- un futur **Dashboard interactif** (sérialisation JSON directe du modèle, aucune logique à dupliquer) ;
- des **emails automatiques** (un sous-ensemble de champs du modèle, ex. juste `decision_prioritaire` + `cout_inaction`) ;
- le **reporting mensuel** (le modèle est déjà conçu autour d'une cadence d'analyse périodique — section 11 « page de suivi ») ;
- le futur **Growth Brain** (déjà cadré comme module séparé, `GROWTH_BRAIN_ENABLED=false` par défaut, sans dépendance inverse vers l'EDM — l'EDM reste un module du cœur produit, pas du Growth Brain) ;
- un futur **Copilot conversationnel** (le modèle structuré est directement injectable dans un prompt de chat, sans repasser par du texte libre).

Aucun de ces canaux futurs n'aura besoin de réécrire la logique de calcul : elle vit une seule fois dans `executive_decision_model.py`.

---

## 11. Risques

- Le passage de `result.get(...)` à un accès typé (`model.section.field`) dans `export_pdf_service.py`/`export_pptx_service.py` touche beaucoup de lignes même si la mise en page ne change pas — risque de régression mécanique (faute de frappe sur un nom de champ). Mitigation : smoke test PDF/PPTX systématique après chaque section migrée, comme en Phase 1.
- Les seuils de priorité (500k€/100k€) et la formule de score ROI sont une proposition raisonnable mais arbitraire — à valider ou ajuster une fois testés sur de vraies analyses.
- `% du CA` dépend d'un nouveau fait LLM (`chiffre_affaires_total`) qui peut être absent ou peu fiable sur des documents incomplets — le champ doit rester optionnel partout en aval (déjà prévu dans le modèle).
- La restructuration de `# CE QUI DETRUIT` change le format texte que Call 2 doit vérifier — il faut mettre à jour ses règles immuables en même temps, sinon Call 2 risque de « corriger » le nouveau format vers l'ancien.
- Les graphiques natifs PPTX sont plus limités stylistiquement que PowerPoint ouvert nativement — prévoir un rendu volontairement simple plutôt que d'essayer de forcer un style trop élaboré.
- Le Carnet d'exécution introduit la notion de `statut`, qui n'a aujourd'hui aucune mécanique de mise à jour (pas de bouton « marquer comme fait »). Le champ est inclus dans le modèle pour ne pas bloquer une future fonctionnalité de suivi, mais reste figé à « À lancer » tant que cette fonctionnalité n'existe pas — à clarifier si une UI de suivi est attendue dans cette même phase ou plus tard.
