"""
tests/test_edx_001.py

EDX-001 — Executive Decision Chain
Gardien de la chaîne de raisonnement Pepperyn.

Protocole de vérification :
  1. Modèle DecisionReasoning — Pydantic (structure, valeurs par défaut)
  2. _normalize_tokens          — tokenisation et préfixes morphologiques
  3. _score_pair                — calcul de score avec bonus sémantique
  4. _compute_reasoning_skeleton — pipeline déterministe complet

  Cas de référence CTO (Optilux SAS) :
  A. Décision stock      → destructeur stock      (HIGH)
  B. Décision DSO        → destructeur DSO/BFR    (HIGH)
  C. Décision fournisseurs → destructeur marge    (HIGH)
  D. Décision commissionnement → destructeur commercial (HIGH)

  5. ExecutiveCaseJSON.decision_reasoning — champ présent dans le modèle
  6. case_to_result_dict — decision_reasoning inclus dans le dict exporté
"""
import sys, os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "dummy")

from models.executive_case import DecisionReasoning, ExecutiveCaseJSON
from models.executive_decision_model import (
    ExecutiveDecision, ValueDestroyer, DataQualityInfo
)
from services.executive_case_builder import (
    _normalize_tokens,
    _score_pair,
    _compute_reasoning_skeleton,
    case_to_result_dict,
)


# ─── Fixtures Optilux SAS (cas de référence CTO) ─────────────────────────────

OPTILUX_DECISIONS = [
    ExecutiveDecision(
        decision="Provisionner et liquider le stock obsolète (620 K€) avant la clôture de septembre",
        annual_impact=400_000, monthly_impact=33_333,
        difficulty="Faible", timeline="30 jours",
        owner="DAF + Directeur Logistique", roi_score=9.2,
    ),
    ExecutiveDecision(
        decision="Plan de recouvrement agressif — réduire le DSO de 87j à 55j en 90 jours",
        annual_impact=185_000, monthly_impact=15_417,
        difficulty="Faible", timeline="30 jours",
        owner="DAF", roi_score=8.7,
    ),
    ExecutiveDecision(
        decision="Renégocier les conditions tarifaires avec les 3 fournisseurs principaux",
        annual_impact=246_000, monthly_impact=20_500,
        difficulty="Moyen", timeline="60 jours",
        owner="Directeur Commercial", roi_score=7.8,
    ),
    ExecutiveDecision(
        decision="Restructurer le plan de commissionnement commercial",
        annual_impact=274_000, monthly_impact=22_833,
        difficulty="Moyen", timeline="90 jours",
        owner="DG + RH", roi_score=6.4,
    ),
]

OPTILUX_DESTROYERS = [
    ValueDestroyer(name="Stock obsolète non provisionné",           annual_impact=-620_000),
    ValueDestroyer(name="Érosion des marges commerciales (-7 pts)", annual_impact=-574_000),
    ValueDestroyer(name="Sous-performance commerciale (-18 %)",     annual_impact=-320_000),
    ValueDestroyer(name="Surcoût BFR — DSO excessif (87j vs 45j)", annual_impact=-185_000),
]

OPTILUX_DQ = DataQualityInfo(score=81, anomalies=["Données Q2 2026 partielles"])


@pytest.fixture(scope="module")
def optilux_skeleton():
    """Squelette déterministe complet pour les 4 décisions Optilux."""
    return _compute_reasoning_skeleton(
        decisions=OPTILUX_DECISIONS,
        destroyers=OPTILUX_DESTROYERS,
        data_quality=OPTILUX_DQ,
        global_confidence=81,
    )


# ─── 1. Modèle DecisionReasoning ──────────────────────────────────────────────

class TestDecisionReasoningModel:

    def test_model_default_values(self):
        """Tous les champs optionnels sont None par défaut."""
        dr = DecisionReasoning(decision_index=0)
        assert dr.decision_index == 0
        assert dr.problem_source is None
        assert dr.matching_confidence is None
        assert dr.why_this_decision is None
        assert dr.inaction_risk is None
        assert dr.decision_confidence is None
        assert dr.confidence_explanation is None

    def test_model_all_fields(self):
        """Le modèle accepte tous les champs simultanément."""
        dr = DecisionReasoning(
            decision_index=2,
            problem_source="Stock obsolète — 620 K€/an",
            matching_confidence="HIGH",
            why_this_decision="Pepperyn recommande cette décision parce que...",
            inaction_risk="À fin septembre, le stock obsolète pèsera...",
            decision_confidence=83,
            confidence_explanation="Score élevé grâce au ROI de 9.2/10.",
        )
        assert dr.matching_confidence == "HIGH"
        assert dr.decision_confidence == 83

    def test_matching_confidence_values(self):
        """Les trois valeurs autorisées de matching_confidence sont acceptées."""
        for conf in ("HIGH", "LOW", "FALLBACK_INDEX"):
            dr = DecisionReasoning(decision_index=0, matching_confidence=conf)
            assert dr.matching_confidence == conf

    def test_executive_case_json_has_decision_reasoning_field(self):
        """ExecutiveCaseJSON contient bien le champ decision_reasoning."""
        case = ExecutiveCaseJSON()
        assert hasattr(case, "decision_reasoning")
        assert isinstance(case.decision_reasoning, list)
        assert case.decision_reasoning == []

    def test_executive_case_json_accepts_reasoning_items(self):
        """ExecutiveCaseJSON accepte une liste de DecisionReasoning."""
        dr = DecisionReasoning(decision_index=0, matching_confidence="HIGH", decision_confidence=83)
        case = ExecutiveCaseJSON(decision_reasoning=[dr])
        assert len(case.decision_reasoning) == 1
        assert case.decision_reasoning[0].matching_confidence == "HIGH"


# ─── 2. _normalize_tokens ────────────────────────────────────────────────────

class TestNormalizeTokens:

    def test_lowercase_and_accent_removal(self):
        tokens = _normalize_tokens("Érosion des marges")
        assert "erosion" in tokens
        assert "marges" in tokens

    def test_stop_words_removed(self):
        tokens = _normalize_tokens("les des par est une que")
        # Tous ces mots sont des stop-words → set vide
        assert len(tokens) == 0

    def test_short_tokens_excluded(self):
        tokens = _normalize_tokens("au et le")
        assert tokens == set()  # < 3 chars, tous stop-words ou trop courts

    def test_prefix_for_long_tokens(self):
        """Tokens ≥ 8 chars → préfixe de 6 chars ajouté."""
        tokens = _normalize_tokens("fournisseurs")
        assert "fournisseurs" in tokens
        assert "fourni" in tokens   # préfixe 6 chars

    def test_prefix_covers_morphological_variants(self):
        """fournisseur et fournisseurs partagent le même préfixe 'fourni'."""
        t_sing = _normalize_tokens("fournisseur")
        t_plur = _normalize_tokens("fournisseurs")
        assert "fourni" in t_sing
        assert "fourni" in t_plur

    def test_financial_keywords_preserved(self):
        """Les mots-clés financiers clés sont bien tokenisés."""
        tokens = _normalize_tokens("stock DSO recouvrement commissionnement")
        assert "stock" in tokens
        assert "dso" in tokens
        assert "recouvrement" in tokens
        assert "commissionnement" in tokens


# ─── 3. _score_pair ──────────────────────────────────────────────────────────

class TestScorePair:

    def test_identical_texts_score_100_plus(self):
        """Textes identiques → score maximum (100 + 30 si même groupe)."""
        t = _normalize_tokens("stock obsolete liquidation")
        score = _score_pair(t, t)
        assert score >= 100

    def test_empty_tokens_score_zero(self):
        assert _score_pair(set(), {"stock"}) == 0.0
        assert _score_pair({"stock"}, set()) == 0.0

    def test_semantic_bonus_same_group(self):
        """Même groupe sémantique → bonus ≥ 30 même sans overlap de tokens."""
        t_decision = _normalize_tokens("fournisseurs principaux reneg")
        t_destroyer = _normalize_tokens("marges erosion brute")
        score = _score_pair(t_decision, t_destroyer)
        # fournisseur(s) et marge/erosion sont dans le groupe 'marge' → +30
        assert score >= 30

    def test_no_bonus_different_groups(self):
        """Groupes différents → pas de bonus sémantique."""
        t_stock = _normalize_tokens("stock obsolete inventaire")
        t_comm  = _normalize_tokens("commissionnement commercial vente")
        score   = _score_pair(t_stock, t_comm)
        # Pas de groupe commun
        assert score < 30


# ─── 4. Cas CTO Optilux — les 4 mappings obligatoires ───────────────────────

class TestOptiluxCTOMappings:

    def test_skeleton_has_four_entries(self, optilux_skeleton):
        """Le skeleton contient une entrée par décision."""
        assert len(optilux_skeleton) == 4

    def test_decision_indices_sequential(self, optilux_skeleton):
        """Les decision_index sont 0, 1, 2, 3."""
        indices = [s["decision_index"] for s in optilux_skeleton]
        assert indices == [0, 1, 2, 3]

    def test_cas_A_stock_decision_maps_to_stock_destroyer(self, optilux_skeleton):
        """
        CTO CASE A : la décision stock est liée au destructeur stock.
        Décision 0 : liquidation du stock obsolète
        → Destructeur : 'Stock obsolète non provisionné'
        """
        s = optilux_skeleton[0]
        assert s["matching_confidence"] == "HIGH", (
            f"Expected HIGH, got {s['matching_confidence']}. "
            f"problem_source={s['problem_source']}"
        )
        assert "stock" in s["problem_source"].lower() or "obsolete" in s["problem_source"].lower().replace("è", "e"), (
            f"Destructeur attendu : stock. Reçu : {s['problem_source']}"
        )

    def test_cas_B_dso_decision_maps_to_bfr_destroyer(self, optilux_skeleton):
        """
        CTO CASE B : la décision DSO est liée au destructeur DSO/BFR.
        Décision 1 : réduction du DSO / recouvrement
        → Destructeur : 'Surcoût BFR — DSO excessif'
        """
        s = optilux_skeleton[1]
        assert s["matching_confidence"] == "HIGH", (
            f"Expected HIGH, got {s['matching_confidence']}. "
            f"problem_source={s['problem_source']}"
        )
        ps = s["problem_source"].lower()
        assert "dso" in ps or "bfr" in ps, (
            f"Destructeur attendu : DSO/BFR. Reçu : {s['problem_source']}"
        )

    def test_cas_C_fournisseurs_decision_maps_to_marge_destroyer(self, optilux_skeleton):
        """
        CTO CASE C : la décision fournisseurs est liée au destructeur marge.
        Décision 2 : renégociation tarifaire fournisseurs
        → Destructeur : 'Érosion des marges commerciales'
        """
        s = optilux_skeleton[2]
        assert s["matching_confidence"] == "HIGH", (
            f"Expected HIGH, got {s['matching_confidence']}. "
            f"problem_source={s['problem_source']}"
        )
        ps = s["problem_source"].lower()
        assert "marge" in ps or "erosion" in ps or "tarif" in ps or "fournisseur" in ps, (
            f"Destructeur attendu : marge/fournisseurs. Reçu : {s['problem_source']}"
        )

    def test_cas_D_commissionnement_decision_maps_to_commercial_destroyer(self, optilux_skeleton):
        """
        CTO CASE D : la décision commissionnement est liée au destructeur commercial.
        Décision 3 : restructuration du plan de commissionnement
        → Destructeur : 'Sous-performance commerciale'
        """
        s = optilux_skeleton[3]
        assert s["matching_confidence"] == "HIGH", (
            f"Expected HIGH, got {s['matching_confidence']}. "
            f"problem_source={s['problem_source']}"
        )
        ps = s["problem_source"].lower()
        assert "commercial" in ps or "commission" in ps or "performance" in ps, (
            f"Destructeur attendu : performance commerciale. Reçu : {s['problem_source']}"
        )

    def test_all_four_destroyers_are_distinct(self, optilux_skeleton):
        """Les 4 décisions pointent vers 4 destructeurs différents (pas de doublon)."""
        sources = [s["problem_source"] for s in optilux_skeleton if s["problem_source"]]
        assert len(sources) == len(set(sources)), (
            f"Collision : plusieurs décisions pointent vers le même destructeur. "
            f"Sources={sources}"
        )


# ─── 5. decision_confidence — formule déterministe ───────────────────────────

class TestDecisionConfidence:

    def test_confidence_in_valid_range(self, optilux_skeleton):
        """decision_confidence est toujours dans [50, 95]."""
        for s in optilux_skeleton:
            assert 50 <= s["decision_confidence"] <= 95, (
                f"Confiance hors plage pour décision {s['decision_index']}: "
                f"{s['decision_confidence']}"
            )

    def test_higher_roi_produces_higher_confidence(self):
        """ROI score plus élevé → decision_confidence plus élevé (toutes choses égales)."""
        dec_high_roi = ExecutiveDecision(
            decision="Liquider le stock obsolète", annual_impact=400_000,
            timeline="30 jours", owner="DAF", roi_score=9.5,
        )
        dec_low_roi = ExecutiveDecision(
            decision="Liquider le stock obsolète", annual_impact=400_000,
            timeline="30 jours", owner="DAF", roi_score=3.0,
        )
        d = [ValueDestroyer(name="Stock obsolète non provisionné", annual_impact=-620_000)]

        sk_high = _compute_reasoning_skeleton([dec_high_roi], d, None, 70)
        sk_low  = _compute_reasoning_skeleton([dec_low_roi],  d, None, 70)

        assert sk_high[0]["decision_confidence"] >= sk_low[0]["decision_confidence"]

    def test_anomalies_reduce_confidence(self):
        """Plus d'anomalies → decision_confidence plus bas (pénalité −2 par anomalie, max −10)."""
        dec = ExecutiveDecision(
            decision="Plan de recouvrement DSO",
            annual_impact=185_000, timeline="30 jours", owner="DAF", roi_score=8.0,
        )
        d = [ValueDestroyer(name="DSO BFR excessif", annual_impact=-185_000)]
        dq_clean = DataQualityInfo(score=80, anomalies=[])
        dq_dirty = DataQualityInfo(score=80, anomalies=["A1", "A2", "A3", "A4", "A5"])

        sk_clean = _compute_reasoning_skeleton([dec], d, dq_clean, 80)
        sk_dirty = _compute_reasoning_skeleton([dec], d, dq_dirty, 80)

        assert sk_clean[0]["decision_confidence"] > sk_dirty[0]["decision_confidence"]


# ─── 6. case_to_result_dict — decision_reasoning dans le dict exporté ────────

class TestCaseToResultDict:

    def test_decision_reasoning_in_result_dict(self):
        """case_to_result_dict inclut decision_reasoning dans le dict."""
        dr = DecisionReasoning(
            decision_index=0,
            problem_source="Stock obsolète — 620 K€/an",
            matching_confidence="HIGH",
            decision_confidence=83,
        )
        case = ExecutiveCaseJSON(decision_reasoning=[dr])
        result = case_to_result_dict(case)
        assert "decision_reasoning" in result
        assert isinstance(result["decision_reasoning"], list)
        assert len(result["decision_reasoning"]) == 1

    def test_decision_reasoning_fields_in_dict(self):
        """Tous les champs de DecisionReasoning sont présents dans le dict exporté."""
        dr = DecisionReasoning(
            decision_index=1,
            problem_source="DSO excessif",
            matching_confidence="HIGH",
            why_this_decision="Pepperyn recommande cette décision parce que...",
            inaction_risk="À fin septembre...",
            decision_confidence=80,
            confidence_explanation="Score basé sur ROI de 8.7.",
        )
        case = ExecutiveCaseJSON(decision_reasoning=[dr])
        result = case_to_result_dict(case)
        r = result["decision_reasoning"][0]
        assert r["decision_index"] == 1
        assert r["problem_source"] == "DSO excessif"
        assert r["matching_confidence"] == "HIGH"
        assert r["why_this_decision"] is not None
        assert r["inaction_risk"] is not None
        assert r["decision_confidence"] == 80
        assert r["confidence_explanation"] is not None

    def test_empty_decision_reasoning_serialized(self):
        """Un ExecutiveCaseJSON sans raisonnement exporte une liste vide."""
        case = ExecutiveCaseJSON()
        result = case_to_result_dict(case)
        assert result["decision_reasoning"] == []
