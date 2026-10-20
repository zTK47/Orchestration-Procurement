# UC-006 — Record Approval Decision

## Intent
Record one approver's decision; when every required level has approved, spend the budget.

## Actors
Manager, Budget Owner.

## Preconditions
Request is `PENDING_APPROVAL` with its required levels set.

## Flow
1. Check that the approver's role matches the level and has not decided this level yet.
2. Save the `Approval`. A rejection moves the request to `REJECTED`.
3. If levels are still missing, stay `PENDING_APPROVAL`.
4. If all approved: re-check the budget, deduct it, move to `APPROVED`.

## Errors
- Wrong role → `UnauthorizedApproverError`.
- Same approver, same level, twice → `DuplicateApprovalError`.
- Budget consumed meanwhile → `BudgetExceededError`, request stays `PENDING_APPROVAL`.

## Acceptance
- Given all required levels approve and budget remains, then `APPROVED` and `budget_spent` grows by the amount.
- Given any rejection, then `REJECTED` (terminal).

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_record_approval_decision_use_case.py` |
| Integration | `tests/integration/test_approval_repository.py` |
| E2E | `tests/e2e/test_catalog_selection_and_errors_e2e.py` |
