# Audit d'écart — Refonte « niveau McKinsey » (PDF + PPTX)

Comparaison entre le visuel fourni (12 exigences) et l'état réel du code après le Phase 1 du manifeste exécutif (commit `8f77061`). Aucune ligne de code n'a été modifiée pour produire ce document.

Légende : ✅ déjà fait · 🟡 partiellement fait · 🔴 manquant · 🐍 calculable en Python (aucun appel LLM) · 🤖 nécessite un nouveau champ de prompt LLM.

---

## 1. État réel du PDF (`export_pdf_service.py`, 1713 lignes)

8 macro-sections existent aujourd'hui :

1. Executive Summary (perte structurelle, diagnostic immédiat, résumé exécutif, scores /10, score santé global + urgence, top décisions)
2. CEO Dashboard (6 KPI : Cash, EBITDA, Marge, Runway, Dette, Croissance)
3. Ce qui détruit la rentabilité (liste à puces + impact financier)
4. Opportunités immédiates (Quick Wins + leviers de croissance)
5. Plan d'action — 30/60/90 jours
6. Simulation avant/après (scénarios meilleur/probable/pire cas + avant-après + simulateur + projection)
7. Analyse détaillée
8. Annexe (qualité des données uniquement)

## 2. État réel du PPTX (`export_pptx_service.py`, 419 lignes)

8 slides, **100 % texte, zéro graphique natif** : Cover, Résumé, Diagnostic, Changements/Alertes, Problèmes, Opportunités, Plan d'action, Scores/Décision. Pas de slide CEO Dashboard, pas de grille Executive Summary à 2 cartes, pas de mini-graphique de tendance.

## 3. État réel de l'Excel (`excel_export.py`, 501 lignes)

5 feuilles statiques, aucune formule live (confirmé lors de l'audit précédent — hors scope de cette refonte, traité séparément).

---

## 4. Point par point — les 12 exigences de l'image

| # | Exigence de l'image | État | Détail |
|---|---|---|---|
| 1 | Structure narrative en 10 points | 🟡 | 6 des 10 sections existent déjà (Executive Summary, CEO Dashboard, Ce qui détruit, 5 décisions, Simulation, Plan 90j, Annexes). **Manquent : page dédiée « Combien cela coûte », Lettre du Copilote.** L'ordre actuel diffère légèrement (Plan d'action avant Simulation, alors que l'image le met après). |
| 2 | Executive Summary impactant (bandeau EBITDA/Cash/Score santé/Confiance IA + décision n°1 en très grand + coût par mois/jour) | 🟡 | `score_global` (Score santé) et `score_confiance` (Confiance IA) **existent déjà** comme champs (`AnalysisResult.score_global`, `AnalysisResult.score_confiance`) mais ne sont pas assemblés dans un bandeau 4-KPI en tête de page. Le coût par mois/semaine/jour/heure n'existe pas — 🐍 **calculable en Python** par simple division de l'impact annuel déjà disponible (`impact_financier_synthese` / 12, /52, /365, /8760). |
| 3 | Quantifier partout (impact annuel + mensuel, probabilité, délai, difficulté, responsable) | 🟡 | `QuickWin` a déjà `roi_estime`, `temps_mise_en_oeuvre`, `difficulte`. `PlanActionItem` a déjà `responsable`, `impact_attendu`. **Manque la probabilité de succès (%) et l'impact mensuel** sur ces deux modèles — 🤖 nouveaux champs de prompt. |
| 4 | Page dédiée « Combien cela coûte » | 🔴 | N'existe pas. 🐍 Entièrement calculable en Python à partir de l'impact financier annuel déjà extrait — pas besoin du LLM. |
| 5 | Tableau des 5 décisions prioritaires (impact annuel/mensuel/probabilité/délai/difficulté/responsable/statut, trié par impact, score ROI global) | 🔴 | Les « Quick Wins » actuels sont rendus en liste de cartes, pas en tableau triable avec toutes ces colonnes. Il faudrait étendre `QuickWin` (champs manquants : probabilité, statut) et reconstruire le rendu en `Table` ReportLab (le pattern `_score_table` existe déjà et est réutilisable). |
| 6 | Simulation Avant/Après avec double courbe (DO NOTHING rouge vs ACTION verte) sur 6-12 mois + KPI comparés + gain estimé + retour à l'équilibre | 🔴 | Le texte existe (`scenarios`), mais aucun graphique. 🐍 Faisable avec `reportlab.graphics.charts.lineplots.LinePlot` (déjà disponible, ReportLab est une dépendance existante — aucune nouvelle librairie). Nécessite des **séries de points** (12 valeurs mensuelles par scénario) — 🤖 à demander au LLM ou 🐍 à interpoler linéairement entre le point de départ et le gain final déjà connu (`scenarios[].impact`), au choix. |
| 7 | Plan d'action 90 jours en 3 phases (Stabiliser/Optimiser/Accélérer) avec priorité H/M/B | ✅ proche | `plan_action_30_60_90` existe avec `horizon` (30/60/90) — il manque juste le libellé de phase (« Stabiliser/Optimiser/Accélérer ») et le niveau de priorité H/M/B explicite. 🐍 Le libellé de phase peut être dérivé de l'horizon en Python (mapping fixe). La priorité H/M/B est 🤖 à ajouter au prompt, ou 🐍 dérivable du montant d'impact (seuils). |
| 8 | Projection & Trajectoire 6-12 mois (waterfall + courbe EBITDA + point de bascule) | 🟡 | Le texte de projection existe (`projection_*`). Pas de graphique. Même remarque qu'au point 6 : faisable avec `reportlab.graphics.charts`. |
| 9 | Lettre du Copilote (page personnalisée, ton direct, signée « Pepperyn IA ») | 🔴 | N'existe pas du tout. 🤖 Nouveau champ de prompt dédié (texte libre, ~150 mots, génér par Call 1, jamais modifié par Call 2 comme les autres sections immuables). |
| 10 | Design & mise en page (codes couleur stricts, hiérarchie visuelle, 1 page = 1 idée) | 🟡 | Les couleurs (`RED`, `AMBER`, `GREEN`, `BLUE_DARK`...) et les builders réutilisables existent déjà et respectent globalement cette logique. Quelques sections (Analyse détaillée, Annexe) restent denses/texte-only — à retravailler en blocs visuels. |
| 11 | Ton & contenu (verbes d'action, phrases courtes, bannir le vague) | 🟡 | Les instructions de prompt actuelles sont déjà « directes et frontales » (cf. règles immuables de Call 2 : « Ne reformule jamais en ton neutre »). Un tour de vis sur le vocabulaire d'action (Geler/Renégocier/Supprimer/Optimiser/Accélérer/Investir) est un ajustement de prompt léger, pas une refonte. |
| 12 | PowerPoint : deck CODIR 10-15 slides, graphiques natifs, 1 slide = 1 message | 🔴 | Écart le plus important. 8 slides texte-only actuellement → il faut ajouter des slides (CEO Dashboard, Executive Summary 2-cartes, Décisions prioritaires en tableau, Simulation avec graphique, Projection avec graphique, Lettre du Copilote courte) et convertir au moins 2-3 slides en graphiques natifs `python-pptx` (`CategoryChartData` / `XL_CHART_TYPE` — déjà disponible, pas de nouvelle dépendance). |

---

## 5. Synthèse — ce qui est calculable en Python vs ce qui nécessite le LLM

**🐍 Python uniquement (aucun risque d'invention, aucun nouvel appel LLM) :**
- Coût de l'inaction par mois/semaine/jour/heure (page 4) — division simple de l'impact annuel déjà extrait.
- Libellés de phase du Plan 90 jours (Stabiliser/Optimiser/Accélérer) — mapping fixe sur `horizon`.
- Tri du tableau des 5 décisions par impact, calcul du score ROI global — agrégation des `quick_wins` existants.
- Graphiques (courbes, waterfall, barres) — `reportlab.graphics.charts` (PDF) et `CategoryChartData` (PPTX), à partir des séries déjà calculées ou interpolées.

**🤖 Nouveau champ de prompt LLM requis :**
- Lettre du Copilote (texte libre).
- Probabilité de succès (%) et statut sur les Quick Wins / 5 décisions prioritaires.
- Priorité H/M/B explicite sur le Plan 90 jours (sauf si on préfère la dériver des montants en Python — recommandé, plus fiable, zéro risque d'invention par le LLM).
- Séries mensuelles de la simulation avant/après si on veut une vraie trajectoire LLM plutôt qu'une interpolation linéaire Python.

---

## 6. Plan de mise en œuvre proposé (PDF + PPTX en parallèle, comme demandé)

**Étape A — Données (schémas + prompt LLM)**
- Étendre `QuickWin` (probabilité, statut) et `PlanActionItem` (priorité H/M/B si calculée en Python, pas de nouveau champ LLM nécessaire).
- Ajouter le champ `lettre_copilote: Optional[str]` à `AnalysisResult` + section `# LETTRE COPILOTE` dans le prompt Call 1 + entrée dans la liste immuable de Call 2.
- Ajouter les helpers Python : `compute_cout_inaction(impact_annuel)` → dict {mois, semaine, jour, heure}, `compute_phase_label(horizon)`, `compute_priorite(impact)`.

**Étape B — PDF**
- Nouveau builder `_build_executive_banner()` (4 KPI EBITDA/Cash/Score santé/Confiance IA + décision n°1 géante) en tête de l'Executive Summary.
- Nouvelle macro-section « Combien cela coûte » (page dédiée, 100 % Python).
- Reconstruction du tableau des 5 décisions prioritaires (`Table` ReportLab triée par impact).
- Ajout de 2 graphiques `reportlab.graphics.charts` : courbe Simulation avant/après, courbe Projection/Trajectoire.
- Nouvelle macro-section « Lettre du Copilote » en clôture, avant les Annexes.
- Réordonnancement final pour suivre exactement les 10 points de l'image.

**Étape C — PPTX**
- Ajout de 4-6 nouvelles slides : CEO Dashboard, Executive Summary 2-cartes, 5 décisions (tableau ou cartes), Simulation avec graphique natif, Projection avec graphique natif, Lettre du Copilote courte.
- Conversion d'au moins 2 slides texte en graphiques natifs `python-pptx`.

**Étape D — Vérification**
- Smoke test PDF (comme pour le Phase 1) + smoke test PPTX (ouverture avec `python-pptx`, vérification du nombre de slides et de la présence des graphiques) + `tsc` côté frontend si des champs sont consommés par l'UI (aperçu rapport dans le chat).

---

## 7. Risques restants

- Les graphiques ReportLab/python-pptx demandent un peu plus de code que des blocs de texte — risque de régression visuelle si mal calibrés ; prévoir un test visuel (export PDF/PPTX réel + relecture).
- Si l'on choisit de demander au LLM les séries mensuelles de simulation plutôt que de les interpoler en Python, il faut renforcer la garde-fou anti-invention (le prompt actuel interdit déjà les montants inventés dans AVANT/APRÈS et SIMULATEUR — il faudra répliquer cette règle sur les nouvelles séries).
- La Lettre du Copilote, étant un texte libre signé, doit rester courte et factuelle — risque de ton trop « marketing » si le prompt n'est pas assez cadré (à calibrer avec un exemple dans le prompt).
- PPTX : python-pptx ne supporte pas tous les styles de graphique aussi finement que PowerPoint natif — prévoir un rendu simple et propre plutôt que des graphiques surchargés.
