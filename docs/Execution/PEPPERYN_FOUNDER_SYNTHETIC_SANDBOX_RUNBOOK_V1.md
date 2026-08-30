# Founder Synthetic Sandbox Runbook v1

## Before the session

1. Use branch `work/synthetic-founder-rehearsal-v1` in a development environment. Do not deploy it to production.
2. Create a dedicated OpenAI development-project API key with an appropriate spend limit.
3. Set it only in the current terminal as `OPENAI_API_KEY`. Never paste it into Git, Markdown, fixtures, logs, or application configuration committed to the repository.
4. From `backend`, run: `python -m sandbox.run_founder_rehearsal`.

The command has no file, company, analysis, upload, prompt, or database argument. It refuses execution if Optilux differs from the registered hash or if the credential is absent.

## Founder rehearsal

Inspect the deterministic Optilux diagnosis and GPT review. Assess whether the output:

1. identifies the main financial tension;
2. separates facts, calculations and uncertainty;
3. proposes useful, prioritized decisions;
4. asks questions that genuinely advance the investigation;
5. reduces reconstruction and prompting work;
6. is usable as an executive starting point.

Record each observation in the scorecard. Record elapsed time and the returned input/output token counts. Do not substitute another company or paste external client material into this sandbox.

## Stop/reset

Stop the process normally. Remove `OPENAI_API_KEY` from the terminal environment when finished. The sandbox creates no provider conversation and no production database record; delete any locally redirected output if it should not be retained.
