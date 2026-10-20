# UC-005 — Submit Catalog Selection

## Intent
Second intake mode: the requester picks a SKU and quantity directly, so no parsing or ranking is needed. (OCI Punchout, the third mode, is out of scope — ADR-005.)

## Actors
Requester.

## Preconditions
A new `ProcurementRequest` in `CREATED`.

## Flow
1. Look up the SKU; check supplier approval and stock.
2. Record a synthetic `ParsedRequest` (confidence 1.0), then resolve with `unit price × quantity`.

## Errors
- Unknown SKU, unapproved supplier or insufficient stock → `SelectedItemUnavailableError`.

## Acceptance
- Given a valid SKU and enough stock, then status is `RESOLVED` with the correct total and `stock_check = PASSED`.
- Given any error case above, then no request state is stored.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_submit_catalog_selection_use_case.py` |
| E2E | `tests/e2e/test_catalog_selection_and_errors_e2e.py` |
