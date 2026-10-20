"""Seeds the database with the same demo data used by demo.py / the
in-memory repositories, so the deployed API has something to query.
Idempotent: does nothing if suppliers already exist.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from procurement.infrastructure.models import (
    CatalogItemModel,
    CostCenterModel,
    SupplierModel,
    UserModel,
)
from procurement.infrastructure.seed_data import build_seed_data


def seed_database(session: Session) -> None:
    if session.query(SupplierModel).first() is not None:
        return  # already seeded

    suppliers, catalog_items, cost_centers, users = build_seed_data()

    for s in suppliers:
        session.add(SupplierModel(id=s.id, name=s.name, approved=s.approved))

    for c in catalog_items:
        session.add(
            CatalogItemModel(
                id=c.id,
                sku=c.sku.value,
                product_name=c.product_name,
                category=c.category,
                supplier_id=c.supplier_id,
                unit_price=c.unit_price.amount,
                currency=c.unit_price.currency,
                stock_qty=c.stock_qty,
                lead_time_days=c.lead_time_days,
            )
        )

    for cc in cost_centers:
        session.add(
            CostCenterModel(
                id=cc.id,
                name=cc.name,
                budget_total=cc.budget_total.amount,
                budget_spent=cc.budget_spent.amount,
                currency=cc.budget_total.currency,
            )
        )

    for u in users:
        session.add(UserModel(id=u.id, name=u.name, email=u.email, role=u.role.value))

    session.commit()
