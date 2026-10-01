# PPR-069 Owner Ack transfer and next-protocol proposal

Status: LOCAL PROPOSAL / NO NEW ATTEMPT / NO REMOTE AUTHORIZATION.
Date: 2026-10-01.
Implementation baseline: ff14a3237152388c6b32989f29f5fd80f39874e9.

## Scope and historical boundaries

Attempt 4 is terminated permanently. Its five remote object counts were zero;
the historical policy remained conformant and disabled. The original network
cause remains UNESTABLISHED and the earlier SUBMISSION_UNRESOLVED is unchanged.
No previous attempt, identity, deadline, manifest, SQL or acknowledgement may be
reused. This document allocates none. The historical protocol and wrapper hashes
are not changed by this proposal.

## Exact local acknowledgement contract

The insertion acknowledgement has exactly these five fields (placeholders are
descriptive and must never be executed):

```json
{
  "schema_version": "v41-owner-local-ack-1",
  "action": "insert",
  "manifest_sha256": "<future frozen manifest digest>",
  "policy_id": "<future frozen policy identity>",
  "sql_sha256": "<future frozen policy-insert.sql digest>"
}
```

For disablement, action is disable and sql_sha256 binds policy-disable.sql.
The fields are resolved exclusively from separately verified frozen artifacts,
not free-text Founder entry and not blindly copied from a mutable marker.
No credentials, tokens, observed_at, claimed remote success or permission are
carried in this file. It does not count as an Auth or remote effect.

The future publisher must verify the exact checkpoint and its own pinned hash,
canonical manifest/SQL hashes and the matching owner-action started marker.
It must refuse a missing marker, completed/refused attempt, unknown action,
existing final or pending acknowledgement, unexpected path or mismatched field.
Insertion freshness and deadline must still be valid. The human must have
observed one successful SQL submission and an uninterrupted waiting runner;
an uncertain SQL outcome is not acknowledged as success and is never retried.

Publication sequence on Windows, same directory and volume:

1. Verify all preconditions; never create an attempt directory.
2. Exclusively create owner-insert-ack.pending (or owner-disable-ack.pending).
3. Write the complete UTF-8 JSON without BOM; flush to disk and close the file.
4. Revalidate the pending bytes, frozen bindings, terminal state and freshness.
5. Publish with the two-argument System.IO.File.Move(pending, final), where
   final is owner-insert-ack.json or owner-disable-ack.json. No overwrite flag.
6. On failure, preserve all files and stop. Do not overwrite, remove or retry.

The pending name is deliberately not watched. Same-volume rename prevents the
reader from consuming a half-written final file. Unsupported filesystem/rename
behavior is a refusal, not a fallback to copy or direct writing. A successful
rename consumes the pending path; that is publication, not historical cleanup.
The final JSON and the started marker remain proof artifacts.

## Proposed next rehearsal sequence

Before asking for a distant GO: prepare a separately authorized fresh manifest,
new identities, deadline and pinned artifacts; validate and checkpoint the new
publisher/launcher/protocol together. Preserve all previous attempts and prove
new identities absent with the authorized fresh read-only precontrol. Record
complete results, compare historical hashes and retain explicit time evidence.

The actual rehearsal, only under a new bounded distant GO:

1. Verify artifacts, one-shot state, project, freshness and remote baselines.
2. Create the exclusive local insertion-handoff marker and wait locally.
3. Founder verifies editor content/project and executes the exact INSERT once.
4. After definite success, Founder runs the pinned local publisher once.
5. Runner rechecks freshness/bindings, makes one policy observation and validates
   target/historical policies. Existing separate admission/receipt/history reads
   remain obligatory; one policy observation does not mean one total safety read.
6. Only after those checks, authenticate once; no refresh or second login.
7. Preserve foreign-scope and substituted-request refusals, exact reserve/claim,
   injected completion, and completion-replay refusal.
8. Request exact policy disablement. Founder executes it once and publishes the
   distinct disable acknowledgement. Observe once; verify irreversible disable.
9. Preserve post-disable refusal, independent-process recovery, owner reread,
   UI component and XLSX/PDF/PPTX checks, and historical postcontrol.
10. Stop with the bounded result; no continuation is implicitly authorized.

The normal ceiling remains ten effect-capable requests (one Auth included) and
five new durable rows: policy/admission/analysis/envelope/receipt. Policy SELECTs
and local acknowledgements do not authorize additional writes. Retain the
existing effect budget and count any safety-disable write within the applicable
GO, never as a free retry. No substitute identities, cleanup or second attempt.

## Failure and safety branch

Local expiry, absent/invalid acknowledgement, policy absence/mismatch or a single
read exception terminates execution. No Auth may follow an unverified insertion.
Acknowledged insert plus failed observation means remote state UNKNOWN, not
ABSENT. If a policy may be active, preserve evidence and request the separately
bounded read-only/safety action unless explicitly covered by the future GO.
Never execute an INSERT after the runner has stopped. Never renew a handoff.

Normal and safety disable observation use the same disable handoff identity.
If that handoff has already failed/been consumed, it cannot be started again;
an independent read-only diagnostic must resolve the state. A successful remote
disable with a failed observation is not permission to issue another UPDATE.
The 1,200-second disable-observation limit does not prolong insertion freshness.

## Evidence, limits and readiness

Checkpointed Owner Ack evidence: 57 PASS; two identity-generation tests remain
NOT EXECUTED. No PostgreSQL, live transport, real Auth, full rehearsal or new
UI/export proof is claimed by this transfer proposal. The historical
governed chain is not closed by an acknowledgement.

Additional local validation exercises the exact Windows no-overwrite rename
primitive in a dedicated scratch directory, using an existing test payload:
partial pending file is invisible as final; complete publication preserves
bytes; pending is consumed; existing final refuses and remains unchanged; an
incomplete abandoned pending remains preserved and never becomes final.
Executed result: LOCAL_ATOMIC_PUBLICATION: 5 CHECKS PASS. Script preserved at
Pepperyn-runtime/verify-owner-ack-atomic-publication-local.ps1; scratch evidence
at Pepperyn-runtime/owner-ack-publication-local-proof. No real attempt artifact
was used or modified. This proves publication mechanics, not a completed
successor launcher. The 57 earlier tests were not rerun in this document-only
protocol formalization and are retained as checkpointed evidence, not new runs.

Before READY, remaining local work is explicit: a pinned publisher implementing
all checks above, end-to-end local tests of its interaction with the runner,
final matching protocol/launcher pins, a new authorized manifest and fresh
read-only baseline. No distant GO can be executable against placeholders.

## Smallest next Founder decision

Authorize LOCAL preparation only of a distinct successor, including new frozen
identities/deadline, the concrete pinned acknowledgement publisher and amended
launcher/protocol; require full local tests and a durability checkpoint before
presenting any distant command. This local GO must not authorize Supabase,
technical Auth, policy insertion, rehearsal or egress.

Once that preparation is READY, present a separate exact distant GO identifying
the artifact hashes and target. It must retain LOCAL_TEST_ADMISSION,
INJECTED_LOCAL_ONLY, provider_execution_attested=false, one Auth, ten effects,
five durable rows, exact safety-disable scope, no retry and no historical change.
This proposal itself supplies neither authorization.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. Generic admission, egress and provider attestation
remain distinct. No attempt 5, new identity or remote access performed here.
