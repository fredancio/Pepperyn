from services.file_parser import _extract_bfr_summary, _extract_bilan_summary


def _sheet(rows, columns=None):
    return {
        "sheet_name": "Synthétique",
        "columns": columns or ["Poste", "2023", "2024", "2025"],
        "full_table": rows,
    }


def test_prompt_prioritized_summaries_use_current_actual_with_provenance():
    sheets = [_sheet([
        {"Poste": "Trésorerie", "2023": 410000, "2024": 372000, "2025": 336000},
        {"Poste": "DSO jours", "2023": 48, "2024": 61, "2025": 74},
        {"Poste": "BFR total", "2023": 312000, "2024": 434000, "2025": 579000},
        {"Poste": "Total actif", "2023": 2040000, "2024": 2107000, "2025": 2206000},
        {"Poste": "Capitaux propres", "2023": 1000000, "2024": 910000, "2025": 791000},
    ])]

    bfr = _extract_bfr_summary(sheets)
    bilan = _extract_bilan_summary(sheets)

    assert bfr["tresorerie_eur"] == {
        "label": "Trésorerie", "value": 336000, "period": "2025", "sheet": "Synthétique",
    }
    assert bfr["dso_jours"]["value"] == 74
    assert bfr["bfr_eur"]["value"] == 579000
    assert bilan["total_actif"]["value"] == 2206000
    assert bilan["capitaux_propres"]["value"] == 791000
    assert {item["period"] for item in (*bfr.values(), *bilan.values())} == {"2025"}


def test_unresolved_or_ambiguous_current_period_is_omitted():
    unresolved = [_sheet(
        [{"Poste": "Trésorerie", "Col A": 410000, "Col B": 336000}],
        ["Poste", "Col A", "Col B"],
    )]
    ambiguous = [_sheet(
        [{"Poste": "Trésorerie", "Jan 2025": 100000, "Fév 2025": 90000}],
        ["Poste", "Jan 2025", "Fév 2025"],
    )]

    assert _extract_bfr_summary(unresolved) == {}
    assert _extract_bilan_summary(unresolved) == {}
    assert _extract_bfr_summary(ambiguous) == {}
    assert _extract_bilan_summary(ambiguous) == {}


def test_zero_is_a_valid_current_actual_value():
    sheets = [_sheet([
        {"Poste": "Trésorerie", "2023": 100, "2024": 50, "2025": 0},
    ])]

    assert _extract_bfr_summary(sheets)["tresorerie_eur"]["value"] == 0
