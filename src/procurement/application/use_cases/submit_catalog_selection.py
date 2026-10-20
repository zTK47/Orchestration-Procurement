"""UC-005 - see docs/specs/UC-005-submit-catalog-selection.md

Covers the "Catalog" intake mode from the original brainstorm (as opposed to
"Free text", handled by ParseRequestUseCase + ResolveItemUseCase). Here the
user already knows exactly which CatalogItem they want, so there is no
sourcing/ranking to do -- only a check that the chosen item is still valid
(approved supplier, sufficient stock).

The third whiteboard intake mode, "OCI Punchout" (an external hosted-catalog
protocol), is deliberately out of scope for this prototype -- see
docs/PROJECT.md "Future Work" and docs/adr/ADR-005.
"""
from __future__ import annotations

from procurement.application.ports.repositories import (
    CatalogItemRepository,
    ProcurementRequestRepository,
    SupplierRepository,
)
from procurement.domain.entities import ProcurementRequest
from procurement.domain.exceptions import SelectedItemUnavailableError
from procurement.domain.value_objects import SKU, Money, ParsedRequest


class SubmitCatalogSelectionUseCase:
    def __init__(
        self,
        catalog_repository: CatalogItemRepository,
        supplier_repository: SupplierRepository,
        procurement_repository: ProcurementRequestRepository,
    ) -> None:
        self._catalog_repository = catalog_repository
        self._supplier_repository = supplier_repository
        self._procurement_repository = procurement_repository

    def execute(self, request: ProcurementRequest, sku: SKU, quantity: int) -> ProcurementRequest:
        """Given a freshly created ProcurementRequest (status CREATED) and a
        directly chosen SKU + quantity, validates availability and advances
        the request straight to RESOLVED -- skipping the sourcing/ranking
        step used by the free-text intake mode."""
        catalog_item = next(
            (item for item in self._catalog_repository.list_all() if item.sku == sku),
            None,
        )
        if catalog_item is None:
            raise SelectedItemUnavailableError(f"No catalog item found for SKU {sku.value}.")

        suppliers = self._supplier_repository.get_all_by_id()
        supplier = suppliers.get(catalog_item.supplier_id)
        if supplier is None or not supplier.approved:
            raise SelectedItemUnavailableError(
                f"Catalog item {sku.value} is supplied by an unapproved supplier."
            )

        stock_check = "PASSED" if catalog_item.stock_qty >= quantity else "FAILED"
        if stock_check == "FAILED":
            raise SelectedItemUnavailableError(
                f"Catalog item {sku.value} has insufficient stock "
                f"({catalog_item.stock_qty} available, {quantity} requested)."
            )

        # Direct catalog selections skip free-text parsing, but the state
        # machine still requires passing through PARSED on the way to
        # RESOLVED -- we record a synthetic, high-confidence ParsedRequest
        # built directly from the chosen item (see docs/PROJECT.md).
        request.mark_parsed(
            ParsedRequest(
                quantity=quantity,
                product_name=catalog_item.product_name,
                category=catalog_item.category,
                confidence=1.0,  # user-selected directly: certain, not inferred
            )
        )
        total_amount = Money(
            amount=catalog_item.unit_price.amount * quantity,
            currency=catalog_item.unit_price.currency,
        )
        request.mark_resolved(
            sku=catalog_item.sku,
            supplier_id=catalog_item.supplier_id,
            amount=total_amount,
            stock_check=stock_check,
        )
        self._procurement_repository.save(request)
        return request
