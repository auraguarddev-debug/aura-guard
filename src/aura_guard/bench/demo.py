"""aura_guard.bench.demo

Quick demo showing Aura Guard vs no protection vs naive call limit.
Used by CLI: aura-guard demo
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..middleware import AgentGuard
from ..types import PolicyAction


def _bad_agent_steps() -> List[Tuple[str, Any]]:
    """Scripted broken agent: triple refund, jitter search, apology loop."""
    steps: List[Tuple[str, Any]] = []

    for _ in range(3):
        steps.append(("tool", ("refund", {"order_id": "o1", "amount": 10}, "t1")))

    queries = [
        "refund policy", "refund policy EU", "refund policy Germany",
        "refund policy EU Germany", "refund policy EU Germany 2024",
        "refund policy EU Germany 2024", "refund policy EU Germany 2024",
        "refund policy EU Germany 2024",
    ]
    for q in queries:
        steps.append(("tool", ("search_kb", {"query": q}, None)))

    for _ in range(6):
        steps.append(("llm", "I apologize for the inconvenience. We're looking into it."))

    steps.append((
        "llm",
        '{"action":"finalize","reason":"ready","reply_draft":"Your refund has been processed.","escalation":null}',
    ))
    return steps


def _mock_execute(name: str, args: Dict[str, Any]) -> Any:
    if name == "refund":
        return {"status": "refunded", **args}
    if name == "search_kb":
        return {"hits": [f"KB:{args.get('query', '')}"]}
    return {"status": "ok"}


@dataclass
class _Row:
    name: str
    calls: int
    side_fx: int
    blocks: int
    cache: int
    rewrites: int
    cost: float
    terminated: Optional[str]


def _run_no_guard() -> _Row:
    executed = side_fx = 0
    for kind, payload in _bad_agent_steps():
        if kind == "tool":
            name, args, _ = payload
            _mock_execute(name, args)
            executed += 1
            if name == "refund":
                side_fx += 1
    return _Row("no_guard", executed, side_fx, 0, 0, 0, executed * 0.04, None)


def _run_call_limit(limit: int = 5) -> _Row:
    executed = side_fx = 0
    terminated = None
    for kind, payload in _bad_agent_steps():
        if kind == "tool":
            if executed >= limit:
                terminated = "call_limit"
                break
            name, args, _ = payload
            _mock_execute(name, args)
            executed += 1
            if name == "refund":
                side_fx += 1
    return _Row(f"call_limit({limit})", executed, side_fx, 0, 0, 0, executed * 0.04, terminated)


def _run_aura_guard() -> _Row:
    guard = AgentGuard(
        max_cost_per_run=0.50,
        side_effect_tools={"refund", "send_reply", "cancel"},
        secret_key=b"aura_guard_demo_key",
    )
    executed = side_fx = 0
    terminated = None

    for kind, payload in _bad_agent_steps():
        if terminated:
            break
        if kind == "tool":
            name, args, ticket_id = payload
            d = guard.check_tool(name, args=args, ticket_id=ticket_id)
            if d.action == PolicyAction.ALLOW:
                result = _mock_execute(name, args)
                guard.record_result(ok=True, payload=result)
                executed += 1
                if name == "refund":
                    side_fx += 1
            elif d.action in (PolicyAction.ESCALATE, PolicyAction.FINALIZE):
                terminated = d.action.value
        else:
            stall = guard.check_output(payload)
            if stall and stall.action in (PolicyAction.ESCALATE, PolicyAction.FINALIZE):
                terminated = stall.action.value

    return _Row("aura_guard", executed, side_fx, guard.blocks, guard.cache_hits,
                guard.rewrites, guard.cost_spent, terminated)


def run_demo(json_out: Optional[str] = None) -> None:
    """Run the triage simulation demo and print results."""
    import datetime

    a = _run_no_guard()
    b = _run_call_limit(5)
    c = _run_aura_guard()

    print()
    print("=" * 64)
    print("  Aura Guard — Triage Simulation Demo")
    print("=" * 64)
    print(f"  Assumed tool-call cost: $0.04 per call\n")

    fmt = "  {:<24} {:>6} {:>7} {:>7} {:>7} {:>8}  {}"
    print(fmt.format("Variant", "Calls", "SideFX", "Blocks", "Cache", "Cost", "Terminated"))
    print("  " + "─" * 72)

    for r in (a, b, c):
        print(fmt.format(
            r.name, r.calls, r.side_fx, r.blocks, r.cache,
            f"${r.cost:.2f}", r.terminated or "-",
        ))

    saved = a.cost - c.cost
    pct = (saved / a.cost * 100) if a.cost else 0
    print()
    print(f"  Cost saved vs no_guard:     ${saved:.2f} ({pct:.0f}%)")
    print(f"  Side-effects prevented:     {a.side_fx - c.side_fx}")
    print(f"  Rewrites issued:            {c.rewrites}")
    print()

    if json_out:
        from .. import __version__

        def _row_dict(r: _Row) -> Dict[str, Any]:
            return {
                "variant": r.name,
                "tool_calls": r.calls,
                "side_effects": r.side_fx,
                "blocks": r.blocks,
                "cache_hits": r.cache,
                "rewrites": r.rewrites,
                "cost_usd": round(r.cost, 4),
                "terminated": r.terminated,
            }

        report = {
            "type": "aura_guard_demo",
            "version": __version__,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tool_call_cost_usd": 0.04,
            "variants": {
                "no_guard": _row_dict(a),
                "call_limit": _row_dict(b),
                "aura_guard": _row_dict(c),
            },
            "comparison": {
                "cost_saved_usd": round(saved, 4),
                "cost_saved_pct": round(pct, 1),
                "side_effects_prevented": a.side_fx - c.side_fx,
                "rewrites_issued": c.rewrites,
            },
        }

        import json as json_mod
        with open(json_out, "w") as f:
            json_mod.dump(report, f, indent=2)
        print(f"  JSON report saved to: {json_out}")
        print()
