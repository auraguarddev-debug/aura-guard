# Aura Guard Evaluation Plan

This document describes a reproducible evaluation methodology for Aura Guard, focused on cost containment, risk reduction, and output quality.

The goal is to answer, with evidence:

1) **Does Aura Guard reduce tool/agent cost?**  
2) **Does it prevent repeated side effects?**  
3) **Does it maintain task success/quality?**  
4) **Does it avoid unacceptable latency or false positives?**

---

## 1) Define “success” up front

You need success criteria that are specific, measurable, and hard to argue with.

### Primary success metrics (what to optimize)

**A. Cost reduction (per task/run)**
- Δ Tool cost (USD)  
- Δ Total cost (USD) = tool cost + model tokens (input+output) if available  
- Track mean and **p50/p90/p95**

**B. Risk reduction**
- Duplicate side-effects prevented (count)
- Side-effect tool executions per run (mean, p95)
- Number of “would-have-double-charged/refunded/emailed” incidents prevented

**C. Reliability**
- Task success rate (completion rate)
- Escalation rate (should not spike unexpectedly)
- Time-to-resolution / turns-to-resolution (p50/p90)

### Guard safety metrics (what must not regress)

**D. False positives**
- Legit tool calls blocked/denied that were necessary for task completion

**E. False negatives**
- Loops that still happened (excess tool calls, repeated errors, repeated side effects)

**F. Latency overhead**
- Additional time per tool call (should be small; measure in your environment)

---

## 2) Choose baselines (so it’s not “guard vs nothing”)

A credible evaluation compares against simple, common safeguards:

1. **No guard** (current behavior)
2. **Global step cap** (e.g., hard stop after N tool calls)
3. **Per-tool cap only** (max N calls to search/retrieval)
4. **Aura Guard full policy** (your intended config)

This prevents the critique: “You could have solved this with a simple step limit.”

---

## 3) Measurement design: how to avoid biased results

### Recommended design: randomized A/B by run
- For each task/run, randomly assign to baseline vs Aura Guard.
- Pin model version + temperature + tools + prompts.
- Run enough samples to stabilize p90/p95.

If you can’t do strict A/B in production:
- Use **shadow mode** first (see below), then a controlled rollout.

### Always log these per run
- run_id, timestamp
- model name/version
- tool calls: executed / denied / cached / failed
- total tool cost estimate
- token usage (input/output) if available
- outcome: success/fail/escalate
- reason codes: which guard primitive triggered (max_calls_per_tool, error_retry, etc.)

---

## 4) Step-by-step evaluation phases

### Phase 0 — Regression harness (fast, deterministic)
Purpose: ensure changes don’t break guard behavior.

Run the synthetic suite:

```bash
aura-guard bench --all --json-out bench_report.json
```

What to report:
- Total saved tool cost in the harness (as regression signal)
- Number of prevented side effects
- Which scenarios trigger rewrites/escalations

What NOT to claim:
- “This proves production savings.” It doesn’t. It proves *logic coverage*.

---

### Phase 1 — Live model harness (real LLM behavior, rigged tools)
Purpose: demonstrate to skeptics that the guard catches **real model loops**, not just scripted steps.

Anthropic harness:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python examples/live_test.py --ab --runs 5 --json-out ab.json --transcript-out transcript.jsonl
```

Report:
- A/B cost delta (tool cost tracked)
- Interventions per scenario
- Before/after tool calls per scenario
- Include a short transcript excerpt showing a real loop and a guard stop

Limitations (be explicit):
- Tools are intentionally rigged to trigger loops
- This is a “failure-mode demo,” not production replay

---

### Phase 2 — Shadow mode in your real agent
Purpose: evaluate false positives and missed loops *before* blocking anything.

How shadow mode works:
- You run Aura Guard decisions, but **you still execute tools**.
- You log what Aura Guard *would* have done and compare against what actually happened.

What to measure:
- How often Aura Guard would deny a call
- In those cases, whether the call was actually useful/necessary
- Identify the tools most often involved (usually search/retrieval + side effects)

Output artifact:
- A weekly “shadow report”:
  - top deny reasons
  - top tools triggering denies
  - estimated cost avoided
  - examples of dangerous repeats (especially side effects)

Decision gate:
- Only move to enforcement when false positives are low and you understand them.

---

### Phase 3 — Enforced pilot (small scope, high-value tools first)
Purpose: get real savings with minimal risk.

Suggested rollout order:
1) **Side-effect idempotency only** (refund/send/cancel)  
2) Add **error retry circuit breaker** for flaky tools  
3) Add **per-tool cap** for expensive query tools  
4) Add **budget cap** for whole run

During pilot, track:
- success rate vs baseline
- escalation rate vs baseline
- tool cost delta
- number of prevented duplicate side effects (often the strongest business-risk metric)

---

## 5) Quality evaluation (so you’re not just “saving money by stopping early”)

Engineers will ask: “Did it still solve the task?”

Pick one of these approaches:

### Option A — Ground-truth tasks (best if you have them)
For tasks like order status, refund policy, ticket lookup:
- define expected fields in the final answer (status, dates, amounts)
- score outputs automatically

### Option B — Human rating (fast to start)
Have 2 humans rate each run on:
- correctness (1–5)
- completeness (1–5)
- helpfulness (1–5)

Require no more than X% degradation vs baseline.

### Option C — LLM-as-judge (acceptable for early signal)
Use a fixed judge prompt and a fixed judge model.
Be honest that it’s not a substitute for ground truth.

---

## 6) Credible reporting format (what to show)

### A/B summary table (example structure)
Include **p50/p90/p95**:

- Tool calls executed
- Tool calls denied
- Total tool cost (USD)
- Total token cost (USD) if available
- Success rate
- Escalation rate
- Duplicate side effects prevented

### Distribution plot (optional but convincing)
Even one chart that shows “tail risk” reduction (p95 cost) is powerful.

### “Top triggers” breakdown
Show how the guard is saving money:
- max_calls_per_tool
- identical repeat caching
- error retry circuit breaker
- idempotency ledger

---

## 7) Case study template (1–2 pages)

Use this structure to create credible “customer stories” (even if the customer is you).

### Title
**“Reduced agent tool spend by X% and prevented Y duplicate side-effects in Z days.”**

### Context
- What agent does (support triage, research, booking, billing, etc.)
- Tools used (search, CRM, payments, ticketing, email)
- Model used and orchestration stack

### Problem
- Concrete incident examples (dates, counts)
- Observed failure modes (loops, retries, duplicate actions)

### Setup
- Guard configuration (side_effect_tools, max_calls_per_tool, max_cost_per_run, error_retry_threshold)
- Baselines used
- Sample size and time window

### Results
- p50/p90/p95 cost per run (before/after)
- Success rate and escalation rate (before/after)
- Side effects prevented (absolute count)
- Examples (1–2 transcripts) of “bad loop stopped safely”

### ROI framing
- Estimated monthly savings (based on run volume)
- Risk reduction narrative (duplicate refunds avoided)

### Limitations / next steps
- Known false positives and mitigations
- Planned improvements (token-cost accounting, better tool classification)

---

## 8) Communicating results

Different audiences care about different outcomes. When you publish results, keep them grounded in the primary metrics:

- **Engineering:** fewer loops, fewer retries, fewer duplicate side effects, lower p95 cost, fewer incidents.
- **Product/ops:** higher task completion rate, lower escalation rate, shorter time-to-resolution.
- **Security/compliance:** clear logs of blocked/denied side effects, auditability, and safe defaults.

Avoid over-claiming from synthetic harnesses. Treat them as regression coverage; use shadow mode / pilot data for real-world claims.

---

## 9) Checklist to run before you publish results

- [ ] Bench results are labeled “synthetic harness”
- [ ] Live harness results are labeled “rigged tools, real model”
- [ ] Pilot results include success-rate comparison
- [ ] You report percentiles, not just averages
- [ ] You include at least one transcript showing the loop + guard stop
- [ ] You disclose cost model assumptions (tool costs, token pricing)

---

## Appendix: minimal “pilot config” recommendation

Start conservative:

- `side_effect_tools = {"refund", "send_reply", "cancel"}`
- `max_calls_per_tool = 3` for query tools
- `error_retry_threshold = 2`
- `max_cost_per_run = $0.50` (or your preferred cap)

Then tune based on shadow mode logs.

