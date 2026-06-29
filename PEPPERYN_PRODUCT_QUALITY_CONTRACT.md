# PEPPERYN_PRODUCT_QUALITY_CONTRACT.md

Version : 2.0
Status : FROZEN
Date : 2026-06-29
Authority : CTO

---

## Product Philosophy

Pepperyn is **not** a reporting software.

Pepperyn is an **Executive Decision Engine**.

Every deliverable must help a CEO or a Board of Directors make better decisions.

The objective is never to generate documents.

The objective is to generate confidence.

If confidence is lost, the product fails.

---

## GOLDEN RULE

A renderer exists for one purpose only:

> Display the Executive Decision Model.

It never:

- thinks
- recalculates
- interprets
- simplifies
- truncates
- invents

It only displays.

---

## RULE 001 — Zero Manual Intervention

No user must ever modify a generated deliverable.

Never.

The generated PDF, PPTX and Excel must be immediately usable.

If the user needs to:

- resize a column
- resize a row
- wrap text
- move an object
- replace a value
- repair a formula
- correct a layout

then the renderer has failed.

---

## RULE 002 — Zero Truncated Content

No information may disappear because of presentation.

Never.

The renderer adapts itself.
The content never adapts itself to the renderer.

Forbidden:

- `[:80]`
- `[:120]`
- `[...]`
- visual clipping
- hidden rows
- hidden text
- cropped shapes

Allowed:

- automatic row height
- automatic font scaling
- page breaks
- wrapping
- additional pages

Information always wins.

---

## RULE 003 — Renderer Responsibility

Presentation problems are renderer problems.

Never user problems.
Never data problems.
Never LLM problems.

---

## RULE 004 — Single Source Of Truth

ExecutiveCase is the only truth.

Every renderer must display exactly the same:

- values
- priorities
- impacts
- decisions
- risks
- roadmap
- scenarios

If two renderers disagree,
the renderer is wrong.
Never the ExecutiveCase.

---

## RULE 005 — Narrative Consistency

The PDF,
the PPT,
and the Excel
must tell exactly the same executive story.

Changing the medium must never change the message.

---

## RULE 006 — Executive Readability

A CEO must understand the situation in less than five minutes.

Every page answers one executive question.

Nothing else.

---

## RULE 007 — Zero Ambiguity

Pepperyn never sends contradictory messages.

Forbidden examples:

- "Données insuffisantes" when the value exists.
- "Impact faible" when ROI is high.
- "Priority High" and "Do later" for the same decision.

One truth.
One interpretation.

---

## RULE 008 — Cause → Decision → Impact

Every executive decision must explicitly answer three questions.

1. What problem does it solve?
2. Why is it the priority?
3. What measurable impact is expected?

If this causal chain is missing, Pepperyn is no longer an Executive Decision Engine.

---

## RULE 009 — Visual Confidence

A CEO must be proud to project every page.

No page may create embarrassment.
No page may require explanation.
No page may require an apology.

---

## RULE 010 — CEO Review

Passing automated tests is never sufficient.

Every RULE follows the same lifecycle.

```
Implementation
↓
Tests
↓
Visual Inspection
↓
CEO Review
↓
Freeze
```

Only the CEO Review can freeze a RULE.

---

## RULE 011 — Delivery Refusal

Pepperyn refuses its own release whenever one of the following exists:

- manual correction required
- contradictory information
- missing values
- visual truncation
- broken formulas
- corrupted text
- placeholder remaining
- renderer disagreement
- impossible interpretation

One single violation blocks the release.

---

## RULE 012 — Product Before Code

The product is judged only through its deliverables.

Not through:

- commits
- tests
- architecture
- documentation
- code quality

Only one question matters:

> "Would a CEO confidently present these three documents tomorrow morning to his Board of Directors?"

If the answer is not an unequivocal **YES**,
the release is refused.

---

## FINAL GOVERNANCE RULE

The renderer never decides.
The developer never decides.
The tests never decide.

Only the CEO validates the product.

Until the CEO explicitly declares
**RULE X — FROZEN**
the work is considered unfinished.

---

*End of Contract.*
