"""Deterministic, synthetic-only exports for a persisted V1 governed envelope.

These renderers deliberately consume the immutable governed envelope rather
than the legacy AnalysisResult projection.  They perform no provider call and
do not create decisions or facts that are absent from the envelope.
"""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from services.v1_analysis_contract import GovernedAnalysisEnvelope

_NAVY = "183B56"
_BLUE = "2A6F97"
_PALE = "EAF2F8"
_TEXT = "243746"
_ORANGE = "F28C28"
_SYNTHETIC_PROVIDER = "Fournisseur simulé local"
_NETWORK_DISCLOSURE = "Aucun réseau externe n'a été utilisé"


def _durable_analysis_id(analysis_id: str) -> str:
    value = str(analysis_id).strip()
    if not value:
        raise ValueError("analysis_id is required for governed exports")
    return value


def _neutralize_spreadsheet_formula(value: object) -> object:
    """Keep provider-authored text inert when Excel opens the workbook."""

    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _fact_map(envelope: GovernedAnalysisEnvelope) -> dict[str, str]:
    return {
        fact.fact_id: f"{fact.metric} ({fact.period}, {fact.source_sheet_ref}/{fact.source_field})"
        for fact in envelope.source_facts.facts
    }


def _refs(ids: tuple[str, ...], fact_map: dict[str, str]) -> str:
    return "; ".join(f"{fact_id}: {fact_map[fact_id]}" for fact_id in ids)


def generate_governed_excel(envelope: GovernedAnalysisEnvelope, analysis_id: str) -> bytes:
    """Render an auditable workbook from the validated envelope only."""

    envelope = GovernedAnalysisEnvelope.model_validate(envelope)
    analysis_id = _durable_analysis_id(analysis_id)
    analysis, source = envelope.governed_analysis, envelope.source_facts
    fact_map = _fact_map(envelope)
    wb = Workbook()
    summary = wb.active
    summary.title = "Synthese"
    summary.sheet_view.showGridLines = False
    summary.append(["Pepperyn - Analyse financiere gouvernee"])
    summary.append(["Perimetre", "Donnees synthetiques uniquement"])
    summary.append(["Identifiant durable de l'analyse", analysis_id])
    summary.append(["Fournisseur", _SYNTHETIC_PROVIDER])
    summary.append(["Reseau externe", _NETWORK_DISCLOSURE])
    summary.append(["Periode", source.current_period or "UNKNOWN"])
    summary.append(["Statut de comprehension", source.status])
    summary.append(["Empreinte source SHA-256", source.source_representation_sha256])
    summary.append([])
    summary.append(["Diagnostic (inference)", analysis.executive_diagnosis])
    summary.append(["Faits cites", _refs(analysis.diagnosis_fact_ids, fact_map)])
    summary.append([])
    summary.append(["Limite", "Les recommandations IA ne constituent pas des decisions confirmees."])

    facts = wb.create_sheet("Faits sources")
    facts.append(["Fact ID", "Metrique", "Valeur", "Unite", "Periode", "Feuille source", "Champ source"])
    for fact in source.facts:
        facts.append([fact.fact_id, fact.metric, fact.value, fact.unit, fact.period,
                      fact.source_sheet_ref, fact.source_field])

    reasoning = wb.create_sheet("Inferences")
    reasoning.append(["Type", "Contenu", "Confiance", "Faits cites", "Validations requises"])
    for item in analysis.observations:
        reasoning.append([f"Observation source-matched - severite inferentielle {item.severity}",
                          f"{item.metric} = {item.observed_value}", None,
                          _refs((item.fact_id,), fact_map), ""])
    for item in analysis.dimension_assessments:
        reasoning.append([f"Dimension {item.scope} - score inferentiel {item.score}/10", item.rationale,
                          item.confidence, _refs(item.fact_ids, fact_map), "; ".join(item.validation_required)])
    for item in analysis.inferences:
        reasoning.append(["Inference", item.statement, item.confidence,
                          _refs(item.fact_ids, fact_map), "; ".join(item.validation_required)])
    for item in analysis.contradictions:
        reasoning.append(["Contradiction", item.statement, None, _refs(item.fact_ids, fact_map), ""])

    recommendations = wb.create_sheet("Recommandations")
    recommendations.append(["Priorite proposee", "Action proposee", "Rationale", "Faits cites", "Prerequis"])
    for item in analysis.recommendations:
        recommendations.append([item.priority, item.action, item.rationale,
                                _refs(item.fact_ids, fact_map), "; ".join(item.prerequisite_validation)])

    unknowns = wb.create_sheet("UNKNOWN")
    unknowns.append(["Materialite", "Question non resolue"])
    for item in analysis.unknowns:
        unknowns.append([item.materiality, item.question])
    for item in source.unknowns:
        unknowns.append(["SOURCE", item])

    for ws in wb.worksheets:
        ws.freeze_panes = "A2" if ws.max_row > 1 else None
        ws.auto_filter.ref = ws.dimensions if ws.max_column > 1 and ws.max_row > 1 else None
        for row in ws.iter_rows():
            for cell in row:
                cell.value = _neutralize_spreadsheet_formula(cell.value)
                cell.font = Font(name="Arial", size=10, color=_TEXT, bold=cell.font.bold)
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        for cell in ws[1]:
            cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor=_NAVY)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        for column in ws.columns:
            letter = column[0].column_letter
            longest = min(max((len(str(cell.value or "")) for cell in column), default=10), 65)
            ws.column_dimensions[letter].width = max(12, longest + 2)
    summary.freeze_panes = None
    summary.auto_filter.ref = None
    summary.merge_cells("A1:B1")
    summary["A1"].font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    summary["A10"].fill = PatternFill("solid", fgColor=_PALE)
    summary["A10"].font = Font(name="Arial", bold=True, color=_NAVY)

    output = BytesIO()
    wb.save(output)
    return output.getvalue()


def generate_governed_pdf(envelope: GovernedAnalysisEnvelope, analysis_id: str) -> bytes:
    """Render a professional, bounded PDF from the validated envelope only."""

    envelope = GovernedAnalysisEnvelope.model_validate(envelope)
    analysis_id = _durable_analysis_id(analysis_id)
    analysis, source = envelope.governed_analysis, envelope.source_facts
    fact_map = _fact_map(envelope)
    output = BytesIO()
    styles = getSampleStyleSheet()
    title = ParagraphStyle("PepperynTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                           fontSize=18, leading=22, textColor=colors.HexColor(f"#{_NAVY}"), alignment=TA_LEFT)
    heading = ParagraphStyle("PepperynHeading", parent=styles["Heading2"], fontName="Helvetica-Bold",
                             fontSize=12, leading=15, spaceBefore=8, spaceAfter=5,
                             textColor=colors.HexColor(f"#{_BLUE}"))
    body = ParagraphStyle("PepperynBody", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=9, leading=13, textColor=colors.HexColor(f"#{_TEXT}"))
    small = ParagraphStyle("PepperynSmall", parent=body, fontSize=7.5, leading=10)
    table_header = ParagraphStyle("PepperynTableHeader", parent=small, fontName="Helvetica-Bold",
                                  textColor=colors.white)

    def p(value: object, style=body) -> Paragraph:
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), style)

    def section(label: str) -> list[object]:
        return [Paragraph(label, heading)]

    story: list[object] = [Paragraph("Pepperyn - Analyse financiere gouvernee", title), Spacer(1, 3 * mm)]
    metadata = [
        [p("Perimetre", small), p("Donnees synthetiques uniquement", small)],
        [p("Identifiant durable de l'analyse", small), p(analysis_id, small)],
        [p("Fournisseur", small), p(_SYNTHETIC_PROVIDER, small)],
        [p("Reseau externe", small), p(_NETWORK_DISCLOSURE, small)],
        [p("Periode", small), p(source.current_period or "UNKNOWN", small)],
        [p("Statut de comprehension", small), p(source.status, small)],
        [p("Empreinte source SHA-256", small), p(source.source_representation_sha256, small)],
    ]
    table = Table(metadata, colWidths=[43 * mm, 137 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{_PALE}")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(f"#{_TEXT}")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CAD6DF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.extend([table, *section("Diagnostic - inference"), p(analysis.executive_diagnosis),
                  p("Faits cites: " + _refs(analysis.diagnosis_fact_ids, fact_map), small)])

    story.extend(section("Faits sources"))
    fact_rows = [[p(x, table_header) for x in ("Fact ID", "Metrique", "Valeur", "Unite", "Periode", "Source")]]
    for fact in source.facts:
        fact_rows.append([p(fact.fact_id, small), p(fact.metric, small), p(fact.value, small), p(fact.unit, small),
                          p(fact.period, small), p(f"{fact.source_sheet_ref}/{fact.source_field}", small)])
    facts_table = Table(fact_rows, repeatRows=1, colWidths=[25*mm, 31*mm, 23*mm, 16*mm, 19*mm, 52*mm])
    facts_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{_NAVY}")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CAD6DF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F9FB")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.extend([facts_table, *section("Observations gouvernees")])
    for item in analysis.observations:
        story.extend([p(f"Observation source-matched: {item.metric} = {item.observed_value}"),
                      p(f"Severite inferentielle: {item.severity}"),
                      p("Fait cite: " + _refs((item.fact_id,), fact_map), small), Spacer(1, 2*mm)])
    story.extend(section("Inferences et validations"))
    for item in analysis.dimension_assessments:
        story.append(KeepTogether([
            p(f"Dimension {item.scope} - score inferentiel {item.score}/10 (confiance {item.confidence}%)"),
            p(item.rationale), p("Faits cites: " + _refs(item.fact_ids, fact_map), small),
            p("Validations requises: " + "; ".join(item.validation_required), small), Spacer(1, 2*mm),
        ]))
    for item in analysis.inferences:
        story.append(KeepTogether([
            p(f"Inference (confiance {item.confidence}%): {item.statement}"),
            p("Faits cites: " + _refs(item.fact_ids, fact_map), small),
            p("Validations requises: " + "; ".join(item.validation_required), small), Spacer(1, 2*mm),
        ]))

    story.extend(section("UNKNOWN et contradictions"))
    if not analysis.unknowns and not source.unknowns and not analysis.contradictions:
        story.append(p("Aucun element declare."))
    for item in analysis.unknowns:
        story.append(p(f"UNKNOWN ({item.materiality}): {item.question}"))
    for item in source.unknowns:
        story.append(p(f"UNDERSTANDING UNKNOWN: {item}"))
    for item in analysis.contradictions:
        story.extend([p("CONTRADICTION: " + item.statement), p("Faits cites: " + _refs(item.fact_ids, fact_map), small)])

    story.extend(section("Recommandations proposees"))
    for item in analysis.recommendations:
        story.extend([p(f"{item.priority} - {item.action}"), p(item.rationale),
                      p("Faits cites: " + (_refs(item.fact_ids, fact_map) if item.fact_ids else "Aucun"), small),
                      p("Prerequis: " + ("; ".join(item.prerequisite_validation) or "Aucun"), small), Spacer(1, 2*mm)])
    story.extend([Spacer(1, 3*mm), p("Les recommandations IA ne constituent pas des decisions confirmees.", small)])

    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=14*mm, bottomMargin=14*mm,
                            title="Pepperyn - Analyse financiere gouvernee")
    doc.build(story)
    return output.getvalue()


def generate_governed_pptx(envelope: GovernedAnalysisEnvelope, analysis_id: str) -> bytes:
    """Render a governed CODIR deck without reinterpreting provider output.

    The deck consumes only the immutable envelope. Long sections create
    continuation slides instead of losing content or silently shrinking it.
    """

    envelope = GovernedAnalysisEnvelope.model_validate(envelope)
    analysis_id = _durable_analysis_id(analysis_id)
    analysis, source = envelope.governed_analysis, envelope.source_facts
    fact_map = _fact_map(envelope)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    def color(hex_value: str) -> RGBColor:
        return RGBColor.from_string(hex_value)

    def add_text(slide, text: str, *, left: float, top: float, width: float,
                 height: float, size: int, bold: bool = False,
                 text_color: str = _TEXT, align=PP_ALIGN.LEFT):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        frame = box.text_frame
        frame.clear()
        frame.word_wrap = True
        paragraph = frame.paragraphs[0]
        paragraph.text = text
        paragraph.alignment = align
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = color(text_color)
        return box

    def add_header(slide, title: str, kicker: str = "PEPPERYN | CODIR") -> None:
        add_text(slide, kicker, left=0.65, top=0.35, width=5.2, height=0.3,
                 size=10, bold=True, text_color=_BLUE)
        add_text(slide, title, left=0.65, top=0.75, width=12.0, height=0.7,
                 size=28, bold=True, text_color=_NAVY)

    def split_entry(entry: str, limit: int = 380) -> list[str]:
        """Split long content and repeat its epistemic classification."""

        first = entry.find(" | ")
        second = entry.find(" | ", first + 3) if first >= 0 else -1
        prefix_end = second if entry.startswith(("P1 | ", "P2 | ", "P3 | ")) else first
        if prefix_end < 0:
            label, remaining = "CONTENU", entry
        else:
            label, remaining = entry[:prefix_end], entry[prefix_end + 3:]
        first_prefix = f"{label} | "
        next_prefix = f"{label} (suite) | "
        chunks: list[str] = []
        prefix = first_prefix
        while len(prefix) + len(remaining) > limit:
            available = limit - len(prefix)
            cut = remaining.rfind(" ", available // 2, available + 1)
            cut = cut + 1 if cut >= 0 else available
            chunks.append(prefix + remaining[:cut])
            remaining = remaining[cut:]
            prefix = next_prefix
        if remaining or not chunks:
            chunks.append(prefix + remaining)
        return chunks

    def paginate(title: str, entries: list[str], *, empty: str = "Aucun element declare.") -> None:
        entries = entries or [empty]
        chunks = [chunk for entry in entries for chunk in split_entry(entry)]
        pages: list[list[tuple[str, float]]] = []
        page: list[tuple[str, float]] = []
        used_height = 0.0
        for chunk in chunks:
            visual_lines = max(1, (len(chunk) + 94) // 95)
            height = 0.28 + visual_lines * 0.24
            if page and used_height + height + 0.13 > 5.15:
                pages.append(page)
                page, used_height = [], 0.0
            page.append((chunk, height))
            used_height += height + 0.13
        if page:
            pages.append(page)
        for page_index, page_entries in enumerate(pages):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            add_header(slide, title if page_index == 0 else f"{title} (suite)")
            top = 1.62
            for entry, height in page_entries:
                add_text(slide, entry, left=0.9, top=top, width=11.6,
                         height=height, size=15)
                top += height + 0.13
            add_text(slide, "Les analyses et recommandations restent soumises aux validations indiquees.",
                     left=0.65, top=7.05, width=12, height=0.25, size=9, text_color=_BLUE)

    cover = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(cover, "PEPPERYN", left=0.75, top=0.55, width=3.0, height=0.5,
             size=17, bold=True, text_color=_BLUE)
    add_text(cover, "Analyse financiere\npour decision CODIR", left=0.75, top=1.75,
             width=8.5, height=1.8, size=34, bold=True, text_color=_NAVY)
    add_text(cover, f"Periode {source.current_period or 'UNKNOWN'} | Donnees synthetiques uniquement",
             left=0.78, top=3.9, width=8.5, height=0.45, size=16, text_color=_TEXT)
    add_text(cover, f"Analyse {analysis_id} | {_SYNTHETIC_PROVIDER} | {_NETWORK_DISCLOSURE}",
             left=0.78, top=4.35, width=11.8, height=0.45, size=11, text_color=_BLUE)
    add_text(cover, "Recommandations proposees. Aucune decision n'est presentee comme confirmee.",
             left=0.78, top=5.0, width=10.8, height=0.6, size=15, bold=True,
             text_color=_ORANGE)
    add_text(cover, f"Source SHA-256 {source.source_representation_sha256}",
             left=0.78, top=6.7, width=11.8, height=0.25, size=8, text_color=_BLUE)

    paginate("Situation executive", [
        f"INFERENCE | {analysis.executive_diagnosis}",
        "FAITS CITES | " + _refs(analysis.diagnosis_fact_ids, fact_map),
    ])
    paginate("Constats financiers", [
        f"OBSERVATION SOURCE | {item.metric} = {item.observed_value} | "
        f"Severite inferentielle {item.severity} | {_refs((item.fact_id,), fact_map)}"
        for item in analysis.observations
    ])
    paginate("Evaluation et hypotheses", [
        f"DIMENSION {item.scope} | Score inferentiel {item.score}/10 | Confiance {item.confidence}% | "
        f"{item.rationale} | Faits: {_refs(item.fact_ids, fact_map)} | "
        f"Validations: {'; '.join(item.validation_required)}"
        for item in analysis.dimension_assessments
    ] + [
        f"INFERENCE | Confiance {item.confidence}% | {item.statement} | "
        f"Faits: {_refs(item.fact_ids, fact_map)} | Validations: {'; '.join(item.validation_required)}"
        for item in analysis.inferences
    ])
    paginate("Incertitudes et contradictions", [
        f"UNKNOWN {item.materiality} | {item.question}" for item in analysis.unknowns
    ] + [
        f"UNDERSTANDING UNKNOWN | {item}" for item in source.unknowns
    ] + [
        f"CONTRADICTION | {item.statement} | Faits: {_refs(item.fact_ids, fact_map)}"
        for item in analysis.contradictions
    ])
    paginate("Recommandations proposées", [
        f"{item.priority} | ACTION PROPOSEE | {item.action} | Rationale: {item.rationale} | "
        f"Faits: {_refs(item.fact_ids, fact_map) if item.fact_ids else 'Aucun'} | "
        f"Prerequis: {'; '.join(item.prerequisite_validation) or 'Aucun'}"
        for item in analysis.recommendations
    ])

    output = BytesIO()
    prs.save(output)
    return output.getvalue()
