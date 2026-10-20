"""UC-002 - see docs/specs/UC-002-resolve-item.md"""
from __future__ import annotations

from procurement.application.ports.repositories import (
    CatalogItemRepository,
    ProcurementRequestRepository,
    SupplierRepository,
)
from procurement.domain.entities import ProcurementRequest
from procurement.domain.services.sourcing_rules import SourcingRule
from procurement.domain.value_objects import Money


class ResolveItemUseCase:
    def __init__(
        self,
        catalog_repository: CatalogItemRepository,
        supplier_repository: SupplierRepository,
        procurement_repository: ProcurementRequestRepository,
        sourcing_rule: SourcingRule | None = None,
    ) -> None:
        self._catalog_repository = catalog_repository
        self._supplier_repository = supplier_repository
        self._procurement_repository = procurement_repository
        self._sourcing_rule = sourcing_rule or SourcingRule()

    def execute(self, request: ProcurementRequest) -> ProcurementRequest:
        """Given a PARSED ProcurementRequest, runs the Sourcing Funnel and
        advances its status to RESOLVED.

        May raise NoMatchingCatalogItemError or RequiresClarificationError
        (both domain errors, propagated as-is -- the Interfaces layer is
        responsible for translating them into HTTP responses)."""
        if request.parsed_data is None:
            raise ValueError("ProcurementRequest must be parsed before it can be resolved.")

        catalog_items = self._catalog_repository.list_all()
        suppliers = self._supplier_repository.get_all_by_id()

        resolved_item = self._sourcing_rule.resolve(
            parsed_request=request.parsed_data,
            catalog_items=catalog_items,
            suppliers=suppliers,
        )

        # Money deliberately does not implement __mul__ (kept minimal), so
        # the line-item total is computed explicitly here.
        total_amount = Money(
            amount=resolved_item.unit_price.amount * request.parsed_data.quantity,
            currency=resolved_item.unit_price.currency,
        )

        request.mark_resolved(
            sku=resolved_item.sku,
            supplier_id=resolved_item.supplier_id,
            amount=total_amount,
            stock_check="PASSED",  # the Sourcing Funnel already filtered on stock_qty
        )
        self._procurement_repository.save(request)
        return request
