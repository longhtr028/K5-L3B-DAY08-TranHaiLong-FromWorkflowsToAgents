"""Shape A: fixed reads, a deterministic quote, and a host-controlled refund."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

from lab8 import durability
from lab8.db import connect
from lab8.runtime import dispatch
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import tool_cost
from lab8.trace import Trace


class ClaimRun:
    """Shared result and refund handling; each shape gathers order evidence."""

    def __init__(self, conn: sqlite3.Connection, shape: str, claim_id: str, seed: int):
        self.conn = conn
        self.shape = shape
        self.claim_id = claim_id
        self.seed = seed
        self.budget = Budget()
        self.trace = Trace(make_run_id(shape, claim_id, seed))
        self.claim = dispatch(conn, self.budget, "get_claim_view", {"claim_id": claim_id}, worker=True)
        self.trace.add("claim_read", {"found": self.claim["found"], "has_order": bool(self.claim.get("order_id"))})

    def early_result(self) -> RunResult | None:
        if not self.claim["found"]:
            return self.finish("failed", "unknown_claim")
        if not self.claim.get("order_id"):
            return self.finish("needs_info", "missing_order_id")
        return None

    def order_args(self) -> dict[str, str]:
        # The caller has already checked that the claim has an order.
        return {key: self.claim[key] for key in ("order_id", "principal_id")}

    def finish(self, status: str, reason: str | None = None, proposal: int = 0) -> RunResult:
        self.trace.add("decision", {"status": status, "reason": reason})
        return finish(
            self.conn,
            shape=self.shape,
            claim_id=self.claim_id,
            seed=self.seed,
            status=status,
            proposal_amount=proposal,
            budget=self.budget,
            trace=self.trace,
            error_reason=reason,
        )

    def settle(self, order_view: dict[str, Any], *, crash_at: str | None) -> RunResult:
        self.trace.add("order_scope", {"visible": order_view["visible"], "reason": order_view["reason"]})
        if not order_view["visible"]:
            return self.finish("escalated", order_view["reason"])

        quote = dispatch(
            self.conn, self.budget, "compute_compensation", {"order": order_view["order"]}, worker=True
        )
        proposal = quote["amount_vnd"]
        quote_reason = quote["reason"]
        if quote_reason.startswith("order_status_"):
            # The quote helper embeds the raw order status in this reason.
            quote_reason = "ineligible_order_status"
        self.trace.add("quote", {"amount_vnd": proposal, "reason": quote_reason})
        if proposal <= 0:
            return self.finish("denied", quote_reason)

        # The host subtracts prior refunds for the order. Send the full quote.
        self.budget.add_tool(tool_cost())
        outcome = durability.issue_refund(self.conn, self.claim_id, proposal, crash_at=crash_at)
        reason = outcome["reason"]
        if reason.startswith("approval_") and reason not in {
            "approval_claim_mismatch", "approval_expired", "approval_revoked", "approval_pending",
        }:
            # Nonstandard approval states are arbitrary strings in the store.
            reason = "invalid_approval_status"
        self.trace.add("host_refund", {"ok": outcome["ok"], "reason": reason})
        if outcome["ok"]:
            return self.finish("resolved", proposal=proposal)
        return self.finish("failed" if outcome["conflict"] else "denied", reason, proposal)


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    with closing(connect(store_path)) as conn:
        run = ClaimRun(conn, "workflow", claim_id, seed)
        if early := run.early_result():
            return early
        order_view = dispatch(conn, run.budget, "lookup_order", run.order_args(), worker=True)
        return run.settle(order_view, crash_at=crash_at)
