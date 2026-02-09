# Reports

This folder contains **example output files** from Aura Guard benchmarks (JSON / JSONL).

Why keep this folder?
- It gives new users a **real artifact** they can inspect.
- It makes your README/demo claims more trustworthy ("show, don't tell").

## Files included

- `2026-02-09_claude-sonnet-4_ab.json`
  - A sample **live A/B** report (5 runs per scenario).
  - This is the same file referenced from `docs/LIVE_AB_EXAMPLE.md`.

## Generate your own report

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python examples/live_test.py --ab --runs 5 --json-out reports/YYYY-MM-DD_<model>_ab.json
```

## Important notes

- **Don't commit real customer data** here. The included scenarios are synthetic examples.
- If your report files become large, consider keeping only **one** sample file in the repo,
  and store the rest locally (or use Git LFS).
