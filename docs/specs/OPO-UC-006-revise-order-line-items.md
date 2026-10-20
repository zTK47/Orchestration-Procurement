# OPO-UC-006 — Revise Order Line Items

## Intent
The human fallback from the whiteboard ("System/Human"): when validation cannot
confirm an order, a person corrects or re-confirms the line items and the order
goes back to `GENERATED` for another validation. Added on 2026-10-01 (team decision).

## Actors
Human buyer (demo page or API).

## Preconditions
Request is `NEEDS_CLARIFICATION`.

## Flow
1. The buyer submits the full corrected list of line items.
2. The line items are replaced, previous validation notes cleared; status `NEEDS_CLARIFICATION → GENERATED`; save.
3. The buyer runs OPO-UC-003 again; the rules decide again (no manual override).

## Errors
- Request not `NEEDS_CLARIFICATION` (e.g. `SENT`) → `IllegalStatusTransitionError` (HTTP 422).
- Empty list → `EmptyOrderRequestError` (HTTP 422).
- Quantity ≤ 0 or negative price → `InvalidLineItemError` / HTTP 422 from the API schema.

## Acceptance
- Given a request in `NEEDS_CLARIFICATION`, when the buyer fixes the unmatched item, then it is `GENERATED`,
  and validating again gives `VALIDATED`.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/application/test_revise_order_line_items.py` |
| Integration | — |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
