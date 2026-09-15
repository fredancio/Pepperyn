# Pepperyn Master Canon

**Status:** transfer-preparation canon, not authorization to complete V1

**Baseline:** `6fb05c11394ce33423e81697a3dd13e9513e7794`

**Prepared for:** Astra autonomous V1 completion

**Product gates:** External Provider **CLOSED**; Real-data Admission **CLOSED**; Self-Selling Control Center **PARKED / DEFERRED**

This directory is the navigation and control layer for the Pepperyn corpus. It
does not replace the historical sources. It links claims to sources, code,
migrations, tests and live evidence so that later agents do not have to trust a
recursive summary.

## Authority hierarchy

When sources conflict, apply this order and record the discrepancy rather than
silently merging it:

1. current explicit Founder decisions;
2. Pepperyn Constitution, Profession Model and explicit invariants;
3. repository, migrations and executable tests for implementation reality;
4. live rehearsal evidence tied to an exact environment and revision;
5. current Work control documentation;
6. historical documentation and superseded ADRs;
7. hypotheses and exploratory material.

The repository proves what exists. It does not by itself prove that a missing
historical capability was abandoned. Historical documentation explains intent
but does not prove implementation.

## Canon map

| File | Purpose |
|---|---|
| `00_NORTH_STAR_AND_DOCTRINE.md` | Founder-controlled product identity and doctrine |
| `01_HISTORICAL_EVOLUTION.md` | Cowork through recovery, Work and Astra transition |
| `01_SOURCE_INVENTORY_AND_AUTHORITY.md` | Source corpus, provenance and unresolved source gaps |
| `02_INTELLIGENCE_ARCHITECTURE.md` | Cognitive concepts and maturity |
| `03_ARCHITECTURE_MODEL.md` | Product/domain/trust/infrastructure architecture |
| `04_PRODUCT_MODEL.md` | User, surfaces and product success test |
| `05_BUSINESS_MODEL.md` | Current business hypothesis and non-decisions |
| `06_FRACTIONAL_CFO_OS.md` | Golden professional operating loop |
| `07_PRIVACY_AND_SECURITY_MODEL.md` | Deterministic privacy and provider boundary |
| `08_DECISION_REGISTER.md` | Current Founder/product/security decisions |
| `09_FEATURE_AND_CAPABILITY_REGISTER.md` | Comprehensive current-repository capability inventory |
| `10_CURRENT_IMPLEMENTATION_REALITY.md` | Evidence-calibrated baseline at transfer preparation |
| `11_NON_REGRESSION_INVARIANTS.md` | Formal No Silent Regression contract |
| `12_V1_DEFINITION_OF_DONE.md` | Private Beta gates and evidence standard |
| `13_PRIVATE_BETA_PLAN.md` | Two-user beta scope and evaluation |
| `14_PRODUCTION_AND_INFRASTRUCTURE.md` | Current/target environments and unknowns |
| `15_DEFERRED_WORK_REGISTER.md` | Navigation to preserved deferred capabilities |
| `16_OPEN_QUESTIONS_AND_UNRESOLVED_CONTRADICTIONS.md` | Quarantined unknowns and blockers |
| `17_EVIDENCE_AND_TRACEABILITY_MATRIX.csv` | Machine-readable capability/evidence navigation |
| `18_ASTRA_AUTONOMOUS_COMPLETION_CONTRACT.md` | Astra authority, stops and operating rules |
| `19_FINFLATE_DEBRANDING_GATE.md` | Active removal surface and release proof |
| `20_FINANCIAL_RELIABILITY_GATE.md` | Professional reliability evidence standard |
| `21_PRODUCTION_SECURITY_GATE.md` | Production-specific security evidence standard |
| `22_TRANSFER_VALIDATION.md` | Context-independent handover validation |
| `23_FOUNDER_HANDOVER_AUTHORITY_RECORD.md` | Repository-resident Founder authority for transfer |

Open product and release gates are not hidden by this package. Their preparation
status and missing evidence are recorded in `10_CURRENT_IMPLEMENTATION_REALITY.md`,
`12_V1_DEFINITION_OF_DONE.md` and `16_OPEN_QUESTIONS_AND_UNRESOLVED_CONTRADICTIONS.md`.
