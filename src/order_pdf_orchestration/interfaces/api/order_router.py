"""HTTP endpoints of the Order PDF Orchestration context.

Concrete adapters arrive through FastAPI `Depends` (interfaces/api/dependencies.py);
routes only build use cases and translate errors to status codes.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from order_pdf_orchestration.application.contract import offer_to_contract, to_contract
from order_pdf_orchestration.application.ports.document_renderer import DocumentRenderer
from order_pdf_orchestration.application.ports.order_generation_agent import (
    OrderGenerationAgent,
    OrderGenerationError,
)
from order_pdf_orchestration.application.ports.repositories import (
    OrderRequestRepository,
    SupplierOfferRepository,
    SupplierRepository,
)
from order_pdf_orchestration.application.ports.supplier_gateway import (
    SupplierGateway,
    SupplierGatewayError,
)
from order_pdf_orchestration.application.use_cases.generate_order_request import (
    GenerateOrderRequestUseCase,
)
from order_pdf_orchestration.application.use_cases.render_order_pdf import RenderOrderPdfUseCase
from order_pdf_orchestration.application.use_cases.revise_order_line_items import (
    ReviseOrderLineItemsUseCase,
)
from order_pdf_orchestration.application.use_cases.send_order_to_supplier import (
    SendOrderToSupplierUseCase,
)
from order_pdf_orchestration.application.use_cases.upload_supplier_offer import (
    UploadSupplierOfferUseCase,
)
from order_pdf_orchestration.application.use_cases.validate_order_request import (
    ValidateOrderRequestUseCase,
)
from order_pdf_orchestration.domain.entities import OrderLineItem, OrderRequest, SupplierOffer
from order_pdf_orchestration.domain.exceptions import DomainError
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.interfaces.api.dependencies import (
    get_document_renderer,
    get_offer_repository,
    get_order_generation_agent,
    get_order_repository,
    get_supplier_gateway,
    get_supplier_repository,
)
from order_pdf_orchestration.interfaces.api.schemas import (
    GenerateOrderRequestIn,
    OrderRequestOut,
    ReviseLineItemsIn,
    SupplierOfferOut,
    SupplierOut,
    UploadSupplierOfferIn,
)

router = APIRouter(tags=["order-pdf-orchestration"])


def _run(action):
    try:
        return action()
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OrderGenerationError, SupplierGatewayError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _out(order: OrderRequest) -> OrderRequestOut:
    return OrderRequestOut(**to_contract(order))


def _order_or_404(orders: OrderRequestRepository, order_id: str) -> OrderRequest:
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="OrderRequest not found.")
    return order


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(
    suppliers: SupplierRepository = Depends(get_supplier_repository),
) -> list[SupplierOut]:
    return [SupplierOut(id=s.id, name=s.name, contactReference=s.contact_reference) for s in suppliers.list_all()]


@router.post("/supplier-offers", response_model=SupplierOfferOut, status_code=201)
def upload_supplier_offer(
    payload: UploadSupplierOfferIn,
    suppliers: SupplierRepository = Depends(get_supplier_repository),
    offers: SupplierOfferRepository = Depends(get_offer_repository),
) -> SupplierOfferOut:
    use_case = UploadSupplierOfferUseCase(supplier_repository=suppliers, offer_repository=offers)

    def upload() -> SupplierOffer:
        offer = SupplierOffer(id=str(uuid.uuid4()), supplier_id=payload.supplierId, raw_text=payload.rawText)
        use_case.execute(offer)
        return offer

    return SupplierOfferOut(**offer_to_contract(_run(upload)))


@router.get("/supplier-offers/{offer_id}", response_model=SupplierOfferOut)
def get_supplier_offer(
    offer_id: str, offers: SupplierOfferRepository = Depends(get_offer_repository)
) -> SupplierOfferOut:
    offer = offers.get_by_id(offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="SupplierOffer not found.")
    return SupplierOfferOut(**offer_to_contract(offer))


@router.post("/order-requests", response_model=OrderRequestOut, status_code=201)
def generate_order_request(
    payload: GenerateOrderRequestIn,
    offers: SupplierOfferRepository = Depends(get_offer_repository),
    orders: OrderRequestRepository = Depends(get_order_repository),
    agent: OrderGenerationAgent = Depends(get_order_generation_agent),
) -> OrderRequestOut:
    order = OrderRequest(id=str(uuid.uuid4()), supplier_offer_id=payload.supplierOfferId, prompt_text=payload.promptText)
    use_case = GenerateOrderRequestUseCase(agent=agent, offer_repository=offers, order_repository=orders)
    return _out(_run(lambda: use_case.execute(order)))


@router.get("/order-requests/{order_id}", response_model=OrderRequestOut)
def get_order_request(
    order_id: str, orders: OrderRequestRepository = Depends(get_order_repository)
) -> OrderRequestOut:
    return _out(_order_or_404(orders, order_id))


@router.post("/order-requests/{order_id}/validate", response_model=OrderRequestOut)
def validate_order_request(
    order_id: str,
    offers: SupplierOfferRepository = Depends(get_offer_repository),
    orders: OrderRequestRepository = Depends(get_order_repository),
) -> OrderRequestOut:
    order = _order_or_404(orders, order_id)
    use_case = ValidateOrderRequestUseCase(offer_repository=offers, order_repository=orders)
    return _out(_run(lambda: use_case.execute(order)))


@router.put("/order-requests/{order_id}/line-items", response_model=OrderRequestOut)
def revise_order_line_items(
    order_id: str,
    payload: ReviseLineItemsIn,
    orders: OrderRequestRepository = Depends(get_order_repository),
) -> OrderRequestOut:
    order = _order_or_404(orders, order_id)
    use_case = ReviseOrderLineItemsUseCase(order_repository=orders)

    def revise() -> OrderRequest:
        line_items = [
            OrderLineItem(
                id=f"LI-{number}",
                description=item.description,
                quantity=item.quantity,
                unit_price=Money(Decimal(str(item.unitPrice)), item.currency),
            )
            for number, item in enumerate(payload.lineItems, start=1)
        ]
        return use_case.execute(order, line_items)

    return _out(_run(revise))


@router.post("/order-requests/{order_id}/pdf", response_model=OrderRequestOut)
def render_order_pdf(
    order_id: str,
    suppliers: SupplierRepository = Depends(get_supplier_repository),
    offers: SupplierOfferRepository = Depends(get_offer_repository),
    orders: OrderRequestRepository = Depends(get_order_repository),
    renderer: DocumentRenderer = Depends(get_document_renderer),
) -> OrderRequestOut:
    order = _order_or_404(orders, order_id)
    use_case = RenderOrderPdfUseCase(
        renderer=renderer, supplier_repository=suppliers, offer_repository=offers, order_repository=orders
    )
    return _out(_run(lambda: use_case.execute(order)))


@router.get("/order-requests/{order_id}/pdf")
def download_order_pdf(
    order_id: str,
    orders: OrderRequestRepository = Depends(get_order_repository),
    renderer: DocumentRenderer = Depends(get_document_renderer),
) -> Response:
    order = _order_or_404(orders, order_id)
    if order.pdf_reference is None:
        raise HTTPException(status_code=404, detail="No PDF has been rendered for this OrderRequest.")
    return Response(
        content=renderer.read(order.pdf_reference),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{order.pdf_reference}"'},
    )


@router.post("/order-requests/{order_id}/send", response_model=OrderRequestOut)
def send_order_to_supplier(
    order_id: str,
    suppliers: SupplierRepository = Depends(get_supplier_repository),
    offers: SupplierOfferRepository = Depends(get_offer_repository),
    orders: OrderRequestRepository = Depends(get_order_repository),
    gateway: SupplierGateway = Depends(get_supplier_gateway),
) -> OrderRequestOut:
    order = _order_or_404(orders, order_id)
    use_case = SendOrderToSupplierUseCase(
        gateway=gateway, supplier_repository=suppliers, offer_repository=offers, order_repository=orders
    )
    return _out(_run(lambda: use_case.execute(order)))
