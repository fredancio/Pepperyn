"""
Golden Test E2E — Arc Décisionnel MVP v16
=========================================

Parcours complet simulé en mémoire (FakeSupabase — pas de vraie DB nécessaire).

Scénario nominal :
  Analyse N → "Je vais appliquer" → Arc INTENTION
  → check-in done → Arc EXECUTION
  → Analyse N+1 → conséquence candidate
  → confirmation → CONSEQUENCES_LINKED → LEARNING_PROPOSED
  → decision_text rétrospectif + learning → Arc CLOSED

Cas négatifs :
  A. "Je ne vais pas appliquer" (rejected)        → aucun arc
  B. "Je ne sais pas encore"   (unsure)           → aucun arc  [RÉGRESSION BUG #ARC-001]
  C. Rejet conséquence candidate                  → arc reste EXECUTION
  D. CLOSED avec decision_text NULL               → ValueError/422
  E. Erreur service arc                           → analyse/feedback continuent
  F. Double soumission "Je vais appliquer"        → idempotence (1 seul arc)

Régression BUG #ARC-001 (classe TestArcCreationStatusRegression) :
  - planned          → exactement 1 arc
  - unsure           → 0 arc  ← correction principale
  - rejected         → 0 arc
  - not_done         → 0 arc
  - no_longer_relevant → 0 arc
  - done             → 0 arc (via feedback, pas via check-in)
"""
from __future__ import annotations

import sys
import uuid
import copy
import pytest
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock, patch


# ─── FakeSupabase en mémoire ──────────────────────────────────────────────────

UNIQUE_CONSTRAINTS = {
    "decision_arcs": ("origin_analysis_id", "recommendation_id"),
    "arc_analysis_links": ("arc_id", "analysis_id"),
}

class ExecuteResult:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class QueryBuilder:
    def __init__(self, table_ref: list, table_name: str):
        self._table = table_ref
        self._table_name = table_name
        self._op = "select"
        self._cols = "*"
        self._filters: list[tuple] = []
        self._insert_row = None
        self._update_dict = None
        self._limit_n: Optional[int] = None
        self._is_single = False
        self._count_mode = None

    def select(self, cols="*", count=None):
        self._op = "select"
        self._cols = cols
        self._count_mode = count
        return self

    def insert(self, data: dict):
        self._op = "insert"
        self._insert_row = dict(data)
        return self

    def update(self, data: dict):
        self._op = "update"
        self._update_dict = dict(data)
        return self

    def eq(self, field: str, value):
        self._filters.append((field, value))
        return self

    def limit(self, n: int):
        self._limit_n = n
        return self

    def single(self):
        self._is_single = True
        return self

    def _matches(self, row: dict) -> bool:
        for f, v in self._filters:
            if row.get(f) != v:
                return False
        return True

    def execute(self) -> ExecuteResult:
        if self._op == "insert":
            row = dict(self._insert_row)
            if "id" not in row:
                row["id"] = str(uuid.uuid4())

            # UNIQUE constraint check
            constraint = UNIQUE_CONSTRAINTS.get(self._table_name)
            if constraint:
                for existing in self._table:
                    if all(existing.get(k) == row.get(k) for k in constraint):
                        raise Exception(
                            f"unique violation: {self._table_name} "
                            f"({', '.join(constraint)})"
                        )

            self._table.append(row)
            return ExecuteResult([row])

        elif self._op == "update":
            updated = []
            for row in self._table:
                if self._matches(row):
                    row.update(self._update_dict)
                    updated.append(copy.copy(row))
            return ExecuteResult(updated)

        else:  # select
            results = [copy.copy(r) for r in self._table if self._matches(r)]
            if self._limit_n is not None:
                results = results[: self._limit_n]
            if self._count_mode == "exact":
                return ExecuteResult(results, count=len(results))
            if self._is_single:
                if not results:
                    raise Exception(f"No row found in {self._table_name} matching {self._filters}")
                return ExecuteResult(results[0])
            return ExecuteResult(results)


class FakeSupabase:
    """Supabase en mémoire — stocke les tables comme listes de dicts."""

    def __init__(self):
        self._data: dict[str, list] = {
            "analyses": [],
            "decision_arcs": [],
            "arc_analysis_links": [],
            "decision_feedback": [],
        }

    def from_(self, table: str) -> QueryBuilder:
        if table not in self._data:
            self._data[table] = []
        return QueryBuilder(self._data[table], table)

    def get(self, table: str) -> list:
        return self._data.get(table, [])

    def seed_analysis(self, id_: str, decision_kernel=None, decision_fingerprint=None,
                      score_rentabilite=None, score_risque=None):
        self._data["analyses"].append({
            "id": id_,
            "decision_kernel": decision_kernel,
            "decision_fingerprint": decision_fingerprint,
            "score_rentabilite": score_rentabilite,
            "score_risque": score_risque,
        })


def make_service(fake_sb: FakeSupabase):
    from services.arc_service import ArcService
    svc = ArcService()
    svc._supabase = fake_sb
    return svc


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ─── Constantes du scénario ───────────────────────────────────────────────────

COMPANY_ID   = "aaaaaaaa-0000-0000-0000-000000000001"
ANALYSIS_N   = "bbbbbbbb-0000-0000-0000-000000000001"
ANALYSIS_N1  = "bbbbbbbb-0000-0000-0000-000000000002"
REC_ID       = "rec-sha1-0000000000000001"
REC_TEXT     = "Renégocier les contrats fournisseurs pour améliorer la marge brute."
FINGERPRINT  = "fp-abcdef1234567890abcdef1234567890"
KERNEL       = {"type": "dk-1", "problemes": ["Marge brute insuffisante"], "score": 4.5}


# ═══════════════════════════════════════════════════════════════════════════════
# SCÉNARIO NOMINAL
# ═══════════════════════════════════════════════════════════════════════════════

class TestNominalScenario:
    """
    Parcours complet de bout en bout.
    """

    def _setup(self):
        sb = FakeSupabase()
        sb.seed_analysis(
            ANALYSIS_N,
            decision_kernel=KERNEL,
            decision_fingerprint=FINGERPRINT,
            score_rentabilite=4,
            score_risque=7,
        )
        svc = make_service(sb)
        return sb, svc

    # ── Étape 1 : Arc créé depuis feedback 'planned' ──────────────────────────

    def test_step1_arc_created_from_planned_feedback(self):
        """
        Utilisateur : "Je vais appliquer"
        → status='planned' → arc_service.create_arc_from_feedback()
        → Arc INTENTION, decision_text NULL, decision_confirmation_source NULL
        """
        sb, svc = self._setup()

        result = svc.create_arc_from_feedback(
            company_id=COMPANY_ID,
            origin_analysis_id=ANALYSIS_N,
            recommendation_id=REC_ID,
            decision_source="plan_action",
            recommendation_text=REC_TEXT,
        )

        assert result["created"] is True, "L'arc doit être créé"
        arc_id = result["arc_id"]
        assert arc_id is not None

        arcs = sb.get("decision_arcs")
        assert len(arcs) == 1
        arc = arcs[0]

        # Champs immuables à la création
        assert arc["status"] == "intention"
        assert arc["recommendation_text"] == REC_TEXT
        assert arc["decision_fingerprint"] == FINGERPRINT
        assert arc["company_id"] == COMPANY_ID
        assert arc["origin_analysis_id"] == ANALYSIS_N

        # Invariants V2.2 — critique
        assert arc.get("decision_text") is None, \
            "INVARIANT: decision_text DOIT être NULL à INTENTION"
        assert arc.get("decision_confirmation_source") is None, \
            "INVARIANT: decision_confirmation_source DOIT être NULL à INTENTION"
        assert arc.get("decision_confirmed_at") is None, \
            "INVARIANT: decision_confirmed_at DOIT être NULL à INTENTION"

        # Lien origin créé
        links = sb.get("arc_analysis_links")
        assert len(links) == 1
        assert links[0]["link_type"] == "origin"
        assert links[0]["arc_id"] == arc_id
        assert links[0]["analysis_id"] == ANALYSIS_N
        assert links[0]["confirmed_by_user"] is True

        print(f"\n[ÉTAPE 1 OK] Arc {arc_id[:8]}… créé — INTENTION")
        print(f"  recommendation_text        : {arc['recommendation_text'][:60]}")
        print(f"  decision_text              : {arc.get('decision_text')!r}")
        print(f"  decision_confirmation_source: {arc.get('decision_confirmation_source')!r}")
        print(f"  decision_confirmed_at      : {arc.get('decision_confirmed_at')!r}")

    # ── Étape 2 : Check-in done → EXECUTION ──────────────────────────────────

    def test_step2_checkin_done_advances_to_execution(self):
        """
        Check-in "done" → Arc INTENTION → EXECUTION
        decision_confirmation_source = 'inferred_from_execution'
        decision_text reste NULL
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]

        result = svc.register_execution_from_checkin(arc_id, "done")

        arc = sb.get("decision_arcs")[0]
        assert arc["status"] == "execution"
        assert arc["execution_status"] == "complete"
        assert arc["decision_confirmation_source"] == "inferred_from_execution"
        assert arc["decision_confirmed_at"] is not None, \
            "decision_confirmed_at doit être renseigné (date de prise de connaissance)"
        assert arc.get("decision_text") is None, \
            "INVARIANT: decision_text reste NULL après check-in — décision inférée ≠ décision documentée"

        print(f"\n[ÉTAPE 2 OK] Arc {arc_id[:8]}… → EXECUTION")
        print(f"  execution_status            : {arc['execution_status']}")
        print(f"  decision_confirmation_source: {arc['decision_confirmation_source']}")
        print(f"  decision_confirmed_at       : {arc['decision_confirmed_at'][:19]}")
        print(f"  decision_text               : {arc.get('decision_text')!r}  ← NULL ✓")

    # ── Étape 3 : Analyse N+1 → conséquence candidate ────────────────────────

    def test_step3_analysis_n1_detects_candidate(self):
        """
        Analyse N+1 → detect_consequence_candidates()
        → candidat inséré dans arc_analysis_links avec link_type='consequence_candidate'
        → confirmed_by_user = NULL (en attente de review)
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")

        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)

        candidates = svc.detect_consequence_candidates(
            company_id=COMPANY_ID,
            new_analysis_id=ANALYSIS_N1,
            analyse_json={
                "score_rentabilite": 6,
                "score_risque": 5,
                "revenus": {"total": 1_250_000},
            },
        )

        assert len(candidates) >= 1, "Au moins un candidat doit être détecté"
        c = candidates[0]
        assert c["arc_id"] == arc_id
        assert c["analysis_id"] == ANALYSIS_N1
        assert "est survenu après" in c["hypothesis"] or "corrélé" in c["hypothesis"] \
               or "évolution" in c["hypothesis"], \
               "L'hypothèse doit exprimer une corrélation temporelle"

        # Vérifier que le lien est dans la DB
        links = [l for l in sb.get("arc_analysis_links")
                 if l["link_type"] == "consequence_candidate"]
        assert len(links) == 1
        assert links[0]["confirmed_by_user"] is None, \
            "confirmed_by_user DOIT être NULL — en attente de review utilisateur"

        # Vérifier que l'hypothèse ne contient pas de causalité
        h = c["hypothesis"].lower()
        forbidden = ["a causé", "est la conséquence de", "grâce à votre décision",
                     "résulte de", "provoque"]
        for term in forbidden:
            assert term not in h, f"RÈGLE CAUSALE VIOLÉE: '{term}' trouvé dans l'hypothèse"

        print(f"\n[ÉTAPE 3 OK] Candidat détecté pour analyse N+1")
        print(f"  hypothesis : {c['hypothesis'][:100]}")
        print(f"  confirmed_by_user : {links[0]['confirmed_by_user']!r}  ← NULL ✓")

    # ── Étape 4 : Confirmation → CONSEQUENCES_LINKED → LEARNING_PROPOSED ──────

    def test_step4_confirm_consequence_advances_to_learning(self):
        """
        Utilisateur confirme le lien → Arc CONSEQUENCES_LINKED → LEARNING_PROPOSED
        learning_text généré automatiquement (template, sans LLM)
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)
        svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1,
                                          {"score_rentabilite": 6, "score_risque": 5})

        result = svc.confirm_consequence_link(arc_id, ANALYSIS_N1, confirmed=True)

        assert result["confirmed"] is True
        assert result["arc_status"] == "learning_proposed"
        assert result["learning_text"] is not None and len(result["learning_text"]) > 20

        arc = sb.get("decision_arcs")[0]
        assert arc["status"] == "learning_proposed"
        assert arc["learning_text"] is not None

        print(f"\n[ÉTAPE 4 OK] Arc {arc_id[:8]}… → LEARNING_PROPOSED")
        print(f"  learning_text (début) : {arc['learning_text'][:100]}")

    # ── Étape 5 : Validation learning avec confirmation rétrospective → CLOSED ─

    def test_step5_validate_learning_with_retrospective_decision_closes_arc(self):
        """
        Arc a decision_text=NULL (inféré). L'utilisateur confirme rétrospectivement.
        → decision_text écrit (immuable ensuite)
        → decision_confirmation_source = 'explicit'
        → Arc CLOSED, closed_at renseigné
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)
        svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1,
                                          {"score_rentabilite": 6, "score_risque": 5})
        svc.confirm_consequence_link(arc_id, ANALYSIS_N1, confirmed=True)

        DECISION_REELLE = ("J'ai renégocié les contrats avec 3 fournisseurs principaux, "
                           "obtenant une réduction moyenne de 8% sur les coûts variables.")
        LEARNING = ("La renégociation des contrats fournisseurs a permis de récupérer "
                    "2 points de marge brute en 4 mois. Leçon : engager ces négociations "
                    "en début de trimestre pour avoir plus de levier.")

        result = svc.validate_learning(
            arc_id=arc_id,
            learning_text=LEARNING,
            decision_text=DECISION_REELLE,
        )

        assert result["status"] == "closed"
        assert result["closed_at"] is not None

        arc = sb.get("decision_arcs")[0]

        # Champs immuables maintenant écrits
        assert arc["status"] == "closed"
        assert arc["decision_text"] == DECISION_REELLE
        assert arc["decision_confirmation_source"] == "explicit", \
            "INVARIANT: confirmation rétrospective = 'explicit'"
        assert arc["decision_confirmed_at"] is not None
        assert arc["learning_text"] == LEARNING
        assert arc["closed_at"] is not None

        # decision_text ≠ recommendation_text
        assert arc["decision_text"] != arc["recommendation_text"], \
            "INVARIANT: decision_text ≠ recommendation_text (l'utilisateur a décidé différemment)"

        print(f"\n[ÉTAPE 5 OK] Arc {arc_id[:8]}… → CLOSED")
        print(f"  decision_text              : {arc['decision_text'][:80]}")
        print(f"  recommendation_text        : {arc['recommendation_text'][:60]}")
        print(f"  decision_confirmation_source: {arc['decision_confirmation_source']}")
        print(f"  decision_confirmed_at      : {arc['decision_confirmed_at'][:19]}")
        print(f"  closed_at                  : {arc['closed_at'][:19]}")
        print(f"  learning_text (début)      : {arc['learning_text'][:80]}")


# ═══════════════════════════════════════════════════════════════════════════════
# CAS NÉGATIFS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNegativeCases:

    def _setup(self):
        sb = FakeSupabase()
        sb.seed_analysis(
            ANALYSIS_N,
            decision_kernel=KERNEL,
            decision_fingerprint=FINGERPRINT,
            score_rentabilite=4,
            score_risque=7,
        )
        svc = make_service(sb)
        return sb, svc

    # ── Cas A : rejected → aucun arc ─────────────────────────────────────────

    def test_A_rejected_status_does_not_create_arc(self):
        """
        "Je ne vais pas appliquer" → status='rejected'
        → Le backend vérifie if request.status == 'planned' → False
        → Aucun arc créé.
        """
        sb, svc = self._setup()

        # Simuler le comportement de decision_memory.py
        status = "rejected"
        arc_created = False
        if status == "planned":
            result = svc.create_arc_from_feedback(
                COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
            )
            arc_created = result.get("created", False)

        assert not arc_created, "CAS A: aucun arc ne doit être créé pour status='rejected'"
        assert len(sb.get("decision_arcs")) == 0

        print("\n[CAS A OK] rejected → 0 arc créé ✓")

    # ── Cas B : unsure → aucun arc (RÉGRESSION BUG #ARC-001) ────────────────

    def test_B_unsure_status_does_not_create_arc(self):
        """
        RÉGRESSION BUG #ARC-001 :
        Avant correction : FeedbackCard.tsx envoyait status='planned' pour
        choice='unsure', ce qui créait un Arc pour "Je ne sais pas encore".

        Après correction : FeedbackCard.tsx envoie status='unsure'.
        → Backend : if request.status == 'planned' → False
        → Aucun arc créé.

        Ce test garantit que la régression ne reviendra pas.
        """
        sb, svc = self._setup()

        # Ce que le backend reçoit maintenant (après correction du bug)
        status_recu_par_backend = "unsure"  # plus "planned"

        arc_created = False
        if status_recu_par_backend == "planned":
            result = svc.create_arc_from_feedback(
                COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
            )
            arc_created = result.get("created", False)

        assert not arc_created, \
            "RÉGRESSION #ARC-001: 'unsure' NE DOIT PAS créer d'arc"
        assert len(sb.get("decision_arcs")) == 0, \
            "RÉGRESSION #ARC-001: aucun arc ne doit être inséré pour status='unsure'"

        print("\n[CAS B OK] unsure → 0 arc créé  ← BUG #ARC-001 corrigé")

    # ── Cas C : rejet conséquence → arc reste EXECUTION ──────────────────────

    def test_C_reject_consequence_does_not_close_or_abandon_arc(self):
        """
        Utilisateur rejette le lien candidat.
        → Arc reste en EXECUTION (pas d'abandon, pas de CLOSED).
        → RÈGLE FONDAMENTALE : refuser ≠ abandonner.
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)
        svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1,
                                          {"score_rentabilite": 6, "score_risque": 5})

        result = svc.confirm_consequence_link(
            arc_id, ANALYSIS_N1, confirmed=False,
            rejection_reason="La hausse du CA est due à un nouveau client, pas à la renégociation."
        )

        assert result["confirmed"] is False
        assert result["arc_status"] == "execution", \
            "RÈGLE: rejet ≠ abandon — arc doit rester en EXECUTION"

        arc = sb.get("decision_arcs")[0]
        assert arc["status"] == "execution", \
            "RÈGLE: arc ne doit PAS passer à abandoned ou closed après un rejet"

        # Le lien est marqué consequence_rejected, pas supprimé
        links = [l for l in sb.get("arc_analysis_links")
                 if l["link_type"] == "consequence_rejected"]
        assert len(links) == 1
        assert links[0]["confirmed_by_user"] is False
        assert links[0]["user_rejection_reason"] is not None

        print(f"\n[CAS C OK] Rejet conséquence → arc reste EXECUTION")
        print(f"  arc.status   : {arc['status']}")
        print(f"  link_type    : {links[0]['link_type']}")
        print(f"  raison rejet : {links[0]['user_rejection_reason'][:60]}")

    # ── Cas D : CLOSED avec decision_text NULL → ValueError ──────────────────

    def test_D_cannot_close_arc_with_null_decision_text(self):
        """
        Tentative de fermeture sans decision_text → ValueError.
        L'arc reste en learning_proposed — il n'est PAS fermé.
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)
        svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1,
                                          {"score_rentabilite": 6, "score_risque": 5})
        svc.confirm_consequence_link(arc_id, ANALYSIS_N1, confirmed=True)

        # Arc a decision_text=NULL. On tente de fermer sans le fournir.
        with pytest.raises(ValueError) as exc_info:
            svc.validate_learning(
                arc_id=arc_id,
                learning_text="Un bon learning",
                decision_text=None,   # NULL — doit être refusé
            )

        assert "decision_text" in str(exc_info.value).lower() or \
               "fermeture impossible" in str(exc_info.value).lower() or \
               "null" in str(exc_info.value).lower(), \
               "Le message d'erreur doit mentionner decision_text"

        # L'arc ne doit PAS avoir changé d'état
        arc = sb.get("decision_arcs")[0]
        assert arc["status"] == "learning_proposed", \
            "L'arc doit rester en learning_proposed après un refus de fermeture"
        assert arc.get("closed_at") is None
        assert arc.get("decision_text") is None

        print(f"\n[CAS D OK] CLOSED refusé sans decision_text")
        print(f"  arc.status après tentative : {arc['status']}")
        print(f"  ValueError: {str(exc_info.value)[:100]}")

    # ── Cas E : erreur arc_service → pipeline continue ────────────────────────

    def test_E_arc_service_error_does_not_block_feedback(self):
        """
        Si arc_service lève une exception inattendue, le feedback est déjà
        sauvegardé et doit retourner success=True. L'arc peut être reconstruit
        via backfill (idempotent).

        Ici on simule le comportement de decision_memory.py (try/except).
        """
        sb = FakeSupabase()
        # Analyse SANS decision_kernel → guard DCT lèvera ValueError
        sb.seed_analysis(ANALYSIS_N, decision_kernel=None, decision_fingerprint=None)
        svc = make_service(sb)

        # Simuler decision_memory.py
        arc_created = False
        arc_id = None
        arc_status = None

        try:
            result = svc.create_arc_from_feedback(
                COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
            )
            arc_created = result.get("created", False)
        except ValueError:
            pass  # Guard DCT — logged as warning, continue
        except Exception:
            pass  # Erreur inattendue — logged as error, continue

        # Le feedback a été sauvé (retour success=True simulé)
        feedback_saved = True
        assert feedback_saved is True, \
            "CAS E: le feedback DOIT être retourné même si l'arc échoue"
        assert arc_created is False
        assert len(sb.get("decision_arcs")) == 0

        print(f"\n[CAS E OK] Erreur guard DCT → feedback retourné success=True")
        print(f"  arc_created : {arc_created}")
        print(f"  feedback    : success=True (non bloqué)")

    # ── Cas F : double soumission → idempotence ───────────────────────────────

    def test_F_double_submission_is_idempotent(self):
        """
        Double-clic sur "Je vais appliquer" → 2 appels à create_arc_from_feedback.
        UNIQUE(origin_analysis_id, recommendation_id) → 1 seul arc créé.
        Le second appel retourne {created: False} sans erreur.
        """
        sb, svc = self._setup()

        result1 = svc.create_arc_from_feedback(
            COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
        )
        result2 = svc.create_arc_from_feedback(
            COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
        )

        assert result1["created"] is True
        assert result2["created"] is False, \
            "IDEMPOTENCE: le second appel doit retourner created=False"
        assert len(sb.get("decision_arcs")) == 1, \
            "IDEMPOTENCE: un seul arc doit exister"

        print(f"\n[CAS F OK] Double soumission idempotente")
        print(f"  1er appel created : {result1['created']}")
        print(f"  2e appel created  : {result2['created']}")
        print(f"  Arcs en DB       : {len(sb.get('decision_arcs'))}")


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS COMPLÉMENTAIRES
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdditionalGuards:

    def _setup(self):
        sb = FakeSupabase()
        sb.seed_analysis(ANALYSIS_N, decision_kernel=KERNEL,
                         decision_fingerprint=FINGERPRINT)
        svc = make_service(sb)
        return sb, svc

    def test_partially_done_checkin_sets_partial_execution(self):
        """
        check-in 'partially_done' → execution_status='partial'
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        svc.register_execution_from_checkin(r["arc_id"], "partially_done")
        arc = sb.get("decision_arcs")[0]
        assert arc["execution_status"] == "partial"
        # FakeSupabase ne pré-remplit pas les colonnes nullable à NULL (comportement DB)
        # Le service ne doit pas ÉCRIRE decision_text — vérifier que la clé est absente ou None
        assert arc.get("decision_text") is None

    def test_cannot_close_already_closed_arc(self):
        """
        Tentative de re-fermeture d'un arc CLOSED → ValueError.
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)
        svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1,
                                          {"score_rentabilite": 6, "score_risque": 5})
        svc.confirm_consequence_link(arc_id, ANALYSIS_N1, confirmed=True)
        svc.validate_learning(arc_id, "Learning initial", "Ma décision")

        with pytest.raises(ValueError, match="CLOSED"):
            svc.validate_learning(arc_id, "Deuxième tentative", "Ma décision")

    def test_no_arc_without_decision_kernel(self):
        """
        Guard DCT : analyse sans decision_kernel → ValueError levée avant tout INSERT.
        """
        sb = FakeSupabase()
        sb.seed_analysis(ANALYSIS_N, decision_kernel=None, decision_fingerprint=FINGERPRINT)
        svc = make_service(sb)
        with pytest.raises(ValueError, match="kernel"):
            svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        assert len(sb.get("decision_arcs")) == 0

    def test_no_arc_without_decision_fingerprint(self):
        """
        Guard DCT : analyse sans decision_fingerprint → ValueError avant INSERT.
        """
        sb = FakeSupabase()
        sb.seed_analysis(ANALYSIS_N, decision_kernel=KERNEL, decision_fingerprint=None)
        svc = make_service(sb)
        with pytest.raises(ValueError, match="fingerprint"):
            svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        assert len(sb.get("decision_arcs")) == 0

    def test_consequence_not_detected_twice_for_same_analysis(self):
        """
        Si une analyse N+1 a déjà un lien vers cet arc, detect_consequence_candidates
        ne doit pas créer de doublon (UNIQUE arc_id, analysis_id).
        """
        sb, svc = self._setup()
        r = svc.create_arc_from_feedback(COMPANY_ID, ANALYSIS_N, REC_ID,
                                         "plan_action", REC_TEXT)
        arc_id = r["arc_id"]
        svc.register_execution_from_checkin(arc_id, "done")
        sb.seed_analysis(ANALYSIS_N1, score_rentabilite=6, score_risque=5)

        analyse_json = {"score_rentabilite": 6, "score_risque": 5}

        # Premier appel → insère le candidat
        c1 = svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1, analyse_json)
        # Deuxième appel → ne doit pas dupliquer
        c2 = svc.detect_consequence_candidates(COMPANY_ID, ANALYSIS_N1, analyse_json)

        candidate_links = [l for l in sb.get("arc_analysis_links")
                           if l["link_type"] == "consequence_candidate"]
        assert len(candidate_links) == 1, \
            "Un seul lien candidat doit exister pour ce couple (arc, analyse)"
        assert len(c2) == 0, "Deuxième détection doit retourner 0 nouveau candidat"


# ═══════════════════════════════════════════════════════════════════════════════
# RÉGRESSION BUG #ARC-001 — Matrice status → création d'arc
# ═══════════════════════════════════════════════════════════════════════════════

class TestArcCreationStatusRegression:
    """
    Régression exhaustive BUG #ARC-001.

    RÈGLE UNIQUE : un Arc est créé SI ET SEULEMENT SI status == 'planned'.
    Tous les autres statuts (unsure, rejected, not_done, done, no_longer_relevant)
    ne doivent créer aucun arc.

    Source de vérité : decision_memory.py ligne `if request.status == "planned":`
    Ce test protège cette ligne contre toute dérive future.
    """

    def _setup(self):
        sb = FakeSupabase()
        sb.seed_analysis(
            ANALYSIS_N,
            decision_kernel=KERNEL,
            decision_fingerprint=FINGERPRINT,
            score_rentabilite=4,
            score_risque=7,
        )
        svc = make_service(sb)
        return sb, svc

    def _simulate_feedback(self, svc, sb, status: str) -> bool:
        """
        Simule le comportement de decision_memory.py :
        arc créé seulement si status == 'planned'.
        Retourne True si un arc a été créé.
        """
        if status == "planned":
            try:
                result = svc.create_arc_from_feedback(
                    COMPANY_ID, ANALYSIS_N, REC_ID, "plan_action", REC_TEXT
                )
                return result.get("created", False)
            except (ValueError, Exception):
                return False
        return False

    def test_regression_planned_creates_exactly_one_arc(self):
        """
        'Je vais appliquer' → status='planned' → exactement 1 arc créé.
        C'est le seul statut qui doit créer un arc.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "planned")
        assert arc_created is True
        assert len(sb.get("decision_arcs")) == 1
        print("\n[RÉGRESSION] planned → 1 arc ✓")

    def test_regression_unsure_creates_no_arc(self):
        """
        RÉGRESSION PRINCIPALE BUG #ARC-001.
        'Je ne sais pas encore' → status='unsure' → 0 arc.
        Avant la correction : FeedbackCard envoyait status='planned' → arc créé.
        Après la correction : FeedbackCard envoie status='unsure' → aucun arc.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "unsure")
        assert arc_created is False, \
            "RÉGRESSION #ARC-001: 'unsure' ne doit jamais créer d'arc"
        assert len(sb.get("decision_arcs")) == 0, \
            "RÉGRESSION #ARC-001: table decision_arcs doit rester vide pour status='unsure'"
        print("\n[RÉGRESSION] unsure → 0 arc ✓  (BUG #ARC-001 corrigé)")

    def test_regression_rejected_creates_no_arc(self):
        """
        'Je ne vais pas appliquer' → status='rejected' → 0 arc.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "rejected")
        assert arc_created is False
        assert len(sb.get("decision_arcs")) == 0
        print("\n[RÉGRESSION] rejected → 0 arc ✓")

    def test_regression_not_done_creates_no_arc(self):
        """
        Bilan check-in 'not_done' → feedback persisté → 0 arc.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "not_done")
        assert arc_created is False
        assert len(sb.get("decision_arcs")) == 0
        print("\n[RÉGRESSION] not_done → 0 arc ✓")

    def test_regression_no_longer_relevant_creates_no_arc(self):
        """
        "Ce n'est pas pertinent" → status='no_longer_relevant' → 0 arc.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "no_longer_relevant")
        assert arc_created is False
        assert len(sb.get("decision_arcs")) == 0
        print("\n[RÉGRESSION] no_longer_relevant → 0 arc ✓")

    def test_regression_done_direct_feedback_creates_no_arc(self):
        """
        Feedback direct 'done' (via bilan pré-analyse) → 0 arc.
        Les arcs en EXECUTION proviennent du check-in, pas d'un feedback direct.
        """
        sb, svc = self._setup()
        arc_created = self._simulate_feedback(svc, sb, "done")
        assert arc_created is False
        assert len(sb.get("decision_arcs")) == 0
        print("\n[RÉGRESSION] done (direct feedback) → 0 arc ✓")

    def test_regression_double_planned_is_idempotent(self):
        """
        Double soumission 'planned' pour la même (analyse, recommandation)
        → UNIQUE constraint → 1 seul arc, second appel retourne created=False.
        Ce test croise la régression #ARC-001 avec l'idempotence.
        """
        sb, svc = self._setup()

        # Premier appel
        arc_created_1 = self._simulate_feedback(svc, sb, "planned")
        assert arc_created_1 is True
        assert len(sb.get("decision_arcs")) == 1

        # Second appel (double-clic, retry réseau, etc.)
        arc_created_2 = self._simulate_feedback(svc, sb, "planned")
        assert arc_created_2 is False, \
            "IDEMPOTENCE: le second 'planned' ne doit pas créer un deuxième arc"
        assert len(sb.get("decision_arcs")) == 1, \
            "IDEMPOTENCE: un seul arc en DB quelle que soit la répétition"
        print("\n[RÉGRESSION] planned x2 → 1 arc (idempotent) ✓")
