# A22 — source clarification in the synthetic portfolio

Status: LOCAL_TESTED / NOT_CHECKPOINTED / NOT_LIVE_PROVEN, 2026-09-18.
Superseded for the one-client navigation path by the bounded live observation
recorded below on 2026-09-19. Implementation remains NOT_CHECKPOINTED.
Base durable HEAD: `4eede4adc1de11f5e6ea669be8dcec07cc3144c6`.
Previous local V35 closeout/refresh changes preserved; generated Next.js delta excluded.

## Why / before / change / after

The CFO must find unresolved source evidence without first opening every client's
analysis. BEFORE: V35 dossiers survive restart but are visible only on the selected
client's empty chat screen. Portfolio reads decisions/arcs only and its empty message
can be mistaken for absence of unresolved source problems.

CHANGE: independent read-only synthetic source clarification section, alongside but
not merged into decision cards. No new decision, arc, fact, interpretation or memory
record. No financial urgency score, causal inference or automatic resolution.

AFTER: under both existing synthetic frontend flags, portfolio separately displays
non-UNDERSTOOD dossiers by owned client with filename, status, exact dossier ID,
source SHA256 and conflict metric labels. Client navigation uses explicit entity.
Decision-empty wording is limited to the decision register when this view is enabled.
Source-empty wording does not claim financial reliability. Outside these flags the
existing portfolio presentation is unchanged. This does not implement general Beta
source intake: the underlying registry still accepts only four synthetic workbooks.

## Boundary / evidence

- GET `/api/v1/synthetic-source-attention` reuses development/synthetic flag,
  authenticated designated-organization gate. No caller-selected company.
- At most 100 stored dossiers are read; overflow refuses, never silently truncates.
  All rows verified before filtering, including rows that claim UNDERSTOOD.
  Exact company/entity/engagement ownership, registered source, payload checksum,
  schema and UUID verified via existing V35 routines. Duplicate/foreign/corrupt
  rows or missing ownership refuse the entire projection; errors return safe 503.
- No source table writes. Alphabetic client order, not economic priority. Dossiers
  remain historical unresolved-source observations: no inferred cross-period relevance
  or automatic removal by a newer dossier; explicit resolution lifecycle remains open.
- Frontend validates scoped dossiers, duplicate IDs, one-company response and bounds.
  Unavailability is not empty. Reload removes old cards; unmounted responses ignored.
- Local mock service/HTTP tests cover provenance, two-client separation, foreign row
  injection, malformed integrity, duplicates, bound overflow, ownership failure,
  outage and production refusal. Component/API tests cover provenance/navigation,
  unavailable/empty/retry, malformed groups and foreign scope.

Validation: 398 backend PASS / 2 SKIP in test_v1*, test_governed*, test_financial*,
test_source*; skips require absent real Phidani.xlsx (not introduced). Full frontend
115 PASS / 16 suites; TypeScript no-emit PASS. Tests use synthetic mocks only, no
live database/provider/real data. FR-EXPECTED-2 remains immutable.

## Open / next

This is not proof of deployed browser behavior, live two-user RLS/IDOR, professional
output quality, full FR07/FR08 or financial prioritization. No provider/RD gate change.
Next live check can be read-only against the existing V35 dossier after restarting
the backend: portfolio shows its source clarification card even though the executed
decision correctly produces no active decision item. No new capture is needed.
Separate client adversarial live proof and reported/derived governed definition
authority remain necessary; do not claim that this read model closes those debts.

External Provider CLOSED; Real-data Admission CLOSED; Self-Selling DEFERRED.

## Read-only browser observation — 2026-09-18

Agent opened the local `/app/portfolio` with the browser tool. Session resolved;
decision register correctly displayed no active item. Separate source section
displayed "Sources indisponibles — absence de points à clarifier non établie."
No upload, analysis, capture, login or other write action was performed by agent.
Read-only current backend OpenAPI inspection confirmed source-dossier routes present
but `/api/v1/synthetic-source-attention` absent. This running process has not loaded
A22. Honest unavailable-state rendering is observed; successful A22 retrieval and
portfolio-to-source navigation remain UNPROVEN. Required next operation is a local
backend restart in its existing secret-bearing Founder terminal, not a migration
or new dossier capture. Do not infer successful integration from component tests.

## Bounded live navigation — recorded 2026-09-19

Following Founder-confirmed backend restart/preflight, agent used the in-app browser
in read-only mode with the existing authenticated session. Observed rendered UI:

1. `/app/portfolio`: no active point in the decision register; separate source
   clarification section contains Optilux Synthetic Internal Pilot, CONTRADICTION,
   dossier `c35d9b59-f8b8-5ede-8863-d2a32b1f106c`, REVENUE and source hash
   `176F8F1A9E6A20B61E61C773AD54000D1D91E769B84C99BD2DA7B8ACB038D7E5`.
   No canonical fact, financial urgency or resolution inferred by the view.
2. Click on the client source link navigates to
   `/app/chat?entity=dfd01f5c-a095-4fcb-8873-ccc3f427d348`; exact client and
   existing conflict dossier visible, save disabled with no file selected.
3. Click on existing dossier restores same ID/hash, REVENUE 1000000 and 990000 EUR
   (2025), their distinct F/S/R references, discrepancy 10000 explicitly not a
   resolution, independent unvalidated EBITDA 80000 and CASH 115000 observations,
   required investigation and no-provider/non-governed-analysis notice.
4. Click on read-only list refresh immediately removes selected detail, displays
   loading, then restores the list without stale detail. This exercises the local
   stale-detail correction's success path in the browser; outage remains mock-tested.

Evidence is agent-observed accessibility-tree/rendered UI through normal navigation,
not a captured HTTP-status/network audit or independent DB before/after comparison.
Agent clicked only read/navigation controls; no file selection, capture, analysis,
login, mutation action or provider call was intentionally initiated. Do not turn this
into a complete network-egress/no-write audit. Existing V35 Founder restart/detail
GET proof remains separately attributed in source-dossier-evidence-A20-A21.md.

Verdict: BOUNDED_LIVE_NAVIGATION_PASS for one synthetic client/dossier. Multi-client
and multi-user adversarial live isolation, production/RLS effectiveness, financial
ranking, source resolution and professional reliability remain OPEN. No gate opened.
