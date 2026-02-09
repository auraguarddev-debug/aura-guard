# Publishing Results

This repo contains both a **synthetic benchmark harness** and **live integration tests**.

The most credible way to share results on GitHub is:

1) provide a **reproducible command**, and  
2) commit a **machine-readable artifact** (JSON / JSONL), and  
3) keep the README summary short.

## Recommended structure

Create a `reports/` folder and store:

- `reports/<date>_<model>_ab.json` — live A/B summary + per-run metrics
- `reports/<date>_<model>_transcript.jsonl` — optional transcripts (sanitized)
- `reports/<date>_<model>_RESULTS.md` — a short narrative (1 page)

Example:

```
reports/
  2026-02-08_claude-sonnet-4_ab.json
  2026-02-08_claude-sonnet-4_transcript.jsonl
  2026-02-08_RESULTS.md
```

## What to include in README

- the command you ran
- a small table with the key aggregates (cost/tool calls/quality)
- one or two sentences about limitations

Avoid dumping long logs or huge JSON blobs into the README.

## Cost disclaimer (important)

The USD values in reports are **estimates** based on your configured:

- tool call prices (`CostModel.default_tool_call_cost` or per-tool costs)
- token pricing (`CostModel.input_token_cost_per_1k` / `CostModel.output_token_cost_per_1k`)

Absolute $ numbers may differ across providers and model pricing.
The meaningful signal is usually the **relative delta** between baselines under the same configuration.

## Handling failures

If a live test fails to call the provider API (auth/rate limit/network), the run should be marked as failed and excluded from averages.
