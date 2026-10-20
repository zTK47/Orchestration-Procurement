# UC-009 — Complete Request

## Intent
Close the request after goods receipt.

## Actors
System or requester.

## Preconditions
Request is `GOODS_RECEIPT`.

## Flow
1. Status `COMPLETED` (terminal); save.

## Errors
- Any other status → `IllegalStatusTransitionError`.

## Acceptance
- Given a goods receipt, then `COMPLETED` and `nextState` is `null`.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_erp_use_cases.py`, `tests/unit/domain/test_procurement_request.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
