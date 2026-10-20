# OPO-UC-003 — Validate Order Request

## Intent
Check a generated order against business rules before anything is sent. What the
rules cannot confirm goes to a human (`NEEDS_CLARIFICATION`), never auto-approved.

## Actors
System (`OrderValidationRule`); human fallback via OPO-UC-006.

## Preconditions
Request is `GENERATED`; its offer exists.

## Flow
1. Evaluate `OrderValidationRule` against the request and its offer:
   - at least one line item (rule 1);
   - every line item description matches the offer text (rule 2: case-insensitive keyword check).
2. All checks pass → `VALIDATED`. Otherwise → `NEEDS_CLARIFICATION`, with one
   `validation_notes` entry per problem. Save.

Rules enforced elsewhere: quantity > 0 and unit price ≥ 0 when a line item is created (rule 3);
total = Σ quantity × unit price (rule 4).

## Errors
- Request not `GENERATED` (e.g. `SENT`, `VALIDATED`) → `IllegalStatusTransitionError` (HTTP 422).
- The aggregate itself refuses `VALIDATED` with zero line items → `EmptyOrderRequestError`.

## Acceptance
- Given all line items found in the offer, then `VALIDATED` and no notes.
- Given one line item not in the offer, then `NEEDS_CLARIFICATION` with a note naming that item.
- Given no line items, then `NEEDS_CLARIFICATION` with a note.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/domain/test_order_validation_rule.py`, `tests/unit/order_pdf_orchestration/application/test_validate_order_request.py` |
| Integration | — |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
