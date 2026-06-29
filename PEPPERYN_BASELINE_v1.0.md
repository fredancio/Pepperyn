# PEPPERYN_BASELINE_v1.0.md

Version : 1.0
Status : FROZEN
Date : 2026-06-29
Authority : CTO

---

## Purpose

This document is the official entry point of Pepperyn governance.

It does not contain business logic.
It does not contain technical specifications.
It does not contain implementation rules.

It references exclusively the documents that constitute the official governance of Pepperyn.

From this baseline:

- Every future evolution must be compatible with these documents.
- No modification of a FROZEN document may be made without an explicit GO CTO.
- Every new specification must reference this baseline.

---

## Governance Documents — Official Registry

The following five documents constitute the official governance of Pepperyn
as adopted on 2026-06-29 by the CTO.

---

### DOC-01 — The Vision Behind Pepperyn

| Field | Value |
|---|---|
| Filename | `The Vision Behind Pepperyn.pdf` |
| Version | 1.0 |
| Status | **FROZEN** |
| Date | 2026-06-29 |
| Authority | CTO |
| Role in hierarchy | Foundational — defines *why* Pepperyn exists |

**Purpose:** Establishes the philosophical foundation. Pepperyn is an Executive Decision Intelligence System. Its role is to participate in executive thinking before executive decisions are made.

**Key principles locked by this document:**
- Pepperyn strengthens executive judgement; it does not replace it.
- Success is measured by the quality of decisions made, not by reports generated.
- The question every executive team must naturally ask: *"What does Pepperyn think?"*

**Metadata note:** The original document carries no version, status, date or authority fields.
These are formally assigned by this baseline. The CTO adopts this document as Version 1.0 FROZEN
as of 2026-06-29.

---

### DOC-02 — PEPPERYN_EXECUTIVE_COGNITION_MODEL.md

| Field | Value |
|---|---|
| Filename | `PEPPERYN_EXECUTIVE_COGNITION_MODEL.md` |
| Version | 1.0 |
| Status | **FROZEN** |
| Date | 2026-06-29 |
| Authority | CTO |
| Role in hierarchy | Architectural — defines *how* Pepperyn thinks |

**Purpose:** Defines the Five Cognitive Layers that transform raw business data into structured executive reasoning: Knowledge → Judgement → Reasoning → Story → Memory. The Render Engine is intentionally excluded from the cognition model.

**Key principles locked by this document:**
- Executive intelligence does not emerge from data. It emerges from a sequence of cognitive transformations.
- Pepperyn never jumps from numbers to recommendations. It progressively transforms information into judgement.
- The Render Engine is a presentation layer, not a cognitive layer.

**Metadata note:** Original document carries Status "Foundational Architecture" and Authority
"PEPPERYN_PRODUCT_CONSTITUTION.md". Both are overridden by this baseline.
Status is formally set to FROZEN. Authority is formally set to CTO.
PEPPERYN_PRODUCT_CONSTITUTION.md is acknowledged as a parent document not yet
integrated into the governance package. Its integration requires a separate GO CTO.

---

### DOC-03 — PEPPERYN_EXECUTIVE_RENDERING_SPECIFICATION.md

| Field | Value |
|---|---|
| Filename | `PEPPERYN_EXECUTIVE_RENDERING_SPECIFICATION.md` |
| Version | 1.0 |
| Status | **FROZEN** |
| Date | 2026-06-29 |
| Authority | CTO |
| Role in hierarchy | Technical — defines *how* Pepperyn presents |

**Purpose:** Defines the frozen structure, page order, typography, layout rules and content
constraints for all three renderers: PDF (Executive Report), PPTX (Board Deck), Excel (Financial Model).

**Key principles locked by this document:**
- The renderer never decides. The renderer only renders.
- Slide order FROZEN (16 slides). Page order FROZEN (11 pages). Sheet structure FROZEN (8 sheets).
- Typography: Inter (primary), Calibri (fallback). Minimum font size: 16pt.
- Any presentation problem is a renderer problem — never a data or user problem.

**Metadata note:** Original document carries Version 1.0, Status FROZEN, Authority CTO.
Date is formally assigned as 2026-06-29 by this baseline.

---

### DOC-04 — PEPPERYN_PRODUCT_QUALITY_CONTRACT.md

| Field | Value |
|---|---|
| Filename | `PEPPERYN_PRODUCT_QUALITY_CONTRACT.md` |
| Version | 2.0 |
| Status | **FROZEN** |
| Date | 2026-06-29 |
| Authority | CTO |
| Role in hierarchy | Contractual — defines *what* Pepperyn must never violate |

**Purpose:** Defines the 12 non-negotiable quality rules and the FINAL GOVERNANCE RULE.
This contract has authority over every renderer. No feature, refactoring or optimisation
may violate this contract.

**12 RULES:**
- RULE 001 — Zero Manual Intervention
- RULE 002 — Zero Truncated Content
- RULE 003 — Renderer Responsibility
- RULE 004 — Single Source Of Truth
- RULE 005 — Narrative Consistency
- RULE 006 — Executive Readability
- RULE 007 — Zero Ambiguity
- RULE 008 — Cause → Decision → Impact
- RULE 009 — Visual Confidence
- RULE 010 — CEO Review
- RULE 011 — Delivery Refusal
- RULE 012 — Product Before Code

**RULE lifecycle:** Implementation → Tests → Visual Inspection → CEO Review → Freeze.
Only the CEO Review can freeze a RULE.

**RULES frozen as of this baseline:**
- RULE 001 — FROZEN (CEO validation received)
- RULE 002 — FROZEN (CEO validation received)
- RULE 003 through RULE 012 — pending closure

**Metadata note:** Original document was Version 1.0 (10 RULES). This baseline adopts Version 2.0
(12 RULES + Product Philosophy + Golden Rule + Final Governance Rule) as the official version.
The repo file `PEPPERYN_PRODUCT_QUALITY_CONTRACT.md` has been updated to Version 2.0 as of
this baseline.

---

### DOC-05 — PEPPERYN_EVOLUTION_ROADMAP.md

| Field | Value |
|---|---|
| Filename | `PEPPERYN_EVOLUTION_ROADMAP.md` |
| Version | 1.0 |
| Status | **FROZEN** |
| Date | 2026-06-29 |
| Authority | CTO |
| Role in hierarchy | Strategic — defines *where* Pepperyn is going |

**Purpose:** Defines the product capability roadmap across four horizons:
H1 (Understand the Business — complete), H1.5 (Decide with Confidence — in progress),
H2 (Remember and Learn), H3 (Anticipate), H4 (Advise in Real Time).

**Key principles locked by this document:**
- Pepperyn does not evolve by accumulating features. It evolves by acquiring executive capabilities.
- Every new capability must satisfy three conditions: improve executive judgement, increase executive trust, strengthen Pepperyn's differentiation.
- Technology serves capabilities. Capabilities serve executive decisions.
- Current priority: complete H1.5 — commercial MVP — before any H2 work begins.

**Metadata note:** Original document carries Status "Living Product Roadmap" and Authority
"PEPPERYN_PRODUCT_CONSTITUTION.md". Both are overridden by this baseline.
Status is formally set to FROZEN as of 2026-06-29. Authority is formally set to CTO.
"Living" nature means the document may be updated by GO CTO, not that it is mutable by default.
PEPPERYN_PRODUCT_CONSTITUTION.md acknowledged (see DOC-02 note above).

---

## Metadata Audit Summary

| Document | Version | Status (original) | Status (baseline) | Date | Authority (original) | Authority (baseline) |
|---|---|---|---|---|---|---|
| The Vision Behind Pepperyn | — → 1.0 | absent → FROZEN | ✅ | absent → 2026-06-29 | absent → CTO | ✅ |
| PEPPERYN_EXECUTIVE_COGNITION_MODEL | 1.0 ✅ | Foundational Architecture → FROZEN | ✅ | absent → 2026-06-29 | PRODUCT_CONSTITUTION.md → CTO | ✅ |
| PEPPERYN_EXECUTIVE_RENDERING_SPECIFICATION | 1.0 ✅ | FROZEN ✅ | ✅ | absent → 2026-06-29 | CTO ✅ | ✅ |
| PEPPERYN_PRODUCT_QUALITY_CONTRACT | 1.0 → 2.0 | FROZEN ✅ | ✅ | absent → 2026-06-29 | CTO ✅ | ✅ |
| PEPPERYN_EVOLUTION_ROADMAP | 1.0 ✅ | Living Product Roadmap → FROZEN | ✅ | absent → 2026-06-29 | PRODUCT_CONSTITUTION.md → CTO | ✅ |

All five documents are now formally governed by this baseline.
All metadata gaps have been resolved by this registry.

---

## Pending Governance Item

**PEPPERYN_PRODUCT_CONSTITUTION.md**

Referenced as the parent authority by PEPPERYN_EXECUTIVE_COGNITION_MODEL.md and
PEPPERYN_EVOLUTION_ROADMAP.md. This document was not included in the governance package.

Status: not yet integrated.

Action required: GO CTO to integrate PEPPERYN_PRODUCT_CONSTITUTION.md into the governance package
and register it as DOC-00 in the next baseline revision.

---

## Rules of Evolution

From this baseline, the following rules govern any change to governance documents.

**Rule E-01 — Immutability of FROZEN documents**
No FROZEN document may be modified without an explicit GO CTO.
A GO CTO must specify: the document, the section, the nature of the change, and the motivation.

**Rule E-02 — Compatibility requirement**
Every new technical specification, architectural decision or product feature must reference this
baseline and demonstrate compatibility with the five governance documents.

**Rule E-03 — Baseline versioning**
Any addition, removal or modification of a governance document produces a new baseline version.
PEPPERYN_BASELINE_v1.0.md is superseded by PEPPERYN_BASELINE_v1.1.md (minor) or
PEPPERYN_BASELINE_v2.0.md (major structural change).

**Rule E-04 — RULE closure sequence**
RULES are closed sequentially according to the RULE 010 lifecycle.
No RULE may be marked FROZEN without CEO Review.
The current sprint closes remaining RULES in the PEPPERYN_PRODUCT_QUALITY_CONTRACT.md
before any H2 capability work begins.

**Rule E-05 — MVP Commercial First**
No new feature.
No architecture refactoring.
Only RULE closure work until the commercial MVP is validated by first clients.
This constraint is lifted only by explicit GO CTO.

---

## Current RULE Status Register

| RULE | Title | Status |
|---|---|---|
| RULE 001 | Zero Manual Intervention | **FROZEN** |
| RULE 002 | Zero Truncated Content | **FROZEN** |
| RULE 003 | Renderer Responsibility | pending |
| RULE 004 | Single Source Of Truth | pending |
| RULE 005 | Narrative Consistency | pending |
| RULE 006 | Executive Readability | pending |
| RULE 007 | Zero Ambiguity | pending |
| RULE 008 | Cause → Decision → Impact | pending |
| RULE 009 | Visual Confidence | pending |
| RULE 010 | CEO Review | pending |
| RULE 011 | Delivery Refusal | pending |
| RULE 012 | Product Before Code | pending |

---

*This document is the single source of governance authority for Pepperyn.*
*It supersedes any prior informal reference to governance documents.*
*It is itself FROZEN and may only be revised by GO CTO.*
