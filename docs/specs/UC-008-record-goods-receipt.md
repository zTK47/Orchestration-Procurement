# UC-008 — Record Goods Receipt

## Intent
Book the delivery of the goods in the ERP and in the request.

## Actors
Requester or warehouse; ERP via `ErpGateway`.

## Preconditions
Request is `ORDER_SENT` and has an `erp_reference`.

## Flow
1. Check the transition, then call `post_goods_receipt(erp_reference)`.
2. Status `GOODS_RECEIPT`; save.

## Errors
- Request not `ORDER_SENT` → `IllegalStatusTransitionError`, the ERP is not called.
- ERP failure → `ErpGatewayError`, status unchanged.

## Acceptance
- Given a sent order, then `GOODS_RECEIPT` and the ERP received the reference.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_erp_use_cases.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
