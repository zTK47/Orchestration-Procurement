"""SQLAlchemy ORM models mirroring the domain entities.

Status: scaffolded for Phase 4 (Validate/Deploy). These models are the
persistence representation only -- they must never be imported by the
domain or application layers (Dependency Rule). Once wired, the
Sqlalchemy*Repository classes will translate between these ORM rows and the
pure-Python domain entities in domain/entities.py.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String, nullable=False)


class CostCenterModel(Base):
    __tablename__ = "cost_centers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    budget_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    budget_spent: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")


class SupplierModel(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CatalogItemModel(Base):
    __tablename__ = "catalog_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sku: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CHF")
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Declared so the unit of work flushes the parent row first when both are
    # added in one session; a bare ForeignKey column does not order INSERTs.
    supplier: Mapped[SupplierModel] = relationship()


class ProcurementRequestModel(Base):
    __tablename__ = "procurement_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    cost_center_id: Mapped[str] = mapped_column(ForeignKey("cost_centers.id"), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="CREATED")

    # ParsedRequest (flattened -- simplest mapping for this prototype; a
    # separate ParsedRequestModel table would be the next refinement)
    parsed_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_product_name: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_category: Mapped[str | None] = mapped_column(String, nullable=True)
    parsed_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)

    resolved_sku: Mapped[str | None] = mapped_column(String, nullable=True)
    resolved_supplier_id: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    stock_check: Mapped[str | None] = mapped_column(String, nullable=True)
    budget_check: Mapped[str | None] = mapped_column(String, nullable=True)

    # Comma-separated for simplicity in this prototype (e.g. "MANAGER,BUDGET_OWNER").
    required_approval_levels: Mapped[str | None] = mapped_column(String, nullable=True)
    history: Mapped[str | None] = mapped_column(String, nullable=True)
    erp_reference: Mapped[str | None] = mapped_column(String, nullable=True)

    requester: Mapped[UserModel] = relationship()
    cost_center: Mapped[CostCenterModel] = relationship()


class ApprovalModel(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    procurement_request_id: Mapped[str] = mapped_column(
        ForeignKey("procurement_requests.id"), nullable=False
    )
    approver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    procurement_request: Mapped[ProcurementRequestModel] = relationship()
    approver: Mapped[UserModel] = relationship()
