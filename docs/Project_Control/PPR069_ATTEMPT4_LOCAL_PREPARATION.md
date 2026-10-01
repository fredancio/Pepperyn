# PPR-069 attempt 4 — distinct local preparation

Status: LOCAL PASS / REMOTE NOT EXECUTED / DISTINCT READ-ONLY GO REQUIRED.
Date: 2026-10-01. Source baseline: e4adc576e590d168af81c83726906256277909d5.

The corrected protocol remains byte-for-byte unchanged, SHA-256
FB7AA56B9209392B6E64E4C125DACF4551CA27F129A91E175269152FE7B8861F.
Attempt 3 remains evidence of its single partial read-only observation, not a
full precontrol PASS. Its old protocol hash is incompatible with the corrected
reader. No prior manifest, deadline, identity, SQL or evidence was overwritten.

## Frozen attempt

Directory: C:/Users/ADMIN-FRED/Documents/Codex/Pepperyn-runtime/v41-injected-4.
Created: 2026-10-01T07:24:01.869336+00:00.
Deadline: 2026-10-02T07:24:01.869336+00:00 (09:24:01 Brussels).
The existing 24-hour window is unchanged, not extended or reset.
The manifest checkpoint_head remains the original protocol ancestry anchor
ccab95c2b6bfeaaae59ecbcbfea1da38f8231ca5, not a claim about the current HEAD.

- policy: 7d25327c-a7e4-47d5-a072-0c47762ae869
- request: 7a1ae69d-d46e-46cf-8e60-a495da6a9e36
- execution: 2d3ca8b3-77a5-4dfc-886b-f7447f5ab616
- analysis: 4ee7a1cd-75ed-49d3-8956-10bf3aa6f1c4

File SHA-256 values (not the manifest's internal canonical digest):

- manifest.json: 520E5AF5400C888F0C6285BC9D9D0B14B43A7422EE9701A2C8207D3256CA11E7
- precontrol.sql: 2CC9AAFEE6045AD03BA617E3E2003EBFA9BD8C482EEAFD21F6E5185E261AB10E
- policy-insert.sql: 100595FCE7C83B9616896C568347454455153B2FCB482FD084AFD443613BA37A
- policy-disable.sql: 74A4B93645CC1C91AF5C8BE2034F9D5A7704A095ECF44940C3B769E2EE60CF34

The mutation SQL files are generated inert artifacts only, NOT authorized for
execution. No precontrol-ready attestation, Auth session or effect journal was
created. The runner and wrapper now select attempt 4, never a prior directory.

## Local evidence

10 tests PASS, zero skipped, 3 dependency deprecation warnings, 27.05 seconds:
test_v41_injected_rehearsal_launcher.py,
test_v41_successor_precontrol_postgres.py,
test_v41_injected_successor_postgres.py.
PostgreSQL ran in pepperyn-b1-policy-test with network mode none, no host ports
and no host bind mounts. The previously stopped container was stopped again.

Coverage: complete single-JSON SQL; missing/active historical policy; evidence
and binding mismatch; scope, search_path and permission drift; extra policy and
occupied identities; owner deadline handoff; one-auth/effect ceilings; new
directory refusal; manifest mutation and new identity separation.
The actual attempt-4 manifest passed the production reader locally. Its three
SQL files were compared byte-for-byte to their deterministic generated values.
All four identities are disjoint from all prior attempt identities. The
21 historical file hashes in PPR069_ATTEMPT4_PRESERVED_ARTIFACTS.json are pinned
for pre/post-checkpoint preservation, including the unchanged historical policy
disable artifact. No remote state was inspected or inferred during this slice.

## Next GO, strictly separate from execution

After checkpoint synchronization, authorize only one execution of the exact
attempt-4 precontrol.sql on Pepperyn Integration Test ejixkplrgobgwqnhidwt,
before the frozen deadline and after verifying its SHA-256. Capture its single
complete JSON. Require the aggregate and all nested checks to PASS, and compare
all returned historical row/catalog fingerprints with preserved historical
evidence. historical_comparison_required=true must not be ignored. A missing
baseline, incomplete result, mismatch or expired window is STOP, not readiness.
No repeat SQL, Auth, policy insertion, rehearsal, provider or data mutation.
Any later rehearsal still requires a separate Founder GO and fresh checks.

B1 OPEN; Generic Producer UNADMITTED; External Provider CLOSED;
Real-data Admission CLOSED. No gate or historical proof is requalified.
