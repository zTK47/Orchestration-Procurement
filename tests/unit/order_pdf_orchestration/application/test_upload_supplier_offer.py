"""OPO-UC-001 - see docs/specs/OPO-UC-001-upload-supplier-offer.md"""
import pytest

from order_pdf_orchestration.application.use_cases.upload_supplier_offer import (
    UploadSupplierOfferUseCase,
)
from order_pdf_orchestration.domain.entities import Supplier, SupplierOffer
from order_pdf_orchestration.domain.exceptions import (
    InvalidSupplierOfferError,
    UnknownSupplierError,
)
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemorySupplierOfferRepository,
    InMemorySupplierRepository,
)


def use_case(offers: InMemorySupplierOfferRepository) -> UploadSupplierOfferUseCase:
    suppliers = InMemorySupplierRepository([Supplier("SUP-1", "Office Tech AG", "orders@officetech.example")])
    return UploadSupplierOfferUseCase(supplier_repository=suppliers, offer_repository=offers)


def test_upload_stores_the_offer_and_returns_its_id():
    offers = InMemorySupplierOfferRepository()
    offer = SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="Dell Latitude 5440 - CHF 1250")

    offer_id = use_case(offers).execute(offer)

    assert offer_id == "OF-1"
    assert offers.get_by_id("OF-1") == offer


def test_upload_for_an_unknown_supplier_is_refused_and_nothing_is_stored():
    offers = InMemorySupplierOfferRepository()

    with pytest.raises(UnknownSupplierError):
        use_case(offers).execute(SupplierOffer(id="OF-1", supplier_id="SUP-404", raw_text="x"))

    assert offers.get_by_id("OF-1") is None


@pytest.mark.parametrize("raw_text", ["", "   \n"])
def test_an_offer_needs_non_blank_text(raw_text):
    with pytest.raises(InvalidSupplierOfferError):
        SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text=raw_text)
