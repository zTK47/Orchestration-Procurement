# UC-002 — Resolve Item (Sourcing Funnel)

## Intent
Find the single best `CatalogItem` for a parsed request.

## Actors
System, after UC-001.

## Preconditions
Request is `PARSED`.

## Flow
1. Keep items of the same category from an **approved** supplier.
2. Drop items with too little stock or a lead time above 14 days.
3. Rank by unit price; the cheapest wins.
4. Store SKU, supplier, total amount (`unit price × quantity`), `stock_check = PASSED`; status `RESOLVED`.

## Errors
- Nothing survives the filters → `NoMatchingCatalogItemError`.
- Two or more items tie for the lowest price → `RequiresClarificationError` (ADR-002).
- Request not parsed → `ValueError`.

## Acceptance
- Given two approved items, when resolving, then the cheaper one is chosen.
- Given the cheapest item is from an unapproved supplier, then it is ignored.
- Given insufficient stock or a lead time above 14 days, then the item is ignored.
- Given a price tie, then resolution fails and the status stays `PARSED`.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/domain/test_sourcing_rules.py`, `tests/unit/application/test_resolve_item_use_case.py` |
| Integration | `tests/integration/test_catalog_and_supplier_repositories.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
