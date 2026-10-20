# Procurement Orchestrator

A **FastAPI** application that turns a purchase need, written as free text or
picked from a catalog, into a validated, approved purchase order handed off to
the ERP. It follows **Clean Architecture**, is built with **TDD** and stores its
data in **PostgreSQL** through SQLAlchemy.

This is the capstone project of the *AI-assisted Software Development* module
(FHNW). It starts from the [AI-SDLC template](https://github.com/AIaSDev/ai-sdlc-template)
and uses [BAIssue](https://github.com/AIaSDev/BAIssue) as its reference. The method
is described in the [AI-SDLC documentation](https://docs.aisl.science/learning-and-resources/ai-sdlc).

## Capstone requirements

| Requirement | Where |
|---|---|
| Enterprise architecture (Domain / Application / Interfaces / Infrastructure) | `src/*/{domain,application,interfaces,infrastructure}`, [ADR-001](docs/adr/ADR-001-clean-architecture.md) |
| Business logic separated from framework code | `domain/` and `application/` import no FastAPI, Pydantic or SQLAlchemy; for the OPO context `tests/unit/order_pdf_orchestration/test_dependency_rule.py` checks this |
| Spec-Driven Development and AGENTS.md | [AGENTS.md](AGENTS.md), `skills/`, `docs/specs/` (15 use cases), `docs/TASKS.md` |
| At least five entities | `User`, `CostCenter`, `Supplier`, `CatalogItem`, `ProcurementRequest`, `Approval` |
| At least two use cases as services | 9 use cases in `src/procurement/application/use_cases/`, 6 more in `src/order_pdf_orchestration/` |
| Relational database with ORM | PostgreSQL + SQLAlchemy 2 (`src/procurement/infrastructure/models.py`, `repositories/`) |
| TDD | unit, integration and e2e tests; red → green log in [docs/TASKS.md](docs/TASKS.md) |
| CI/CD | `.github/workflows/` (see [CI, releases and CD](#ci-releases-and-cd)) |
| Use of a coding agent | [AGENTS.md](AGENTS.md), [Agents and MCP](#agents-and-mcp), [docs/LEARNINGS.md](docs/LEARNINGS.md) |

## What it does

The project has two bounded contexts, based on the team's two sketches in
[docs/design-sketches](docs/design-sketches/README.md).

**Procurement** (`src/procurement`), from the "Catalog Order Logic" sketch:

```
CREATED → PARSED → RESOLVED → VALIDATED → PENDING_APPROVAL → APPROVED
   → ORDER_SENT → GOODS_RECEIPT → COMPLETED
```

- **Sourcing:** picks the approved supplier with enough stock, delivery within
  14 days and the lowest price. On a price tie it asks for clarification instead
  of choosing on its own ([ADR-002](docs/adr/ADR-002-price-tie-requires-clarification.md)).
- **Budget:** checked against the cost center during validation, and again
  right before the money is spent.
- **Approval:** above 1000 CHF the `MANAGER` must approve, above 10000 CHF the
  `BUDGET_OWNER` as well.

**Order PDF Orchestration** (`src/order_pdf_orchestration`), from the "Free Text Order Orchestration" sketch:

```
DRAFT → GENERATED → VALIDATED → SENT
GENERATED → NEEDS_CLARIFICATION → GENERATED (human revision)
```

- **Generation:** from the supplier offer and the prompt, an agent generates the
  `OrderRequest` ([ADR-007](docs/adr/ADR-007-order-generation-is-llm-agent-based.md));
  Pydantic checks the agent's output
  ([ADR-008](docs/adr/ADR-008-pydantic-validates-llm-output-at-the-boundary.md)).
- **Validation:** business rules validate the order and ask a person to revise
  it when something does not match.
- **Sending:** a PDF is rendered and the order is sent to the supplier.

LLM, ERP, PDF renderer and supplier are offline, deterministic **mock** adapters
behind ports in `application/ports/`
([ADR-004](docs/adr/ADR-004-llm-as-mocked-adapter.md)). A real adapter replaces a
mock in one place, `interfaces/api/dependencies.py`.

## Architecture

Dependencies point inward: `domain ← application ← interfaces ← infrastructure`.

```
src/procurement/
├── domain/                 # entities, value objects (Money, SKU), SourcingRule, ApprovalRoutingPolicy
├── application/
│   ├── ports/              # repositories, LLMAdapter, ErpGateway
│   ├── use_cases/          # UC-001 … UC-009
│   └── contract.py         # pipeline JSON
├── interfaces/
│   ├── api/                # FastAPI router, Pydantic DTOs, Depends wiring
│   └── static/index.html   # minimal UI
└── infrastructure/         # SQLAlchemy models and repositories, mocks, seed, main.py
src/order_pdf_orchestration/  # same structure, separate app
```

- **Domain** and **application** are plain Python.
- **Interfaces** translates HTTP ↔ use cases and chooses the adapters.
- **Infrastructure** holds the database, the adapters and app startup.

Details: [docs/PROJECT.md](docs/PROJECT.md). Decisions:

| ADR | Decision |
|---|---|
| [001](docs/adr/ADR-001-clean-architecture.md) | Clean Architecture with four layers |
| [002](docs/adr/ADR-002-price-tie-requires-clarification.md) | Price tie → human clarification |
| [003](docs/adr/ADR-003-dependency-injection-via-ports.md) | Use cases depend on ports; adapters are injected |
| [004](docs/adr/ADR-004-llm-as-mocked-adapter.md) | LLM behind a mockable port |
| [005](docs/adr/ADR-005-oci-punchout-out-of-scope.md) | OCI Punchout out of scope |
| [006](docs/adr/ADR-006-erp-behind-a-gateway-port.md) | ERP behind `ErpGateway` |
| [007](docs/adr/ADR-007-order-generation-is-llm-agent-based.md) | Order generation is agent-based, behind a port |
| [008](docs/adr/ADR-008-pydantic-validates-llm-output-at-the-boundary.md) | Pydantic validates the agent's output at the boundary |

All ADRs stay **Proposed** until the team accepts them.

## UI and API

| App | Path | Purpose |
|---|---|---|
| Procurement | `/` | minimal UI |
| | `/docs` | Swagger / OpenAPI |
| | `/health` | health check |
| Order PDF Orchestration | `/` | demo UI |
| | `/docs` | Swagger / OpenAPI |

Procurement endpoints (`/procurement-requests`):

- `POST /procurement-requests`: create a request from free text and parse it (UC-001)
- `POST /procurement-requests/from-catalog`: create a request from the catalog (UC-005)
- `POST /procurement-requests/{id}/resolve`: sourcing (UC-002)
- `POST /procurement-requests/{id}/validate`: budget check (UC-003)
- `POST /procurement-requests/{id}/create-order`: create the order and decide on approval (UC-004)
- `POST /procurement-requests/{id}/approvals`: approval decision (UC-006)
- `POST /procurement-requests/{id}/send-order`: hand-off to the ERP (UC-007)
- `POST /procurement-requests/{id}/goods-receipt`: goods receipt (UC-008)
- `POST /procurement-requests/{id}/complete`: close the request (UC-009)
- `GET /procurement-requests/{id}`: current state

Every response uses the JSON from the sketch: `requestId`, `status`,
`parsedData`, `resolvedData`, `validation`, `workflow`.

## Configuration

The only environment variable is `DATABASE_URL`, for example
`postgresql+psycopg2://user:password@host:5432/procurement`. Credentials never go
into code: locally they live in `.env`, which `.gitignore` already excludes; in
CI and production they live in GitHub Secrets or on the hosting platform.

## Running locally

```bash
bash scripts/setup-python.sh                   # .venv + requirements.txt (template script)
.venv/bin/pip install -e ".[dev]"
docker compose up -d db                        # PostgreSQL 16
uvicorn procurement.infrastructure.main:app --reload
```

- UI: http://localhost:8000/ and API: http://localhost:8000/docs
- OPO app: `uvicorn order_pdf_orchestration.infrastructure.main:app --reload --port 8001`
- Without installing anything: `python demo.py` runs the pipeline in memory up to `COMPLETED`.

## Testing

| Level | What it checks | Command | Count |
|---|---|---|---|
| Unit | domain, application, mock adapters; no database | `pytest tests/unit` | 141 |
| Integration | SQLAlchemy repositories against PostgreSQL | `pytest tests/integration` | 12 |
| E2E | full HTTP stack with `TestClient` | `pytest tests/e2e` | 13 |

Integration and e2e tests read `DATABASE_URL`, which defaults to the Postgres
from `docker-compose.yml`. Lint with `ruff check src tests`.

## Docker

```bash
docker build -t procurement-orchestrator .
docker compose up                              # app + PostgreSQL
```

## CI, releases and CD

The workflows are the AI-SDLC template's, completed for this project.

- **CI** (`.github/workflows/ci.yml`), on push and pull request to `main`:
  AI-SDLC structure → lint + unit tests → integration + e2e on PostgreSQL 16 →
  Docker image build.
- **Release** (`.github/workflows/release.yml`): a `vX.Y.Z` tag checks the
  structure, runs the unit tests and creates the GitHub Release.

  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```

- **CD** (`.github/workflows/cd.yml`): **not active yet**. It is the inactive
  template and waits for `scripts/deploy.sh`, `scripts/smoke-test.sh` and the
  variable `CD_ENABLED=true`. Platform, database and secrets are still to be
  decided with the team (phase 5, [docs/TASKS.md](docs/TASKS.md)).

## Agents and MCP

- **Shared instructions:** [AGENTS.md](AGENTS.md) routes the AI-SDLC phases;
  `skills/ai-sdlc-*` holds the guidance for each phase.
- **Setup:** `bash scripts/setup-skills.sh claude` (or `copilot`, `codex`,
  `all`…) exposes the skills to the agent.
- **Agent and model:** TODO (team). State which agent and which model you used,
  and why: quality, cost, speed, access through the FHNW LiteLLM proxy.

### MCP server

| | |
|---|---|
| **Server** | [GitMCP](https://gitmcp.io) for this repository: `https://gitmcp.io/zTK47/Orchestration-Procurement` |
| **Why** | gives the agent the repository's code and documentation context (README, `docs/`, code search), even outside the local working copy |
| **Permissions** | read-only access to the repository's public content; no token, no writes to GitHub |
| **Configuration** | `.mcp.json` (Claude Code, project scope) and `.vscode/mcp.json` (VS Code); no keys in either file |

Alternatively, from the command line:
`claude mcp add --transport http orchestration-procurement-docs https://gitmcp.io/zTK47/Orchestration-Procurement`.

Claude Code asks for approval before it uses a server defined in `.mcp.json`.
To test it, ask a question such as "Explain how our API layer is structured" and
compare the answer with and without the server. Test result: TODO (team).

## Known limitations

- LLM, ERP, PDF and supplier are mocks: no real calls are made.
- The OPO context keeps its data in memory; PostgreSQL persistence exists only
  in the procurement context.
- Approval levels and history are stored as comma-separated columns, a
  prototype shortcut instead of an audit table.
- OCI Punchout, a real SAP adapter and a configurable price-tie strategy are out
  of scope.

## License

Educational project. `CITATION.cff` and `.zenodo.json` come from the AI-SDLC
template and cite the template itself.
