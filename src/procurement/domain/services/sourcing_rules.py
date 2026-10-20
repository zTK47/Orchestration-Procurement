"""The Sourcing Funnel: resolves a ParsedRequest to a single CatalogItem.

Steps (see docs/specs/UC-002-resolve-item.md for the full Given/When/Then spec):
  1. Filter to CatalogItems whose category matches and whose supplier is
     APPROVED.
  2. Filter out items with insufficient stock or a lead time longer than
     allowed.
  3. Rank the remaining items by unit price, ascending.
  4. If two or more items are tied for the lowest price, raise
     RequiresClarificationError (a human must decide -- this is a deliberate
     design choice, not a bug: see ADR-002).
  5. If nothing survives the filters, raise NoMatchingCatalogItemError.
"""
from __future__ import annotations

from procurement.domain.entities import CatalogItem, Supplier
from procurement.domain.exceptions import (
    NoMatchingCatalogItemError,
    RequiresClarificationError,
)
from procurement.domain.value_objects import ParsedRequest


class SourcingRule:
    """Stateless domain service implementing the Sourcing Funnel."""

    def resolve(
        self,
        parsed_request: ParsedRequest,
        catalog_items: list[CatalogItem],
        suppliers: dict[str, Supplier],
        max_lead_time_days: int = 14,
    ) -> CatalogItem:
        candidates = self._filter_by_category_and_approved_supplier(
            catalog_items, suppliers, parsed_request.category
        )
        candidates = self._filter_by_stock_and_lead_time(
            candidates, parsed_request.quantity, max_lead_time_days
        )

        if not candidates:
            raise NoMatchingCatalogItemError(
                f"No approved, in-stock catalog item found for category "
                f"'{parsed_request.category}' (quantity={parsed_request.quantity})."
            )

        candidates.sort(key=lambda item: item.unit_price.amount)
        cheapest_price = candidates[0].unit_price.amount
        tied = [c for c in candidates if c.unit_price.amount == cheapest_price]

        if len(tied) > 1:
            skus = ", ".join(c.sku.value for c in tied)
            raise RequiresClarificationError(
                f"Multiple catalog items are tied at the lowest price "
                f"({cheapest_price}): {skus}. Manual selection required."
            )

        return candidates[0]

    @staticmethod
    def _filter_by_category_and_approved_supplier(
        catalog_items: list[CatalogItem],
        suppliers: dict[str, Supplier],
        category: str,
    ) -> list[CatalogItem]:
        result = []
        for item in catalog_items:
            if item.category.lower() != category.lower():
                continue
            supplier = suppliers.get(item.supplier_id)
            if supplier is None or not supplier.approved:
                continue
            result.append(item)
        return result

    @staticmethod
    def _filter_by_stock_and_lead_time(
        catalog_items: list[CatalogItem],
        required_quantity: int,
        max_lead_time_days: int,
    ) -> list[CatalogItem]:
        return [
            item
            for item in catalog_items
            if item.stock_qty >= required_quantity
            and item.lead_time_days <= max_lead_time_days
        ]
