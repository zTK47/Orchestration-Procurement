"""OPO-UC-001 - see docs/specs/OPO-UC-001-upload-supplier-offer.md"""
from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import (
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.domain.entities import SupplierOffer
from order_pdf_orchestration.domain.exceptions import UnknownSupplierError


class UploadSupplierOfferUseCase:
    def __init__(
        self, supplier_repository: SupplierRepository, offer_repository: SupplierOfferRepository
    ) -> None:
        self._suppliers = supplier_repository
        self._offers = offer_repository

    def execute(self, offer: SupplierOffer) -> str:
        if self._suppliers.get_by_id(offer.supplier_id) is None:
            raise UnknownSupplierError(f"Supplier {offer.supplier_id} does not exist.")
        self._offers.save(offer)
        return offer.id
