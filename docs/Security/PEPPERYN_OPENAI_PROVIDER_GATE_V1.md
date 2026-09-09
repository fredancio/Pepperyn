# PEPPERYN --- OPENAI PROVIDER GATE V1

**Document type:** Security / Provider Governance / Work Handover\
**Status:** Conditional Pass --- Real-client admission remains CLOSED\
**Prepared for:** ChatGPT Work / Pepperyn Supervisor / Architecture /
Security\
**Date:** 2026-08-30

------------------------------------------------------------------------

## 1. Executive Decision

> **OPENAI PROVIDER GATE: CONDITIONAL PASS**

The OpenAI API is an **approved provider candidate for Pepperyn V1**,
subject to the technical, contractual, regional, account-level and
code-enforcement conditions defined below.

This decision does **not** authorize real-client external inference.

> **REAL-DATA ADMISSION = CLOSED**

Real-client data may not be transmitted to OpenAI until Provider Gates
PG-1 through PG-8 have been evidenced against the effective Pepperyn
production project/account and the Pepperyn LLM Egress Trust Gate has
passed its remaining gates.

### Target architecture

-   European OpenAI API processing where supported and appropriate.
-   Target: Zero Data Retention (ZDR), subject to eligibility/approval
    and endpoint compatibility.
-   No voluntary training/data-sharing opt-in.
-   Approved stateless or minimally stateful inference surfaces.
-   Pepperyn-owned enterprise/decision memory.
-   Exact financial values only where professionally necessary.
-   Pseudonymized identities.
-   Task-specific minimum disclosure.
-   All inference routed through `LlmEgressAuthority`.

``` text
CLIENT / PROFESSIONAL USER
          |
          v
       PEPPERYN
          |
          +-- authentication / authorization
          +-- tenant / Entity / Engagement isolation
          +-- task-specific context selection
          +-- minimization
          +-- pseudonymization
          +-- provenance / correspondence
          |
          v
   LlmEgressAuthority
          |
          +-- provider-policy enforcement
          +-- final payload validation
          +-- frozen transport payload
          +-- approved endpoint/model/region only
          |
          v
      OPENAI API
```

------------------------------------------------------------------------

## 2. Governing Security Principle

Pepperyn's objective is **not** to prevent every financial datum from
ever leaving Pepperyn.

The intended rule is:

> **SEND ONLY WHAT THE AUTHORIZED PROFESSIONAL TASK REQUIRES, THROUGH
> ONE GOVERNED AND TESTABLE EXTERNAL BOUNDARY, WITHOUT UNNECESSARY
> IDENTITY OR CROSS-CLIENT CONTEXT.**

The provider question is therefore:

> Under what precise technical and contractual conditions may Pepperyn
> transmit pseudonymized financial information necessary for
> professional reasoning to the OpenAI API?

This Provider Gate does not replace Pepperyn's internal authorization,
isolation, pseudonymization, correspondence, minimization, testing or
GDPR obligations.

------------------------------------------------------------------------

## 3. Relationship to the LLM Egress Trust Gate

Provider assurance is a parallel dependency of the broader security
program:

``` text
Slice 1 — Governed LLM egress authority
    |
Slice 2 — Ownership / Entity / Engagement isolation
    |
Slice 3 — Durable correspondence / provenance
    |
Slice 4 — Task minimization / unsafe surfaces
    |
    +-----------------------------+
    |                             |
Final Pepperyn Security Gate   OpenAI Provider Gate
    |                             |
    +--------------+--------------+
                   |
            REAL-DATA ADMISSION
                   |
       Founder First-Engagement
```

Work must not reopen already-resolved internal architecture merely
because this provider gate exists.

------------------------------------------------------------------------

## 4. Training / Model Improvement

Current OpenAI API documentation states that API data is **not used to
train or improve OpenAI models by default**, unless the customer
explicitly opts in to data sharing.

### Pepperyn rule

> Production API data sharing for model training/improvement must remain
> disabled.

Before real-data admission, the effective Pepperyn organization/project
configuration must be verified rather than relying only on the provider
default.

**Gate:** PG-1.

------------------------------------------------------------------------

## 5. Retention Is Not Training

A critical distinction:

> **NOT USED FOR TRAINING ≠ NOT RETAINED**

OpenAI documents abuse-monitoring retention under standard API
conditions, commonly up to 30 days depending on endpoint/configuration.
Some API surfaces may also maintain application state independently.

Pepperyn must therefore verify training policy and retention policy
separately.

------------------------------------------------------------------------

## 6. Zero Data Retention

OpenAI offers controls including **Zero Data Retention (ZDR)** and
**Modified Abuse Monitoring (MAM)** for eligible/approved API customers.

### Pepperyn decision

> **TARGET PROVIDER CONFIGURATION = ZDR**

ZDR must never be assumed until the effective Pepperyn API project has
been approved/configured and the selected endpoints/features are
confirmed compatible.

Synthetic implementation may proceed before this.

Real-client external inference may not.

**Gate:** PG-3.

------------------------------------------------------------------------

## 7. European Regional Processing

OpenAI currently documents European data-residency/regional-processing
options for supported API services/models.

### Pepperyn target

> **EUROPEAN REGIONAL PROCESSING for V1 where supported and
> appropriate.**

Before admission, verify:

-   effective project region;
-   selected endpoint;
-   selected model/model family;
-   regional-processing compatibility;
-   any ZDR/regional prerequisites.

**Gate:** PG-4.

------------------------------------------------------------------------

## 8. DPA / GDPR Provider Layer

OpenAI publishes a Data Processing Addendum. For applicable EEA/Swiss
customer relationships, the current framework identifies OpenAI Ireland
Ltd. and addresses international-transfer mechanisms.

### Consequence

Availability of the DPA supports provider suitability, but does **not**
make Pepperyn globally GDPR-compliant.

Pepperyn remains responsible for its own legal bases, transparency,
contracts, minimization, retention, rights handling, security and other
applicable obligations.

**Gate:** PG-2.

------------------------------------------------------------------------

## 9. Subprocessors

OpenAI maintains an official subprocessor list. Current official
material reviewed for this gate includes infrastructure/service
providers such as Microsoft, Cloudflare and CoreWeave.

### Consequences

Pepperyn must not promise:

> "Your data is processed only by OpenAI."

Before real-data admission:

-   current subprocessor information must be recorded;
-   material regional implications reviewed;
-   future customer-facing privacy wording must match the actual chain;
-   responsibility for future material provider changes should be
    assigned.

**Gate:** PG-6.

------------------------------------------------------------------------

## 10. Provider Security Assurance

OpenAI currently publishes security/compliance information including
references to controls/certifications such as SOC 2 Type 2, ISO/IEC
27001 and ISO/IEC 27701 for applicable systems/services.

This is supporting evidence only. It does not replace Pepperyn
authorization, pseudonymization, isolation, minimization or
outbound-boundary testing.

------------------------------------------------------------------------

## 11. Pepperyn Owns Its Memory

Preferred architecture:

``` text
Pepperyn governed memory
        |
task-specific context selection
        |
LlmEgressAuthority
        |
temporary OpenAI inference
        |
Pepperyn-controlled result / memory
```

Avoid making provider-side persistent conversation state the
authoritative enterprise memory.

### Architectural principle

> **Enterprise memory belongs to Pepperyn. The external model is a
> governed reasoning engine, not Pepperyn's authoritative memory
> store.**

This improves privacy control, provider portability, cost control,
testability, client isolation and auditability.

------------------------------------------------------------------------

## 12. Prompt Caching / Provider State

Provider privacy analysis must include more than visible prompt/response
storage. OpenAI documentation describes prompt-caching behavior and
endpoint-specific state semantics.

Therefore:

> ZDR must not be translated into an unqualified claim that absolutely
> no technical state of any kind exists anywhere after inference.

For V1, do not enable optional provider persistence/caching features
without demonstrated product value and understood data-control
semantics.

------------------------------------------------------------------------

## 13. Exact Financial Values --- Founder F4

Founder F4 remains authoritative.

### Decision

Exact financial values may cross the governed provider boundary when
materially necessary for professional financial reasoning.

The objective is:

> **MINIMUM NECESSARY FINANCIAL REALITY\
> + PSEUDONYMIZED IDENTITY\
> + AUTHORIZED ENTITY/ENGAGEMENT CONTEXT\
> + TASK-SPECIFIC DISCLOSURE\
> + GOVERNED PROVIDER EGRESS**

Potentially necessary exact values include revenue, margin, EBITDA,
cash, debt, working capital, budget/actual variance, ratios, runway,
covenants, scenario assumptions and projections.

Identity disclosure and financial-information disclosure must be
governed separately.

------------------------------------------------------------------------

## 14. Narrative / Identity --- Founder F7

Initial V1 real-client external inference permits:

-   structured governed disclosure;
-   governed `BOUNDED_TEXT`.

Unrestricted arbitrary narrative is not authorized for initial V1
real-client egress.

Direct identity must not be restored merely because exact financial
values are required.

Future governed rich narrative remains deferred Product/Security
research and must not be architecturally made impossible.

------------------------------------------------------------------------

## 15. API Surface Philosophy

Prefer API usage that is:

-   stateless or minimally stateful;
-   explicitly governed;
-   compatible with approved retention policy;
-   compatible with regional requirements;
-   compatible with ZDR where required;
-   intercepted by `LlmEgressAuthority`;
-   free from unnecessary provider-owned persistent memory.

Endpoint/model choice is part of the disclosure policy, not merely an
implementation convenience.

------------------------------------------------------------------------

# 16. Provider Gates

## PG-1 --- Training / Data Sharing

**Requirement:** No voluntary OpenAI API data-sharing/training opt-in.

**Evidence required:** - current official OpenAI policy; - effective
Pepperyn organization/project setting; - no explicit opt-in enabled.

**Status:** CONDITIONAL PASS --- provider capability confirmed;
effective config still to verify.

------------------------------------------------------------------------

## PG-2 --- DPA

**Requirement:** Current OpenAI DPA applicable to the Pepperyn legal
entity/processing relationship.

**Evidence required:** - contracting entity; - DPA version/date; -
acceptance/execution status where required; - appropriate Pepperyn
legal/privacy review.

**Status:** CONDITIONAL PASS --- DPA available; Pepperyn-specific state
to verify.

------------------------------------------------------------------------

## PG-3 --- Zero Data Retention

**Requirement:** Target production project uses ZDR for real-client
inference unless a later explicit Founder/Security decision approves
another profile.

**Evidence required:** - eligibility; - approval where required; -
effective configuration; - endpoint/feature compatibility.

**Status:** OPEN.

------------------------------------------------------------------------

## PG-4 --- European Region

**Requirement:** European regional processing/data-residency controls
where supported and selected for V1.

**Evidence required:** - production project region; - endpoint/region
configuration; - model compatibility; - regional/ZDR prerequisites.

**Status:** OPEN.

------------------------------------------------------------------------

## PG-5 --- Endpoint / Feature Policy

**Requirement:** Only explicitly approved OpenAI surfaces may receive
Pepperyn real-client payloads.

Maintain an allow-list binding where appropriate:

-   provider;
-   endpoint;
-   model/model family;
-   region;
-   retention class;
-   task class.

Avoid unnecessary persistent conversation/storage features.

**Status:** OPEN.

------------------------------------------------------------------------

## PG-6 --- Subprocessor Governance

**Requirement:** Maintain a current record of relevant
provider/subprocessor chain and processing implications.

**Evidence required:** - current official list; - processing-location
implications; - consistent privacy wording; - change-monitoring
responsibility.

**Status:** CONDITIONAL PASS.

------------------------------------------------------------------------

## PG-7 --- Effective Account Evidence

**Requirement:** Verify the actual Pepperyn OpenAI organization/project,
not generic provider documentation.

Evidence should include, without secrets:

-   organization/project identity;
-   production/development separation;
-   data-sharing setting;
-   retention/ZDR status;
-   region;
-   approved endpoint/model configuration;
-   relevant account-level controls;
-   evidence date and reviewer.

**Status:** BLOCKED until the effective project/configuration exists or
is accessible.

------------------------------------------------------------------------

## PG-8 --- Code Enforcement

**Requirement:** Approved provider policy becomes executable.

The governed security boundary must fail closed when real-data provider
configuration is not approved.

Potential enforcement dimensions:

-   provider allow-list;
-   endpoint allow-list;
-   region;
-   retention class;
-   task class;
-   real-data admission capability;
-   provider-policy version.

Caller code must not be trusted to declare provider compliance.

**Status:** CODE ENFORCEMENT IMPLEMENTED / OPERATIONAL ACTIVATION CLOSED.
The local PG-8 contract requires a size-bounded, SHA-256-pinned, exact-scope
evidence manifest; an approved policy version; a named project; effective DPA;
disabled data sharing; European Responses endpoint; ZDR; an approved model;
`store=false`; an approved task; and evidence no older than 90 days.  The
issuer-bound authorization is tied to the exact canonical request hash and is
verified immediately before the sole transport boundary. Missing, expired,
tampered or mismatched state fails closed. This validates code enforcement
only: it does not prove the truth of the external account evidence, and it does
not activate transport or real-data admission.

------------------------------------------------------------------------

## 17. Consolidated Gate Matrix

  -----------------------------------------------------------------------------
  Gate              Requirement             Current status    Real-data blocker
  ----------------- ----------------------- ----------------- -----------------
  PG-1              No                      Conditional pass  Yes until
                    training/data-sharing                     effective config
                    opt-in                                    verified

  PG-2              Applicable DPA          Conditional pass  Yes until
                                                              Pepperyn state
                                                              verified

  PG-3              ZDR target              Open              Yes

  PG-4              European regional       Open              Yes under target
                    configuration                             architecture

  PG-5              Approved                Open              Yes
                    endpoint/feature policy                   

  PG-6              Subprocessor governance Conditional pass  Yes until
                                                              operationally
                                                              recorded

  PG-7              Effective account       Blocked pending   Yes
                    evidence                configuration     

  PG-8              Code-level enforcement  Implemented;      Yes until
                                             activation closed PG-1--PG-7 pass
  -----------------------------------------------------------------------------

### Overall

> **OPENAI API --- APPROVED PROVIDER CANDIDATE, CONDITIONALLY**

> **REAL-CLIENT EXTERNAL INFERENCE --- NOT AUTHORIZED**

------------------------------------------------------------------------

## 18. What Work Must Not Do

Work must not:

-   redo broad provider research without a concrete freshness gap;
-   copy historical Anthropic assumptions into OpenAI architecture;
-   assume no-training means no-retention;
-   assume ZDR before account evidence;
-   weaken Pepperyn pseudonymization because provider controls exist;
-   treat certifications as a substitute for Pepperyn controls;
-   enable real-client admission;
-   use persistent provider conversations merely for convenience;
-   place API keys/secrets in governance artifacts;
-   create another provider transport outside `LlmEgressAuthority`;
-   turn this gate into a general GDPR project.

------------------------------------------------------------------------

## 19. Later Work Instructions

At provider-admission stage, Work should:

1.  verify that official OpenAI policy has not materially changed;
2.  inspect the effective Pepperyn API organization/project
    configuration;
3.  evidence PG-1 through PG-7;
4.  implement/verify PG-8;
5.  test fail-closed provider admission;
6.  perform independent security review;
7.  only then recommend opening real-client inference.

If official provider policy changes materially, update this gate
explicitly.

------------------------------------------------------------------------

## 20. Required Real-Data Admission Evidence Package

Before real-client inference, preserve a compact evidence package
containing:

-   Provider Gate version;
-   provider-policy verification date;
-   applicable DPA reference/status;
-   ZDR approval/configuration evidence;
-   regional processing configuration;
-   approved endpoint/model policy;
-   data-sharing/training setting evidence;
-   subprocessor review date;
-   effective project/account identifier without secrets;
-   code-enforcement test result;
-   final LLM Egress Trust Gate result;
-   independent promotion verdict.

------------------------------------------------------------------------

## 21. Candidate Executable Admission Invariant

``` text
REAL_DATA_EGRESS_ALLOWED
IFF
    authenticated_request
AND ownership_verified
AND entity_engagement_scope_verified
AND correspondence_valid
AND disclosure_policy_passed
AND payload_provenance_valid
AND provider_policy_version_approved
AND provider_project_verified
AND retention_policy_approved
AND region_approved
AND endpoint_approved
AND real_data_admission_capability_valid
AND LlmEgressAuthority_is_only_transport
```

Failure of any required condition:

``` text
NO PROVIDER DISPATCH
```

This is a candidate future invariant, not authorization to implement
prematurely.

------------------------------------------------------------------------

## 22. Product / Commercial Consequences

### Do not promise

> "No financial data leaves Pepperyn."

This would be unnecessarily restrictive and may conflict with
professional reasoning.

### Preferred conceptual direction

Future legal/marketing review may work from:

> Pepperyn minimizes and pseudonymizes information before governed
> external inference. Only information necessary for the authorized task
> is disclosed through controlled provider boundaries configured
> according to Pepperyn's privacy and retention requirements.

This is **not approved final legal or marketing copy**.

Also do not promise:

> "Data is processed only by OpenAI."

The actual provider/subprocessor chain must be represented accurately.

------------------------------------------------------------------------

## 23. Source-of-Truth / Freshness Rule

Provider policy is time-sensitive.

Before real-data admission, Work must re-check current official OpenAI
sources.

Use authoritative OpenAI documentation rather than historical project
assumptions or third-party summaries.

### Official sources reviewed

**API data controls / retention / endpoint behavior**\
https://platform.openai.com/docs/models/default-usage-policies-by-endpoint

**OpenAI Zero Data Retention information**\
https://openai.com/index/offering-zero-data-retention-for-frontier-models/

**OpenAI Data Processing Addendum**\
https://openai.com/policies/data-processing-addendum/

**OpenAI Subprocessor List**\
https://openai.com/policies/sub-processor-list/

**OpenAI Security and Privacy**\
https://openai.com/security-and-privacy/

------------------------------------------------------------------------

## 24. Work Handover Decision

Work must treat the following as operative:

> **OPENAI API IS AN APPROVED PROVIDER CANDIDATE FOR PEPPERYN V1,
> CONDITIONALLY.**

Target:

> **EUROPEAN PROCESSING + ZDR + NO TRAINING OPT-IN + APPROVED
> STATELESS/MINIMALLY STATEFUL API SURFACE + PEPPERYN-OWNED MEMORY +
> GOVERNED `LlmEgressAuthority`.**

Founder F4:

> Exact financial values may be externally processed when materially
> necessary for professional financial reasoning, provided
> identity/context disclosure is minimized and governed.

Founder F7:

> Initial V1 real-client egress is structured disclosure plus governed
> `BOUNDED_TEXT`; unrestricted arbitrary narrative remains deferred
> research, not permanently forbidden architecture.

### Final rule

> **DO NOT ENABLE REAL-CLIENT EXTERNAL INFERENCE UNTIL PG-1 THROUGH PG-8
> HAVE PASSED WITH EFFECTIVE, DATED EVIDENCE.**

------------------------------------------------------------------------

## 25. Recommended Next Product Milestone

This Provider Gate should now leave the active critical path until
operational verification becomes possible.

The parallel product milestone is:

> **FOUNDER FIRST-ENGAGEMENT REHEARSAL**

Prepare a realistic end-to-end financial engagement so that once the LLM
Egress Trust Gate and Provider Gate permit it, Pepperyn can immediately
be evaluated as an actual Fractional CFO working environment rather than
continuing architecture-first development.

------------------------------------------------------------------------

# FINAL STATUS

**OPENAI PROVIDER GATE V1 --- CONDITIONAL PASS**

**OPENAI API --- APPROVED PROVIDER CANDIDATE**

**REAL-DATA ADMISSION --- CLOSED**

**SYNTHETIC DEVELOPMENT --- AUTHORIZED**

**NEXT PROVIDER ACTION --- EFFECTIVE ACCOUNT / ZDR / REGION / ENDPOINT
VERIFICATION BEFORE REAL-CLIENT ADMISSION**

------------------------------------------------------------------------

## 26. Effective-account checkpoint — 2026-09-07

- **PG-1 effective configuration:** PASS. Founder-observed organization
  settings show model-feedback sharing, evaluation/fine-tuning sharing and
  input/output sharing all disabled. No voluntary training/data-sharing opt-in
  is active.
- **Current project inventory:** the organization exposes only its historical
  default project, configured with Global geography and no project data
  retention profile. No dedicated Pepperyn API project exists yet.
- **PG-3 / PG-4:** OPEN. The new-project form exposes only a project name and
  no region selector, so this organization is not currently evidenced as
  eligible for project-level European data residency. ZDR is not shown as
  enabled. OpenAI support has been asked for the supported individual-founder
  eligibility path; no approval is assumed while that request is pending.
- **Current API contract:** the official Responses reference confirms that
  `store` defaults to true if omitted, that `store=false` is supported, and
  that Structured Outputs are configured through `text.format`. Current data
  controls documentation lists `/v1/responses` and Structured Outputs as
  supported for European processing, subject to account eligibility,
  retention controls and model support. PG-8 therefore remains correctly
  strict on `store=false`, the EU base URL, ZDR and the approved model.
- **PG-2 / PG-6:** provider capability evidence remains available, but the
  Pepperyn-specific DPA applicability/effectiveness and dated operational
  subprocessor review remain incomplete. Neither is inferred from dashboard
  configuration.
- **Decision:** no Global project will be created as a substitute for the
  required regional/ZDR evidence. Real-data admission and provider transport
  remain CLOSED while the external request is pending.

------------------------------------------------------------------------

## 27. Official-response and effective-project proof update — 2026-09-09

### New provider evidence received

The Founder received a response from the OpenAI Privacy Team directing
Pepperyn to the official OpenAI Data Processing Addendum. This is dated
evidence that the provider identifies the DPA as the contractual source for the
enquiry. It strengthens PG-2 at provider-document level, but does not by itself
prove that the Pepperyn contracting party has accepted every required
amendment or that a particular API project has European geography and Zero
Data Retention.

Official OpenAI documentation rechecked on 2026-09-09 confirms that API data
is not used for model training by default unless the customer opts in; ZDR is
available to approved customers at organization or project level; data
residency is configured per project; and European regional requests use
`https://eu.api.openai.com/v1`. Non-US residency also requires approval for
abuse-monitoring controls and an applicable retention amendment. Endpoint,
feature and model compatibility remains material: ZDR does not make an
otherwise ineligible stateful feature non-retaining.

### Remaining proof for the effective Pepperyn project

The following evidence is cumulative. Generic documentation, a DPA link, or a
successful request alone cannot substitute for it.

1. **Contracting and eligibility:** identify the actual Pepperyn API
   contracting party and applicable OpenAI entity without placing personal
   data in this repository; preserve the DPA version/date and evidence of
   applicability or acceptance; preserve OpenAI approval for the required
   abuse-monitoring control and applicable non-US retention amendment; record
   any account-specific exception communicated by OpenAI.
2. **Dedicated project:** create or identify a dedicated Pepperyn API project
   whose geography is visibly `Europe (EEA + Switzerland)`; preserve its
   non-secret project/organization identifiers, purpose, creation date and
   environment separation. The historical Global default project is not
   sufficient.
3. **Effective ZDR:** capture the project Data Retention screen and retrieve
   `GET /organization/projects/{project_id}/data_retention` with an Admin API
   key. Require `zero_data_retention` (or `enhanced_zero_data_retention` if
   specifically approved). If it returns `organization_default`, separately
   retrieve the organization setting and resolve the effective value. `none`
   is a failure. Preserve no secret or unredacted key.
4. **Project-bound credential:** create a project service account or API key
   scoped only to that European project; preserve only its identifier/redacted
   value and project association; prove Pepperyn cannot silently fall back to
   an organization/default-project key.
5. **Transport policy:** bind `LlmEgressAuthority` to
   `https://eu.api.openai.com/v1`, an approved endpoint and an eligible pinned
   model/snapshot; keep `store=false`; prohibit incompatible persistent
   surfaces/options including provider conversations/threads,
   `background=true`, and any feature not proven ZDR-eligible; verify every
   production-capable OpenAI call site uses this boundary without caller
   overrides.
6. **Synthetic activation proof:** only after items 1–5 pass, run one
   payload-free or synthetic sentinel through the real governed transport;
   preserve a redacted request manifest proving policy version, project, EU
   base URL, endpoint, model, `store=false`, task and absence of stateful tools;
   prove fail-closed behavior for Global endpoint, wrong project credential,
   non-ZDR state, unsupported feature/model, stale evidence and missing
   evidence; obtain independent security review before any gate-opening
   recommendation.

### Updated disposition

- **PG-1:** PASS on the already observed disabled sharing settings and current
  no-training-by-default policy; recheck at promotion.
- **PG-2:** CONDITIONAL PASS, strengthened by the Privacy Team response and DPA
  reference; Pepperyn-specific applicability/acceptance and the required
  retention amendment remain unevidenced.
- **PG-3:** OPEN — no effective Pepperyn-project ZDR result captured.
- **PG-4:** OPEN — no dedicated European Pepperyn project captured.
- **PG-5:** OPEN — exact endpoint/model/feature policy not activated against an
  eligible project.
- **PG-6:** CONDITIONAL PASS — dated operational subprocessor review required.
- **PG-7:** BLOCKED — effective project and project-bound credential evidence
  remain absent.
- **PG-8:** IMPLEMENTED / ACTIVATION CLOSED — generic provider evidence cannot
  activate it.

**Decision:** the new official evidence narrows the remaining work but opens no
gate. External Provider remains **CLOSED**. Real-data admission remains
**CLOSED**. V30 synthetic follow-up work may continue independently.

### Official sources rechecked

- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
- [Retrieve project data retention](https://developers.openai.com/api/reference/python/resources/admin/subresources/organization/subresources/projects/subresources/data_retention/methods/retrieve)
- [Retrieve organization data retention](https://developers.openai.com/api/reference/python/resources/admin/subresources/organization/subresources/data_retention/methods/retrieve)
- [OpenAI Projects Admin API](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/projects)
