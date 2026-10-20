# OPO-UC-001 — Upload Supplier Offer

## Intent
Store a supplier's offer as raw text so that an order can later be generated from it
and checked against it. Bounded context: Order PDF Orchestration (OPO).

## Actors
Human buyer (demo page or API).

## Preconditions
The supplier exists (seeded suppliers in this slice).

## Flow
1. The buyer pastes the offer text and picks a supplier.
2. The system checks the supplier exists, stores the `SupplierOffer` and returns its id.

Scope: pasted text only. Out: file upload and PDF/DOCX parsing (backlog).

## Errors
- Unknown supplier → `UnknownSupplierError` (HTTP 422), nothing stored.
- Empty or whitespace-only text → `InvalidSupplierOfferError` (HTTP 422; the API also rejects an empty string).

## Acceptance
- Given a known supplier and non-empty text, when uploaded, then the offer can be read back by its id.
- Given an unknown supplier, then the upload fails and nothing is stored.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/order_pdf_orchestration/application/test_upload_supplier_offer.py` |
| Integration | — (in-memory repositories only in this slice) |
| E2E | `tests/e2e/order_pdf_orchestration/test_order_flow_e2e.py` |
