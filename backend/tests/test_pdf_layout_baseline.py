"""
PEPPERYN QUALITY CONTRACT — PDF LAYOUT BASELINE v1.0

Ce test garantit que le layout du Rapport Exécutif PDF reste identique
entre les versions. Toute déviation par rapport aux constantes de
config/pdf_layout.py constitue une régression.

RÈGLE : Ces tests ne peuvent être modifiés que par décision CTO explicite.
"""
import io
import subprocess
import tempfile
import os
import pytest

import sys
sys.path.insert(0, "/sessions/modest-sleepy-hypatia/mnt/Pepperyn/backend")

from tests.test_rule_001_zero_manual_intervention import OPTILUX
from services.export_pdf_service import generate_pdf_report
from config.pdf_layout import (
    HEX_NAVY, HEX_BLUE, HEX_RED, HEX_AMBER, HEX_GREEN,
    HEX_GRAY, HEX_LGRAY, HEX_LBGRAY,
    PAGE_W_PT, PAGE_H_PT, MARGIN_MM, TOP_MARGIN_MM, BOT_MARGIN_MM,
    PAGES_FULL, PAGES_SLIM,
    PAGE_SEQUENCE, PHASE_LABELS,
)


# ─── FIXTURE ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def pdf_bytes():
    """Génère le PDF une seule fois pour toute la suite."""
    return generate_pdf_report(OPTILUX)


@pytest.fixture(scope="module")
def pdf_text_by_page(pdf_bytes):
    """
    Extrait le texte page par page via pdftotext.
    Retourne un dict {page_number (1-indexed): text}.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        tmp = f.name
    try:
        pages = {}
        for p in range(1, PAGES_FULL + 1):
            r = subprocess.run(
                ["pdftotext", "-layout", f"-f", str(p), f"-l", str(p), tmp, "-"],
                capture_output=True, text=True,
            )
            pages[p] = r.stdout
        return pages
    finally:
        os.unlink(tmp)


def _page_count(pdf_bytes: bytes) -> int:
    """Retourne le nombre de pages du PDF via pdfinfo."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        tmp = f.name
    try:
        r = subprocess.run(["pdfinfo", tmp], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
        return -1
    finally:
        os.unlink(tmp)


# ─── TESTS PALETTE ────────────────────────────────────────────────────────────

class TestPaletteConstants:
    """Vérifie que les valeurs hexadécimales de la palette McKinsey ne dérivent pas."""

    def test_navy(self):
        assert HEX_NAVY == "#0A2540", "Couleur NAVY déviée — modifier config/pdf_layout.py pour officialiser."

    def test_blue(self):
        assert HEX_BLUE == "#1B4F8A"

    def test_red(self):
        assert HEX_RED == "#C0392B", "Rouge d'urgence modifié — impact visuel critique."

    def test_green(self):
        assert HEX_GREEN == "#1D6A3A", "Vert de gain modifié — impact visuel critique."

    def test_amber(self):
        assert HEX_AMBER == "#B8763A"

    def test_gray(self):
        assert HEX_GRAY == "#6B7280"

    def test_lgray(self):
        assert HEX_LGRAY == "#D8E3E9"

    def test_lbgray(self):
        assert HEX_LBGRAY == "#F8FAFB"


# ─── TESTS GÉOMÉTRIE ──────────────────────────────────────────────────────────

class TestGeometryConstants:

    def test_margin_mm(self):
        assert MARGIN_MM == 18

    def test_top_margin_mm(self):
        assert TOP_MARGIN_MM == 22

    def test_bot_margin_mm(self):
        assert BOT_MARGIN_MM == 16

    def test_page_width_pt(self):
        assert PAGE_W_PT == 595

    def test_page_height_pt(self):
        assert PAGE_H_PT == 842


# ─── TESTS NOMBRE DE PAGES ────────────────────────────────────────────────────

class TestPageCount:

    def test_full_page_count(self, pdf_bytes):
        """Avec financial_statements complets, le PDF doit avoir exactement PAGES_FULL pages."""
        count = _page_count(pdf_bytes)
        assert count == PAGES_FULL, (
            f"PDF : {count} pages obtenues, {PAGES_FULL} attendues. "
            f"Une page a été ajoutée ou supprimée — décision CTO requise."
        )


# ─── TESTS SÉQUENCE DES PAGES ────────────────────────────────────────────────

class TestPageSequence:
    """
    Vérifie que chaque page contient le titre de section attendu.
    Le texte de référence est le TITRE_SECTION du PAGE_SEQUENCE.
    """

    # Pages à vérifier (on exclut cover=1 et back=16 dont le texte est moins structuré)
    CHECKS = {
        2:  "VERDICT EXÉCUTIF",
        3:  "OÙ VOTRE CAPITAL EST SOUS-EMPLOYÉ",
        4:  "COÛT DE L'INACTION",
        5:  "DÉCISIONS PRIORITAIRES",
        6:  "COMMENT PEPPERYN A RAISONNÉ",
        7:  "VALEUR CRÉÉE SI VOUS AGISSEZ",
        8:  "CALENDRIER D'ALLOCATION",
        9:  "SCÉNARIOS",
        10: "RISQUES À SURVEILLER",
        11: "MES KPIs DE PILOTAGE",
        12: "TRANSPARENCE & FIABILIT",
    }

    @pytest.mark.parametrize("page_num,expected_text", CHECKS.items())
    def test_page_contains_section_title(self, pdf_text_by_page, page_num, expected_text):
        text = pdf_text_by_page.get(page_num, "")
        assert expected_text in text, (
            f"Page {page_num} : titre attendu \"{expected_text}\" introuvable. "
            f"Une page a été déplacée ou renommée — décision CTO requise."
        )


# ─── TESTS PAGE 6 — PHASES AGENT ─────────────────────────────────────────────

class TestPageReasoningPhases:
    """
    Vérifie que les 4 labels de phase apparaissent bien en page 6 (Raisonnement).
    Ces labels sont la source de vérité cross-livrables pour l'audit de cohérence.
    """

    @pytest.mark.parametrize("phase_label", PHASE_LABELS)
    def test_phase_label_present_on_page_6(self, pdf_text_by_page, phase_label):
        text = pdf_text_by_page.get(6, "")
        # pdftotext peut couper les longues lignes — on cherche les 30 premiers chars
        snippet = phase_label[:30]
        assert snippet in text, (
            f"Page 6 — label phase introuvable : \"{phase_label[:50]}...\". "
            f"Modifier config/pdf_layout.py pour officialiser le nouveau libellé."
        )


# ─── TESTS INTÉGRITÉ MINIMALE ────────────────────────────────────────────────

class TestMinimalIntegrity:

    def test_pdf_non_empty(self, pdf_bytes):
        assert len(pdf_bytes) > 10_000, "PDF trop petit — génération probablement échouée."

    def test_pdf_magic_bytes(self, pdf_bytes):
        assert pdf_bytes[:4] == b"%PDF", "Les premiers octets ne sont pas un PDF valide."

    def test_no_manque_data_in_key_pages(self, pdf_text_by_page):
        """Les pages clés ne doivent pas contenir le fallback 'données insuffisantes'."""
        forbidden = "données insuffisantes"
        for page_num in range(2, 12):
            text = pdf_text_by_page.get(page_num, "").lower()
            assert forbidden not in text, (
                f"Page {page_num} : phrase fallback interdite détectée. "
                f"Utiliser _MANQUE_DATA ou _MANQUE_DATA_SHORT à la place."
            )
