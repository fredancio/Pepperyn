# PEPPERYN_PRODUCT_QUALITY_CONTRACT.md
Version : 1.0  
Status : FROZEN  
Authority : CTO Contract

## Purpose

Pepperyn is an Executive Decision System.  
Every deliverable produced by Pepperyn must be immediately usable by a CEO, CFO or Board of Directors without any manual correction.  
This contract has authority over every renderer.  
No feature, refactoring, optimisation or architectural improvement may violate this contract.

---

## RULE 001 — Zero Manual Intervention

Every generated deliverable must be immediately usable.  
The user must never need to:

* resize a column;
* resize a row;
* wrap text manually;
* repair a formula;
* correct an alignment;
* complete missing values;
* modify formatting.

If any manual intervention is required after generation, the renderer is NON-COMPLIANT.

---

## RULE 002 — Zero Truncated Content

No information may be visually truncated.  
If the content is longer than the available space, the renderer must automatically adapt:

* column width;
* row height;
* font size (within acceptable limits);
* wrap text;
* page layout.

Truncation is forbidden.

---

## RULE 003 — Renderer Responsibility

A renderer is responsible for presentation.  
It is never allowed to delegate presentation problems to the user.  
Every renderer must automatically guarantee:

* AutoFit
* Wrap Text
* Vertical Alignment
* Horizontal Alignment
* Readable spacing
* Printable layout

---

## RULE 004 — Single Source of Truth

Every renderer consumes exactly the same ExecutiveCase.  
A renderer may NEVER:

* recalculate a value;
* reinterpret a priority;
* invent a classification;
* generate an alternative narrative;
* derive information that is not explicitly present in the ExecutiveCase.

Renderers DISPLAY.  
They never THINK.

---

## RULE 005 — Narrative Consistency

The three deliverables must always tell exactly the same executive story.  
They must expose:

* the same findings;
* the same priorities;
* the same decisions;
* the same roadmap;
* the same risks;
* the same confidence.

Only the presentation changes.  
The meaning never changes.

---

## RULE 006 — Executive Readability

Every page, slide and worksheet must answer one executive question.  
The reader must never wonder:  
*"What am I supposed to understand here?"*  
If the message is not immediately obvious, the renderer is non-compliant.

---

## RULE 007 — Zero Ambiguity

No renderer may display wording that contradicts the available data.  
Examples:

* "Données insuffisantes" while a value exists.
* "Impact faible" while ROI is high.
* "Unknown" while the information is available.

Semantic contradictions are considered critical defects.

---

## RULE 008 — Delivery Refusal

A version must not be released if any of the following remains true:

* truncated text;
* unresolved formulas;
* inconsistent figures;
* contradictory priorities;
* unreadable layout;
* manual corrections required;
* ExecutiveCase inconsistently rendered.

One violation is sufficient to refuse delivery.

---

## RULE 009 — Commercial Readiness

Every release must satisfy one question:  
*"Could a CEO present these three deliverables tomorrow morning to his Board of Directors without modifying anything?"*  
If the answer is NO, the release is rejected.

---

## RULE 010 — Feature Freeze

During Executive Polish:  
No new functionality.  
No architectural evolution.  
No optimisation unrelated to Product Quality.  
Only quality improvements are authorised.  
This contract remains in force until Commercial Freeze is officially lifted.
