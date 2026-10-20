"""Shared fixtures for integration AND e2e tests: a real SQLAlchemy
engine/session against Postgres (see DATABASE_URL / docker-compose.yml),
with each test isolated via the standard SAVEPOINT-rollback pattern --
necessary because our repositories call session.commit() internally (see
docs/adr/ADR-003), which would otherwise leak state between tests.

Requires a running Postgres: `docker compose up -d db` (or set DATABASE_URL
to point at your own instance, e.g. a Neon connection string) before running
`pytest tests/integration` or `pytest tests/e2e`.
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from procurement.infrastructure.models import Base

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg2://procurement:procurement@localhost:5432/procurement"
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    outer_transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient wired to the same isolated, rolled-back db_session
    used by integration tests, via dependency_overrides -- the standard
    FastAPI pattern for e2e-testing without touching real persisted state."""
    from fastapi.testclient import TestClient

    from procurement.infrastructure.main import create_app
    from procurement.infrastructure.repositories.sqlalchemy_approval_repository import (
        SqlAlchemyApprovalRepository,
    )
    from procurement.infrastructure.repositories.sqlalchemy_catalog_item_repository import (
        SqlAlchemyCatalogItemRepository,
    )
    from procurement.infrastructure.repositories.sqlalchemy_cost_center_repository import (
        SqlAlchemyCostCenterRepository,
    )
    from procurement.infrastructure.repositories.sqlalchemy_procurement_request_repository import (
        SqlAlchemyProcurementRequestRepository,
    )
    from procurement.infrastructure.repositories.sqlalchemy_supplier_repository import (
        SqlAlchemySupplierRepository,
    )
    from procurement.infrastructure.repositories.sqlalchemy_user_repository import (
        SqlAlchemyUserRepository,
    )
    from procurement.infrastructure.seed_db import seed_database
    from procurement.interfaces.api.dependencies import (
        get_approval_repository,
        get_catalog_repository,
        get_cost_center_repository,
        get_procurement_repository,
        get_supplier_repository,
        get_user_repository,
    )

    seed_database(db_session)  # no-op if already seeded in this transaction

    # init_db=False: the engine fixture already created the schema and the
    # seed above ran inside this test's rolled-back transaction. Letting the
    # app seed at startup too would open a second connection that blocks on
    # this transaction's uncommitted rows (a cross-connection deadlock).
    # All endpoint repositories are redirected to db_session below, so
    # requests/approvals created during a test never persist beyond it.
    app = create_app(init_db=False)
    app.dependency_overrides[get_procurement_repository] = lambda: SqlAlchemyProcurementRequestRepository(db_session)
    app.dependency_overrides[get_catalog_repository] = lambda: SqlAlchemyCatalogItemRepository(db_session)
    app.dependency_overrides[get_supplier_repository] = lambda: SqlAlchemySupplierRepository(db_session)
    app.dependency_overrides[get_cost_center_repository] = lambda: SqlAlchemyCostCenterRepository(db_session)
    app.dependency_overrides[get_user_repository] = lambda: SqlAlchemyUserRepository(db_session)
    app.dependency_overrides[get_approval_repository] = lambda: SqlAlchemyApprovalRepository(db_session)

    with TestClient(app) as test_client:
        yield test_client
