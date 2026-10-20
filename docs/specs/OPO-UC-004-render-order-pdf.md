# OPO-UC-004 — Render Order PDF

## Intent
Produce the order document the supplier will receive: a real PDF file with supplier,
line items and total, via the `DocumentRenderer` port.

## Actors
System; `DocumentRenderer` (mock adapter that writes a real PDF with fpdf2).

## Preconditions
Request is `VALIDATED`.

## Flow
1. Load the supplier of the request's offer.
2. Call `DocumentRenderer.render(order, supplier)`; store the returned `pdf_reference`; save.
3. The PDF can be downloaded via `GET /order-requests/{id}/pdf`.

Rendering does not change the status. Rendering again on a `VALIDATED` request replaces the file.

## Errors
- Request not `VALIDATED` → `OrderNotValidatedError` (HTTP 422), the renderer is not called.

## Acceptance
- Given a validated request, then `pdfReference` is set and the downloaded file starts with `%PDF-`.
- Given a request in `NEEDS_CLARIFICATION`, then no PDF is produced.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/application/test_render_order_pdf.py`, `tests/unit/order_pdf_orchestration/infrastructure/test_mock_document_renderer.py` |
| Integration | — |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
