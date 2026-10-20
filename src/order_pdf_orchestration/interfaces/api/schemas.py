"""Pydantic DTOs of the OPO API. camelCase mirrors application/contract.py."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SupplierOut(BaseModel):
    id: str
    name: str
    contactReference: str


class UploadSupplierOfferIn(BaseModel):
    supplierId: str
    rawText: str = Field(..., min_length=1)


class SupplierOfferOut(BaseModel):
    offerId: str
    supplierId: str
    rawText: str


class GenerateOrderRequestIn(BaseModel):
    supplierOfferId: str
    promptText: str = Field(..., min_length=1)


class LineItemIn(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    unitPrice: float = Field(..., ge=0)
    currency: str = Field("CHF", pattern=r"^[A-Z]{3}$")


class ReviseLineItemsIn(BaseModel):
    lineItems: list[LineItemIn] = Field(..., min_length=1)


class LineItemOut(BaseModel):
    id: str
    description: str
    quantity: int
    unitPrice: float
    lineTotal: float
    currency: str


class TotalOut(BaseModel):
    amount: float
    currency: str


class ValidationOut(BaseModel):
    notes: list[str]


class WorkflowOut(BaseModel):
    currentState: str
    nextState: str | None
    history: list[str]


class OrderRequestOut(BaseModel):
    orderRequestId: str
    status: str
    supplierOfferId: str
    promptText: str
    lineItems: list[LineItemOut]
    total: TotalOut | None
    validation: ValidationOut
    pdfReference: str | None
    supplierReference: str | None
    workflow: WorkflowOut
