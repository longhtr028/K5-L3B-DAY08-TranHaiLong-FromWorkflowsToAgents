"""Shape C: delegate scoped reads using a typed handoff, then settle in code."""

from __future__ import annotations

from contextlib import closing

from lab8.db import connect
from lab8.handoff import make_handoff
from lab8.runtime import run_readonly_investigators
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
        run = ClaimRun(conn, "orchestrator", claim_id, seed)
        if early := run.early_result():
            return early

        handoff = make_handoff(
            request_id=f"REQ-{claim_id}",
            claim_id=claim_id,
            task="gather_refund_evidence",
            facts={},
            allowed_tools=["lookup_order", "lookup_policy"],
        )
        run.trace.add("handoff", handoff)
        investigated = run_readonly_investigators(
            conn, run.budget, handoff, principal_id=run.claim["principal_id"]
        )["tools"]
        run.trace.add("investigation", {"policy_count": len(investigated["lookup_policy"]["policies"])})
        return run.settle(investigated["lookup_order"], crash_at=crash_at)
