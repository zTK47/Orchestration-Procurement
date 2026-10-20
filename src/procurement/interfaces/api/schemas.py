"""Pydantic schemas (DTOs). Validation lives only here and in infrastructure.

Field names are camelCase on purpose: they mirror the agreed JSON contract."""
from __future__ import annotations

from pydantic import BaseModel, Field

from procurement.domain.entities import ApprovalDecision, ApprovalLevel


class CreateProcurementRequestIn(BaseModel):
    requesterId: str
    costCenterId: str
    rawText: str = Field(..., min_length=1)


class SubmitCatalogSelectionIn(BaseModel):
    requesterId: str
    costCenterId: str
    sku: str
    quantity: int = Field(..., gt=0)


class RecordApprovalDecisionIn(BaseModel):
    approverId: str
    level: ApprovalLevel
    decision: ApprovalDecision


class ParsedDataOut(BaseModel):
    quantity: int
    productName: str
    category: str
    confidence: float


class ResolvedDataOut(BaseModel):
    sku: str
    supplierId: str
    unitPrice: float
    totalAmount: float
    currency: str


class ValidationOut(BaseModel):
    budgetCheck: str | None
    stockCheck: str | None
    requiresApproval: bool | None
    approvalLevel: str | None
    approvalLevels: list[str]


class WorkflowOut(BaseModel):
    currentState: str
    nextState: str | None
    history: list[str]


class ProcurementRequestOut(BaseModel):
    requestId: str
    status: str
    rawText: str | None
    parsedData: ParsedDataOut | None
    resolvedData: ResolvedDataOut | None
    validation: ValidationOut
    workflow: WorkflowOut
    erpReference: str | None
