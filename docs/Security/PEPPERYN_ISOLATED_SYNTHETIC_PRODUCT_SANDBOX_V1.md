# Pepperyn Isolated Synthetic Product Sandbox v1

Status: development-only product experiment. This is not a production trust boundary and is not evidence of real-data safety.

## Boundary

The sandbox has one registered source: `OPTILUX_V3`, whose exact repository bytes must hash to `6C66DE79F3AEBDACD41CE70AB38070C15A2516912105FB8E226A38CAAFCBFADB`. The loader accepts no path, upload, company ID, entity ID, analysis ID, correspondence, memory, decisions, or caller-authored prompt.

The closed flow is:

`registered Optilux fixture → AnalysisResult → ExecutiveDecisionModel + DecisionKernel → fixed Founder review task → sealed sandbox request → LlmEgressAuthority → OpenAI Responses API → sandbox-only structured result`

No production router imports the sandbox. The sandbox imports no Supabase, production memory, correspondence, upload, or production repository adapter. The production `dispatch` method and real-data admission remain unchanged and closed.

The OpenAI call is stateless (`store: false`), uses no provider conversation or provider-side enterprise memory, and requests strict JSON-schema output. The sandbox fails closed without `OPENAI_API_KEY`. The API is used according to the official [Responses API reference](https://developers.openai.com/api/reference/cli/resources/responses/methods/create).

## Product logic reused

- canonical `AnalysisResult` validation;
- deterministic Executive Decision Model construction;
- canonical Decision Kernel extraction;
- the existing `LlmEgressAuthority` as the sole provider transport;
- existing PDF, PPTX and Excel renderers remain available to the Founder workflow and are not forked by the sandbox.

The Optilux fixture begins after historical ingestion and already contains the canonical analysis result. This v1 therefore evaluates financial interpretation, deterministic diagnosis, recommendations, uncertainty, investigation questions and executive reasoning; it does not claim to rehearse arbitrary workbook upload or fresh ingestion.

## Explicit non-goals

This sandbox does not generalize synthetic provenance, admit real data, certify provider output, connect production persistence, or create a reusable sandbox platform.

## Real-data admission blockers preserved

- **RD-1:** immutable provider-response snapshots.
- **RD-2:** non-strippable provider-derived provenance and governed terminal consumption.
- **RD-3:** real source to every dynamic disclosure lineage.
- **RD-4:** nested schemas/types/ranges plus provider and response hashing.
- **RD-5:** response-registry expiry and pruning.

All five remain mandatory before Milestone B.
