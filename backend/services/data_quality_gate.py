"""
Data Quality Gate — Pepperyn

Couche de pré-validation obligatoire avant toute analyse financière.
Utilise pepperyn_data_robustness comme boîte noire pour les fichiers ERP/transactionnels.
Ajoute une détection structurelle pour les documents P&L / Bilan / Budget.

Flux :
  Excel uploadé (bytes)
    → save temp file
    → import_finance_excel(path)
    → détection type (ERP vs structural)
    → QualityGateResult {can_analyze, status, score, mapping_summary, anomalies, ...}

Statuts :
  "ok"      → analyse normale, section fiabilité ajoutée au rapport
  "warning" → analyse avec avertissements explicites
  "blocked" → PAS d'analyse financière, rapport qualité uniquement
"""
import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Mots-clés structurels reconnus dans les P&L / Bilans francophones ──────

_STRUCTURAL_KEYWORDS = [
    "chiffre d'affaires", "chiffre affaires", "ca net", "ca total",
    "résultat", "resultat", "résultat net", "resultat net",
    "ebitda", "ebit", "marge brute", "marge operationnelle",
    "charges", "coûts", "couts", "charges fixes", "masse salariale",
    "amortissement", "dotations", "provisions",
    "budget", "prévision", "prevision", "forecast", "réel", "reel",
    "bilan", "actif", "passif", "capitaux propres",
    "trésorerie", "tresorerie", "flux",
    "total produits", "total charges", "produits exploitation",
    "charges exploitation", "charges financières",
]

_STRUCTURAL_KEYWORDS_EN = [
    "revenue", "net revenue", "gross margin", "operating income",
    "net income", "ebitda", "operating expenses", "cost of goods",
    "total sales", "net sales",
]


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QualityGateResult:
    """Résultat unifié du gate de qualité des données."""
    can_analyze: bool
    status: str                   # "ok" | "warning" | "blocked"
    score_data: int               # Score fiabilité données (0-100)
    document_format: str = "unknown"   # "erp_transactional" | "structural_pl" | "unknown"
    mapping_summary: List[str] = field(default_factory=list)
    anomalies: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    blocking_reason: Optional[str] = None
    sheets_detected: List[str] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """Injecte le contexte qualité dans le prompt LLM Claude."""
        icon = {"ok": "✅", "warning": "⚠️", "blocked": "🚫"}.get(self.status, "ℹ️")
        lines = [
            "═══ FIABILITÉ DES DONNÉES SOURCE ═══",
            f"{icon} Statut qualité : {self.status.upper()} | Score : {self.score_data}/100",
            f"Format détecté : {self.document_format}",
        ]
        if self.mapping_summary:
            lines.append("Mapping détecté : " + " | ".join(self.mapping_summary[:4]))
        if self.anomalies:
            lines.append("Anomalies : " + " ; ".join(self.anomalies[:4]))
        if self.assumptions:
            lines.append("Hypothèses retenues : " + " ; ".join(self.assumptions[:3]))
        if self.status == "warning":
            lines.append(
                "IMPORTANT : Ces données sont partiellement fiables. "
                "Tu DOIS mentionner explicitement les limites identifiées dans ton analyse. "
                "Ne présente pas comme certaine une conclusion qui repose sur des données douteuses."
            )
        lines.append("═══ FIN FIABILITÉ ═══")
        return "\n".join(lines)

    def to_report_section(self) -> dict:
        """Dictionnaire prêt pour injection dans PDF / Excel / PPTX."""
        return {
            "score_data": self.score_data,
            "status": self.status,
            "document_format": self.document_format,
            "mapping_summary": self.mapping_summary,
            "anomalies": self.anomalies,
            "assumptions": self.assumptions,
            "blocking_reason": self.blocking_reason,
            "sheets_detected": self.sheets_detected,
        }


# ─────────────────────────────────────────────────────────────────────────────

def _is_structural_document(raw_sheets: dict) -> bool:
    """Détecte si le fichier est un document structurel (P&L, bilan, budget)."""
    for sheet_name, df in raw_sheets.items():
        # Chercher les mots-clés dans le nom de la feuille
        sn = sheet_name.lower()
        for kw in ["compte de résultat", "compte resultat", "p&l", "income", "bilan",
                   "budget", "prevision", "prévision", "tableau de bord", "dashboard"]:
            if kw in sn:
                return True
        # Chercher les mots-clés dans les cellules du DataFrame
        try:
            all_text = " ".join(
                str(v).lower()
                for col in df.columns
                for v in df[col].dropna().astype(str)
            ) + " " + " ".join(str(c).lower() for c in df.columns)
            found = sum(1 for kw in _STRUCTURAL_KEYWORDS + _STRUCTURAL_KEYWORDS_EN if kw in all_text)
            if found >= 2:
                return True
        except Exception:
            pass
    return False


def _validate_structural(raw_sheets: dict) -> QualityGateResult:
    """
    Valide un document structurel (P&L, bilan).
    Retourne un QualityGateResult basé sur des heuristiques.
    """
    sheets = list(raw_sheets.keys())
    anomalies = []
    assumptions = []
    mapping_summary = []
    penalty = 0

    if not raw_sheets:
        return QualityGateResult(
            can_analyze=False,
            status="blocked",
            score_data=0,
            document_format="unknown",
            blocking_reason="Le fichier Excel est vide ou illisible.",
        )

    total_numeric_values = 0
    for sheet_name, df in raw_sheets.items():
        if df.empty:
            anomalies.append(f"Feuille '{sheet_name}' vide")
            penalty += 10
            continue

        # Vérifier présence de données numériques (pandas peut typer en object à cause des titres)
        import pandas as pd
        numeric_count = 0
        for col in df.columns:
            converted = pd.to_numeric(df[col], errors="coerce")
            numeric_count += int(converted.notna().sum())
        total_numeric_values += numeric_count

        if numeric_count == 0:
            anomalies.append(f"Feuille '{sheet_name}' : aucune valeur numérique trouvée")
            penalty += 20

        # Détecter mots-clés financiers
        all_text = " ".join(str(c).lower() for c in df.columns)
        try:
            all_text += " " + " ".join(
                str(v).lower()
                for col in df.columns
                for v in df[col].dropna().astype(str).head(50)
            )
        except Exception:
            pass

        kw_found = [kw for kw in _STRUCTURAL_KEYWORDS if kw in all_text]
        if kw_found:
            mapping_summary.append(f"'{sheet_name}' : {', '.join(kw_found[:3])}")
        elif numeric_vals > 0:
            mapping_summary.append(f"'{sheet_name}' : données numériques non étiquetées")
            assumptions.append(f"Les colonnes de '{sheet_name}' n'ont pas été identifiées automatiquement.")
            penalty += 8

    if total_numeric_values == 0:
        return QualityGateResult(
            can_analyze=False,
            status="blocked",
            score_data=0,
            document_format="structural_pl",
            blocking_reason="Aucune donnée numérique détectée dans le fichier. "
                            "L'analyse financière est impossible sans chiffres.",
            sheets_detected=sheets,
        )

    score = max(0, 100 - penalty)

    if score >= 80:
        status = "ok"
        can_analyze = True
    elif score >= 50:
        status = "warning"
        can_analyze = True
        assumptions.append(
            "Certaines données n'ont pas pu être mappées automatiquement. "
            "L'analyse s'appuie sur les données brutes détectées."
        )
    else:
        status = "warning"
        can_analyze = True
        anomalies.append("Structure du fichier partiellement reconnue — l'analyse peut être incomplète.")
        assumptions.append("Analyse effectuée sur données partielles. Résultats à valider.")

    return QualityGateResult(
        can_analyze=can_analyze,
        status=status,
        score_data=score,
        document_format="structural_pl",
        mapping_summary=mapping_summary,
        anomalies=anomalies,
        assumptions=assumptions,
        sheets_detected=sheets,
    )


def _validate_erp(tables: dict, mapping: dict, quality_report) -> QualityGateResult:
    """Convertit le résultat du module ERP en QualityGateResult unifié."""
    mapping_summary = []
    for table_name, mr in mapping.items():
        cols = ", ".join(f"{k}→'{v}'" for k, v in mr.column_mapping.items())
        missing = mr.missing_required_fields
        entry = f"{table_name} (feuille '{mr.sheet_name}'): {cols}"
        if missing:
            entry += f" [manquant: {', '.join(missing)}]"
        mapping_summary.append(entry)

    anomalies = [
        f"[{i.severity}] {i.table}.{i.field}: {i.message}"
        for i in (quality_report.issues or [])
    ]
    assumptions = list(quality_report.assumptions or [])
    score = quality_report.score

    # blocked si le module le dit OU si score très bas sans aucune table
    if quality_report.status == "blocked" or (not tables and score < 50):
        return QualityGateResult(
            can_analyze=False,
            status="blocked",
            score_data=score,
            document_format="erp_transactional",
            mapping_summary=mapping_summary,
            anomalies=anomalies,
            assumptions=assumptions,
            blocking_reason=(
                "Les données ERP sont insuffisantes ou trop incohérentes pour générer "
                "un rapport financier fiable. Veuillez fournir un fichier complet."
            ),
        )

    if score >= 85:
        status = "ok"
    elif score >= 65:
        status = "warning"
    else:
        status = "warning"
        anomalies.append(
            "Score de fiabilité bas — l'analyse peut être biaisée. "
            "Vérifiez les données sources avant de prendre une décision."
        )

    return QualityGateResult(
        can_analyze=True,
        status=status,
        score_data=score,
        document_format="erp_transactional",
        mapping_summary=mapping_summary,
        anomalies=anomalies,
        assumptions=assumptions,
    )


# ─────────────────────────────────────────────────────────────────────────────

def validate_excel_before_analysis(file_bytes: bytes, filename: str) -> QualityGateResult:
    """
    Point d'entrée principal du gate.

    Reçoit les bytes du fichier uploadé.
    Retourne un QualityGateResult qui détermine si l'analyse peut continuer.

    Pour les fichiers non-Excel (CSV, PDF) : gate non applicable → "ok" avec note.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # ── Non-Excel : gate non applicable ──────────────────────────────────────
    if ext not in ("xlsx", "xls"):
        return QualityGateResult(
            can_analyze=True,
            status="ok",
            score_data=85,
            document_format=f"non_excel_{ext}",
            assumptions=[
                f"Fichier {ext.upper()} : validation structurelle non disponible. "
                "L'analyse s'appuie sur le contenu brut extrait."
            ],
        )

    # ── Excel : écriture temp + import_finance_excel ──────────────────────────
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        from pepperyn_data_robustness import import_finance_excel
        result = import_finance_excel(tmp_path)

        tables = {
            k: getattr(result.dataset, k)
            for k in ("sales", "purchases", "fixed_costs", "budget", "cash")
        }
        non_empty_tables = {k: v for k, v in tables.items() if v is not None and not v.empty}

        logger.info(
            f"[QUALITY GATE] {filename} — tables détectées: {list(non_empty_tables.keys())} "
            f"| score module: {result.quality.score} | status module: {result.quality.status}"
        )

        # ── Aucune table ERP détectée → tenter détection structurelle ─────────
        if not non_empty_tables:
            if _is_structural_document(result.dataset.raw_sheets):
                gate = _validate_structural(result.dataset.raw_sheets)
            else:
                # Fichier Excel avec contenu non reconnu
                if result.dataset.raw_sheets:
                    gate = _validate_structural(result.dataset.raw_sheets)
                else:
                    gate = QualityGateResult(
                        can_analyze=False,
                        status="blocked",
                        score_data=0,
                        document_format="unknown",
                        blocking_reason=(
                            "Impossible de lire le contenu du fichier Excel. "
                            "Vérifiez que le fichier n'est pas corrompu ou protégé."
                        ),
                    )
        else:
            # Tables ERP détectées → validation ERP
            gate = _validate_erp(non_empty_tables, result.mapping, result.quality)
            gate.sheets_detected = list(result.dataset.raw_sheets.keys())

        return gate

    except ImportError:
        # Module non disponible — gate désactivé, on laisse passer
        logger.warning("[QUALITY GATE] Module pepperyn_data_robustness non disponible — gate désactivé")
        return QualityGateResult(
            can_analyze=True,
            status="ok",
            score_data=70,
            document_format="unknown",
            assumptions=["Validation des données non disponible (module manquant)."],
        )
    except Exception as e:
        # Erreur inattendue — on ne bloque pas l'analyse mais on loggue
        logger.error(f"[QUALITY GATE] Erreur inattendue sur {filename}: {e}")
        return QualityGateResult(
            can_analyze=True,
            status="warning",
            score_data=60,
            document_format="unknown",
            anomalies=[f"Erreur lors de la validation des données : {str(e)[:120]}"],
            assumptions=["L'analyse continue malgré une erreur de validation des données."],
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
