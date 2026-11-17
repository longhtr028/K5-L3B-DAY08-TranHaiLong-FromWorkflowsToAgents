"""Shape B: a bounded ReAct loop with read tools and host-owned settlement."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from lab8.db import connect
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import RunResult
from lab8.shapes.workflow import ClaimRun


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    with closing(connect(store_path)) as conn:
        run = ClaimRun(conn, "single", claim_id, seed)
        if early := run.early_result():
            return early

        # The agent sees observations for these reads only. The claim fixes
        # the order lookup arguments before the model picks an action.
        pending = ["lookup_order", "lookup_policy"]
        order_view = None

        def decide(observation: dict[str, Any]) -> dict[str, Any]:
            nonlocal order_view
            last_tool = observation.get("last_tool")
            if last_tool == "lookup_order":
                order_view = observation["last_result"]
                run.trace.add("read", {"tool": last_tool, "visible": order_view["visible"]})
            elif last_tool == "lookup_policy":
                run.trace.add("read", {"tool": last_tool, "policy_count": len(observation["last_result"]["policies"])})

            if not pending or (order_view is not None and not order_view["visible"]):
                return {"final": {}}

            choice = 0
            if len(pending) > 1:
                # MockLLM returns a seeded digest instead of a tool-call object.
                # Use one bit of the digest to select from the finite action set.
                reply = complete(run.budget, seed=seed, purpose="choose_read", prompt=", ".join(pending))
                choice = int(reply.endswith(("1", "3", "5", "7", "9", "b", "d", "f")))
            name = pending.pop(choice)
            run.trace.add("action", {"tool": name})
            return {"tool": name, "args": run.order_args() if name == "lookup_order" else {}}

        outcome = run_react(conn, run.budget, observation={}, decide=decide, max_steps=8, worker=True)
        if outcome["stopped"] == "step_cap":
            return run.finish("failed", "step_cap")
        if order_view is None:
            return run.finish("failed", "missing_order_evidence")
        return run.settle(order_view, crash_at=crash_at)
