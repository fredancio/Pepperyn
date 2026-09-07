# Pepperyn V1 heterogeneous synthetic workbook provenance

All four workbooks were created on 2026-09-07 specifically for local V1
falsification. They contain synthetic literal values only. They contain no
formula, macro, external link, credential, personal identity or client datum.

| Fixture | SHA-256 | Intended falsification |
|---|---|---|
| `pepperyn_v1_heterogeneous_english.xlsx` | `FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93` | English management labels, reordered sheets and 2024/2025 periods must produce grounded 2025 facts. |
| `pepperyn_v1_heterogeneous_ambiguous_period.xlsx` | `8F35CF676B58BFF823CD423BDA70145A9951A55B9F689FF591282F3EAF9C6E51` | `Current` and `Latest` must not be silently assigned a governed current period. |
| `pepperyn_v1_heterogeneous_ambiguous_number.xlsx` | `E89851FF9AAF2FADA84F012CE7BDE846F859C7A62B1531F7C4F7F96A055F9E29` | Locale-dependent numeric strings must not become exact financial facts. |
| `pepperyn_v1_heterogeneous_conflict.xlsx` | `176F8F1A9E6A20B61E61C773AD54000D1D91E769B84C99BD2DA7B8ACB038D7E5` | Conflicting current-period revenue values must not be reconciled silently. |

The files are deliberately small professional-style extracts, not copies of
the Optilux M1C layout. Each file is passed as real XLSX bytes through the
Quality Gate, `FileConnector`, file parser, normalization, anonymization and
governed financial-understanding builder. Provider request construction is
permitted only for the understood case and remains no-network in this suite.

