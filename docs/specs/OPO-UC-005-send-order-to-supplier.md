# OPO-UC-005 — Send Order To Supplier

## Intent
Send the validated order and its PDF to the supplier automatically and keep the
supplier's reference.

## Actors
System; `SupplierGateway` (mock adapter).

## Preconditions
Request is `VALIDATED` (rule 5) and its PDF has been rendered (team decision 2026-10-01:
the supplier always receives the document).

## Flow
1. Check `VALIDATED → SENT` is legal and a `pdf_reference` exists.
2. Call `SupplierGateway.send_order(order, supplier)`; store `supplier_reference`; status `SENT`; save.

`SENT` is terminal (rule 6): no regeneration, revalidation, revision or resend.

## Errors
- Request not `VALIDATED`, including already `SENT` → `IllegalStatusTransitionError` (HTTP 422), gateway not called.
- No PDF rendered → `PdfNotRenderedError` (HTTP 422), gateway not called.
- Gateway failure → `SupplierGatewayError` (HTTP 502), status unchanged.

## Acceptance
- Given a validated request with a PDF, then it is `SENT` with a `supplierReference`.
- Given a `SENT` request, when sent again, then it is refused and the supplier is not contacted twice.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/application/test_send_order_to_supplier.py` |
| Integration | — |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
