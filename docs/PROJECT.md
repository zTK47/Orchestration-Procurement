# PROJECT.md

Complete this document during **BOOTSTRAP**. Keep it concise and specific to
the project created from this template.

## Purpose

- Project name: Procurement Orchestrator
- User or organisational problem: purchase needs arrive as free text, catalog
  selections or supplier offers and are turned into orders by hand. Sourcing,
  budget, approval and the ERP/supplier hand-off are applied inconsistently.
- Intended users: requesters (employees), approvers (manager, budget owner),
  buyers who order from a supplier offer.
- In scope: free-text and catalog intake, sourcing, budget validation,
  threshold-based approval, ERP hand-off, goods receipt; order generation from a
  supplier offer with PDF and supplier hand-off. LLM, ERP, PDF and supplier are
  offline mocks behind ports.
- Out of scope: OCI Punchout (ADR-005), a real LLM via LiteLLM, a real SAP
  adapter, a configurable price-tie strategy, partial stock and backorders.

Course: FHNW BSc Business Information Technology, *AI-assisted Software
Development*, capstone project. Design input: `docs/design-sketches/`.

## Architecture

Clean Architecture, dependencies point inward:

`domain ← application ← interfaces ← infrastructure`

| Layer | Contents | Validated by |
|---|---|---|
| `domain/` | Entities, value objects, domain services, domain errors. Pure Python. | Unit tests |
| `application/` | Use cases, ports (repositories, LLM, ERP, renderer, supplier), JSON contract builder. | Unit tests |
| `interfaces/` | FastAPI routers, Pydantic DTOs, `Depends` wiring, static frontend. | Integration + e2e tests |
| `infrastructure/` | SQLAlchemy models and repositories, mock adapters, in-memory repositories, seed data, app startup. | Integration + e2e tests |

Constraints:
- `domain/` and `application/` never import FastAPI, Pydantic or SQLAlchemy
  (guarded by `tests/unit/order_pdf_orchestration/test_dependency_rule.py`).
- Every LLM, ERP, PDF or supplier call goes through a port in `application/ports/`.
- Concrete adapters are chosen in `interfaces/api/dependencies.py`.

Decisions: `docs/adr/` ADR-001 … ADR-008 (all Proposed).

### Bounded context 1: Procurement (`src/procurement`)

Entities: `User`, `CostCenter`, `Supplier`, `CatalogItem`, `ProcurementRequest`
(aggregate root), `Approval`. Value objects: `Money`, `SKU`, `ParsedRequest`.
Domain services: `SourcingRule` (Sourcing Funnel), `ApprovalRoutingPolicy`.

Business rules:
1. Approval routing: amount ≤ 1000 no approval; > 1000 `MANAGER`; > 10000 also `BUDGET_OWNER`.
2. Budget is checked when validating and again, authoritatively, right before it is spent.
3. Sourcing Funnel: approved supplier, enough stock, lead time ≤ 14 days, cheapest wins;
   a price tie raises `RequiresClarificationError` (ADR-002).
4. `REJECTED` and `COMPLETED` are terminal; an approved request cannot be re-decided.
5. The same approver cannot decide twice at the same level.
6. An order can only be sent to the ERP after approval; goods receipt only after the order was sent.

```
CREATED → PARSED → RESOLVED → VALIDATED → PENDING_APPROVAL → APPROVED
   → ORDER_SENT → GOODS_RECEIPT → COMPLETED
VALIDATED → APPROVED (no approval required)      PENDING_APPROVAL → REJECTED
```

| Use case | Transition |
|---|---|
| UC-001 Parse Request | CREATED → PARSED |
| UC-002 Resolve Item | PARSED → RESOLVED |
| UC-005 Submit Catalog Selection | CREATED → RESOLVED (via a synthetic PARSED step) |
| UC-003 Validate Request | RESOLVED → VALIDATED |
| UC-004 Create Order | VALIDATED → PENDING_APPROVAL or APPROVED |
| UC-006 Record Approval Decision | PENDING_APPROVAL → APPROVED or REJECTED |
| UC-007 Send Order To ERP | APPROVED → ORDER_SENT |
| UC-008 Record Goods Receipt | ORDER_SENT → GOODS_RECEIPT |
| UC-009 Complete Request | GOODS_RECEIPT → COMPLETED |

API contract: every endpoint returns the pipeline JSON from the catalog sketch:
`requestId`, `status`, `rawText`, `parsedData`, `resolvedData`, `validation`,
`workflow` (`currentState`, `nextState`, `history`). Additions:
`resolvedData.totalAmount`, `validation.approvalLevels` (`approvalLevel` is the
highest required level) and `erpReference`. `requiresApproval` is `null` until
UC-004 has decided it.

### Bounded context 2: Order PDF Orchestration (`src/order_pdf_orchestration`)

Source: the sketch "Free Text Order Orchestration". A buyer pastes a supplier
offer and writes a free-text order prompt; an agent (ADR-007) turns it into an
`OrderRequest` with line items; business rules validate it, with a human
fallback; a PDF is rendered and the order is sent to the supplier.

Kept separate from `src/procurement`: different language and lifecycle and its
own app, so neither context can break the other's tests. Nothing under
`src/procurement` is imported; `Money` is re-implemented locally on purpose.

```
DRAFT → GENERATED → VALIDATED → SENT (terminal)
GENERATED → NEEDS_CLARIFICATION → GENERATED (human revises line items, OPO-UC-006)
```

| Use case | Transition |
|---|---|
| OPO-UC-001 Upload Supplier Offer | — (stores the offer) |
| OPO-UC-002 Generate Order Request | DRAFT → GENERATED |
| OPO-UC-003 Validate Order Request | GENERATED → VALIDATED or NEEDS_CLARIFICATION |
| OPO-UC-006 Revise Order Line Items | NEEDS_CLARIFICATION → GENERATED |
| OPO-UC-004 Render Order PDF | VALIDATED (sets `pdf_reference`) |
| OPO-UC-005 Send Order To Supplier | VALIDATED (with PDF) → SENT |

Business rules: at least one line item to validate; every line item must match
the offer text (else `NEEDS_CLARIFICATION`, never auto-approved); quantity > 0,
unit price ≥ 0; total = Σ quantity × unit price; send only when `VALIDATED` and
the PDF exists; `SENT` is terminal.

Adapters (offline, deterministic mocks, as in ADR-004): `MockOrderGenerationAgent`
(output schema-checked with Pydantic, ADR-008), `MockDocumentRenderer` (fpdf2:
pure Python, no system packages, LGPL-3.0 used unmodified), `MockSupplierGateway`,
in-memory repositories.

## Structure

```
src/procurement/{domain,application,interfaces,infrastructure}/
src/order_pdf_orchestration/{domain,application,interfaces,infrastructure}/
tests/{unit,integration,e2e}/
docs/{PROJECT.md,TASKS.md,LEARNINGS.md,specs/,adr/,design-sketches/}
demo.py                      # procurement pipeline in memory, no install needed
Dockerfile, docker-compose.yml
```

Template artefacts (`AGENTS.md`, `skills/`, `scripts/`, `.devcontainer/`,
`environments/python/`, `.github/`) are kept as delivered by the template.

## Commands

| Activity | Command |
|---|---|
| Install | `bash scripts/setup-python.sh && .venv/bin/pip install -e ".[dev]"` |
| Lint | `ruff check src tests` |
| Unit tests | `pytest tests/unit` |
| Integration tests | `docker compose up -d db && pytest tests/integration` |
| E2E tests | `pytest tests/e2e` (Postgres for the procurement context) |
| Run locally | `uvicorn procurement.infrastructure.main:app --reload` (UI on `/`, Swagger on `/docs`) |
| Run OPO app | `uvicorn order_pdf_orchestration.infrastructure.main:app --reload --port 8001` |
| Demo without install | `python demo.py` |
| Build/release | `docker build -t procurement-orchestrator .`; tag `v*` runs `.github/workflows/release.yml` |
| Agent skills | `bash scripts/setup-skills.sh claude` |

Tests use `DATABASE_URL`, default
`postgresql+psycopg2://procurement:procurement@localhost:5432/procurement`.

## Dependencies

- Manifest: `pyproject.toml`; `requirements.txt` mirrors it.
- Runtime: Python 3.12 (`.python-version`), FastAPI, Uvicorn, Pydantic v2,
  SQLAlchemy 2, psycopg2, fpdf2. Dev: pytest, httpx, ruff.
- Database: PostgreSQL 16 locally and in CI.
- Configuration: `DATABASE_URL`. Never commit credentials; production secrets
  live in GitHub Secrets / the hosting platform only.
- Deployment platform: not configured yet (`.github/workflows/cd.yml` is the
  inactive template, phase 5).
