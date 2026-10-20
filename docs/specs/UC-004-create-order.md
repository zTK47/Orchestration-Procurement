# UC-004 — Create Order

## Intent
Decide which human approvals an order needs from its amount, and move it on.

## Actors
System, after UC-003.

## Preconditions
Request is `VALIDATED`.

## Flow
1. `ApprovalRoutingPolicy` returns the required levels (thresholds 1000 / 10000).
2. No level → `APPROVED`; otherwise → `PENDING_APPROVAL`.

## Errors
- Request has no amount → `ValueError`.
- Request not `VALIDATED` → `IllegalStatusTransitionError`.

## Acceptance
- Given amount ≤ 1000, then the request is `APPROVED` without approvals.
- Given 1000 < amount ≤ 10000, then `PENDING_APPROVAL` with `MANAGER`.
- Given amount > 10000, then `MANAGER` and `BUDGET_OWNER` are required.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/domain/test_approval_routing_policy.py`, `tests/unit/application/test_create_order_use_case.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
