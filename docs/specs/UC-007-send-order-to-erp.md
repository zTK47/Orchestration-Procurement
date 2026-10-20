# UC-007 — Send Order To ERP

## Intent
Hand an approved order to the ERP and keep its purchase-order reference.

## Actors
System; ERP via the `ErpGateway` port (mock adapter, ADR-006).

## Preconditions
Request is `APPROVED`.

## Flow
1. Check the transition is legal, then call `send_purchase_order`.
2. Store the returned reference; status `ORDER_SENT`; save.

## Errors
- Request not `APPROVED` → `IllegalStatusTransitionError`, the ERP is not called.
- ERP failure → `ErpGatewayError` (HTTP 502), status and reference unchanged.

## Acceptance
- Given an approved request, then it is `ORDER_SENT` with an `erpReference`.
- Given an ERP failure, then the request stays `APPROVED`.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_erp_use_cases.py` |
| Integration | `tests/integration/test_procurement_request_repository.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py`, `tests/e2e/test_catalog_selection_and_errors_e2e.py` |
