# PHIDANI_WALKING_SKELETON.md

**Nature :** Mission 6. Aucun code. Décrit le plus petit parcours vertical traversant toutes les facultés, sur le cas Phidani (fichier janvier-août 2019 → janvier-septembre 2019, date système simulée 2 octobre 2019).

---

| Étape | Contrat | Entrée | Sortie | Test | Volontairement vide dans cette tranche |
|---|---|---|---|---|---|
| **1. Ingestion** | — (mécanique existante) | Fichier Excel Phidani (nouvelle version) | Structure brute parsée | Le fichier est lu sans erreur, colonnes identifiées | Support ERP/API/MCP — un seul format Excel suffit |
| **2. Normalisation → Evidence** | `EvidenceContext` | Structure brute parsée | `FinancialFact[]` avec provenance, `sheets_verified` | Chaque fait produit référence une cellule/feuille source réelle | NER sur texte libre non structuré — hors périmètre, déjà documenté comme limite connue |
| **3. Contexte temporel minimal** | `TemporalContext` | `PeriodObservation` (nouvelle période détectée : septembre), Engagement Phidani | `BusinessMoment` (« nouvelle période disponible »), `DataFreshness`, `ComparisonHorizons` (YTD jan-sept, rolling 12 si historique suffisant) | Le FTE identifie correctement août comme période précédente et septembre comme probablement close, sans intervention humaine | Tous les calendriers fiscaux/cycles — seule la détection janvier-septembre est requise, pas une généralisation |
| **4. Dossier cognitif** | `CognitiveCaseFile` | Evidence + Temporal + Organization (minimal — Phidani déjà créée) | Dossier assemblé, borné | Le dossier contient une provenance pour chaque fait, aucune donnée sans origine | `OpenExceptions` peut rester vide si aucune anomalie réelle sur ce cas — ne pas forcer une exception artificielle |
| **5. Deux analyses indépendantes** | `IndependentAnalysis` × 2 | `CognitiveCaseFile` (identique pour les deux) | Analyse A (angle rentabilité/cash), Analyse B (angle modèle économique/risques) | Les deux analyses ne partagent aucun contexte au-delà du dossier ; test explicite : aucune trace de l'une dans les logs d'appel de l'autre | Quinze agents spécialistes — seulement deux angles pour cette tranche |
| **6. Adjudication** | `AdjudicationResult` | Analyse A + Analyse B | Convergences, divergences qualifiées (factuelle/causale/jugement), preuves ignorées éventuelles | Si A et B divergent sur un point factuel, l'Adjudicator le signale explicitement, ne moyenne jamais | Résolution automatique de divergence critique — doit rester visible, pas arbitrée silencieusement |
| **7. Synthèse (Executive CFO)** | `ExecutiveRecommendation` | `AdjudicationResult` uniquement (jamais le dossier brut) | Synthèse, recommandation(s), conditions, risques, questions de revue | Aucune divergence non résolue n'est masquée dans la sortie finale | Alternatives multiples élaborées — une recommandation principale + risques suffit pour cette tranche |
| **8. Quality Gate** | déterministe | `ExecutiveRecommendation` + `EvidenceContext` | Pass/Fail + raisons | Chaque chiffre cité est traçable jusqu'à un `FinancialFact` ; aucune recommandation sans preuve associée | Contrôles de conformité réglementaire avancés — hors périmètre de cette tranche |
| **9. Décision humaine** | — (interface existante, Article II) | `ExecutiveRecommendation` validée par le Gate | Acceptée / rejetée / modifiée par l'utilisateur | La décision humaine est capturée et horodatée | Workflow d'approbation multi-niveaux — une seule décision suffit |
| **10. Mémoire minimale** | `LearningProposal` | Décision humaine + résultat immédiat connu | Entrée Decision Memory (Engagement Phidani) : nouveaux faits, période analysée, conclusions qualifiées, recommandation, décision, inconnues, ce qui doit être observé au prochain cycle | La prochaine exécution sur Phidani peut lire cette entrée et la citer | Apprentissage professionnel global — reste strictement local à Phidani, aucune promotion automatique |

---

## Ce que ce squelette prouve, et seulement cela

Que les huit facultés peuvent communiquer par les contrats cibles de bout en bout sur un cas réel, sans qu'aucune faculté n'ait besoin d'être complète pour que le parcours fonctionne. Il ne prouve pas la qualité du raisonnement produit (c'est l'objet des Golden Cases, Mission 31.6) ni la stabilité inter-runs (Mission 31.5) — ces preuves viennent après, pas dans cette tranche.

---

**PHIDANI_WALKING_SKELETON ÉTABLI. AUCUN CODE ÉCRIT.**
