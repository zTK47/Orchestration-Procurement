# UC-003 — Validate Request

## Intent
Check that the resolved amount fits the cost center's remaining budget. Approval routing is not part of this use case (UC-004).

## Actors
System, after UC-002 or UC-005.

## Preconditions
Request is `RESOLVED`; its cost center exists.

## Flow
1. Compare the amount with `budget_total − budget_spent`.
2. Set `budget_check = PASSED`, status `VALIDATED`; save.

## Errors
- Amount above the available budget → `BudgetExceededError`, status stays `RESOLVED`.
- Request not resolved, or unknown cost center → `ValueError`.

## Acceptance
- Given enough budget, then status is `VALIDATED` and no approval level is decided yet.
- Given too little budget, then validation fails and nothing changes.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_validate_request_use_case.py` |
| Integration | `tests/integration/test_cost_center_repository.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
