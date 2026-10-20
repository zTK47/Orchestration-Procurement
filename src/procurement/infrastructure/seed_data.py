"""In-memory seed data shared by the FastAPI app (main.py) and the CLI demo
script (demo.py). Deliberately has zero third-party dependencies so it can
be imported even in environments without FastAPI/SQLAlchemy installed."""
from __future__ import annotations

from decimal import Decimal

from procurement.domain.entities import CatalogItem, CostCenter, Supplier, User, UserRole
from procurement.domain.value_objects import SKU, Money


def build_seed_data() -> tuple[list[Supplier], list[CatalogItem], list[CostCenter], list[User]]:
    suppliers = [
        Supplier(id="SUP-001", name="TechDistrib AG", approved=True),
        Supplier(id="SUP-002", name="UnverifiedSupplier Ltd", approved=False),
    ]
    catalog_items = [
        CatalogItem(
            id="CAT-001",
            sku=SKU("LEN-T14-G3"),
            product_name="Lenovo Laptop",
            category="Laptop",
            supplier_id="SUP-001",
            unit_price=Money(Decimal("1200.00"), "CHF"),
            stock_qty=20,
            lead_time_days=5,
        ),
        CatalogItem(
            id="CAT-002",
            sku=SKU("HP-X360"),
            product_name="HP Laptop",
            category="Laptop",
            supplier_id="SUP-002",  # not approved -> filtered out by the Sourcing Funnel
            unit_price=Money(Decimal("900.00"), "CHF"),
            stock_qty=20,
            lead_time_days=3,
        ),
    ]
    cost_centers = [
        CostCenter(
            id="CC-IT",
            name="IT Department",
            budget_total=Money(Decimal("50000.00"), "CHF"),
            budget_spent=Money(Decimal("0.00"), "CHF"),
        ),
    ]
    users = [
        User(id="U-REQ-1", name="Alice Requester", email="alice@example.com", role=UserRole.REQUESTER),
        User(id="U-MAN-1", name="Bob Manager", email="bob@example.com", role=UserRole.MANAGER),
        User(id="U-BO-1", name="Carla BudgetOwner", email="carla@example.com", role=UserRole.BUDGET_OWNER),
    ]
    return suppliers, catalog_items, cost_centers, users
