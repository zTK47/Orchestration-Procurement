# OPO-UC-002 — Generate Order Request

## Intent
Turn a free-text order prompt plus a stored supplier offer into a structured
`OrderRequest` with line items, using the `OrderGenerationAgent` port (ADR-007).

## Actors
Human buyer; `OrderGenerationAgent` (mock adapter, ADR-007/ADR-008).

## Preconditions
The referenced `SupplierOffer` exists. A new `OrderRequest` starts in `DRAFT`.

## Flow
1. Load the offer; call `OrderGenerationAgent.generate(prompt_text, offer)`.
2. Store the returned line items on the request; status `DRAFT → GENERATED`; save.

## Errors
- Unknown offer → `UnknownSupplierOfferError` (HTTP 422), the agent is not called.
- Request not in `DRAFT` (e.g. `SENT`) → `IllegalStatusTransitionError` (HTTP 422), the agent is not called.
- Agent output fails its schema check → `OrderGenerationError` (HTTP 502), nothing stored.

## Acceptance
- Given an offer listing "Dell Latitude 5440 Laptop" at CHF 1250 and the prompt
  "3 Dell Latitude laptops", then the request is `GENERATED` with one line item, quantity 3, unit price 1250.
- Given a prompt naming an item not in the offer, then a line item is still produced (unit price 0)
  so that validation can flag it — generation never silently drops what the user asked for.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/application/test_generate_order_request.py`, `tests/unit/order_pdf_orchestration/infrastructure/test_mock_order_generation_agent.py` |
| Integration | — |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
