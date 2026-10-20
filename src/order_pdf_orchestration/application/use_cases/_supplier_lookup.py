from __future__ import annotations

from order_pdf_orchestration.application.ports.repositories import (
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.domain.entities import OrderRequest, Supplier
from order_pdf_orchestration.domain.exceptions import (
    UnknownSupplierError,
    UnknownSupplierOfferError,
)


def supplier_of(
    order: OrderRequest, offers: SupplierOfferRepository, suppliers: SupplierRepository
) -> Supplier:
    offer = offers.get_by_id(order.supplier_offer_id)
    if offer is None:
        raise UnknownSupplierOfferError(f"Supplier offer {order.supplier_offer_id} does not exist.")
    supplier = suppliers.get_by_id(offer.supplier_id)
    if supplier is None:
        raise UnknownSupplierError(f"Supplier {offer.supplier_id} does not exist.")
    return supplier
