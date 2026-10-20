# Procurement Orchestrator

Applicazione **FastAPI** che trasforma una richiesta d'acquisto, scritta in testo
libero oppure scelta da catalogo, in un ordine validato, approvato e passato
all'ERP. Usa la **Clean Architecture**, è sviluppata con **TDD** e salva i dati in
**PostgreSQL** tramite SQLAlchemy.

È il capstone project del modulo *AI-assisted Software Development* (FHNW). Il
progetto parte dall'[AI-SDLC template](https://github.com/AIaSDev/ai-sdlc-template)
e ha come riferimento [BAIssue](https://github.com/AIaSDev/BAIssue). Il metodo è
descritto nella [documentazione AI-SDLC](https://docs.aisl.science/learning-and-resources/ai-sdlc).

## Requisiti del capstone

| Requisito | Dove |
|---|---|
| Architettura enterprise (Domain / Application / Interfaces / Infrastructure) | `src/*/{domain,application,interfaces,infrastructure}`, [ADR-001](docs/adr/ADR-001-clean-architecture.md) |
| Logica di business separata dal framework | `domain/` e `application/` non importano FastAPI, Pydantic o SQLAlchemy; per il contesto OPO lo verifica `tests/unit/order_pdf_orchestration/test_dependency_rule.py` |
| Spec-Driven Development e AGENTS.md | [AGENTS.md](AGENTS.md), `skills/`, `docs/specs/` (15 use case), `docs/TASKS.md` |
| Almeno 5 entità | `User`, `CostCenter`, `Supplier`, `CatalogItem`, `ProcurementRequest`, `Approval` |
| Almeno 2 use case come servizi | 9 use case in `src/procurement/application/use_cases/`, altri 6 in `src/order_pdf_orchestration/` |
| Database relazionale con ORM | PostgreSQL + SQLAlchemy 2 (`src/procurement/infrastructure/models.py`, `repositories/`) |
| TDD | test unit, integration ed e2e; log red → green in [docs/TASKS.md](docs/TASKS.md) |
| CI/CD | `.github/workflows/` (vedi [CI, release e CD](#ci-release-e-cd)) |
| Uso di un coding agent | [AGENTS.md](AGENTS.md), [Agenti e MCP](#agenti-e-mcp), [docs/LEARNINGS.md](docs/LEARNINGS.md) |

## Cosa fa

Il progetto è diviso in due bounded context, che partono dalle due mappe del team
in [docs/design-sketches](docs/design-sketches/README.md).

**Procurement** (`src/procurement`), dalla mappa "Catalog Order Logic":

```
CREATED → PARSED → RESOLVED → VALIDATED → PENDING_APPROVAL → APPROVED
   → ORDER_SENT → GOODS_RECEIPT → COMPLETED
```

- **Sourcing:** sceglie il fornitore approvato con stock sufficiente, consegna
  entro 14 giorni e prezzo più basso. A parità di prezzo chiede un chiarimento
  invece di scegliere da solo ([ADR-002](docs/adr/ADR-002-price-tie-requires-clarification.md)).
- **Budget:** lo controlla sul centro di costo in validazione, e di nuovo
  subito prima della spesa.
- **Approvazione:** oltre 1000 CHF serve il `MANAGER`, oltre 10000 CHF anche il
  `BUDGET_OWNER`.

**Order PDF Orchestration** (`src/order_pdf_orchestration`), dalla mappa "Free Text Order Orchestration":

```
DRAFT → GENERATED → VALIDATED → SENT
GENERATED → NEEDS_CLARIFICATION → GENERATED (revisione umana)
```

- **Generazione:** dall'offerta del fornitore e dal prompt, un agente genera
  l'`OrderRequest` ([ADR-007](docs/adr/ADR-007-order-generation-is-llm-agent-based.md));
  Pydantic controlla l'output dell'agente
  ([ADR-008](docs/adr/ADR-008-pydantic-validates-llm-output-at-the-boundary.md)).
- **Validazione:** le regole di business validano l'ordine e, se qualcosa non
  torna, chiedono la revisione di una persona.
- **Invio:** viene generato un PDF e l'ordine parte verso il fornitore.

LLM, ERP, renderer PDF e fornitore sono adapter **mock**, offline e
deterministici, dietro porte in `application/ports/`
([ADR-004](docs/adr/ADR-004-llm-as-mocked-adapter.md)). Un adapter reale si
sostituisce in un solo punto, `interfaces/api/dependencies.py`.

## Architettura

Le dipendenze puntano verso l'interno: `domain ← application ← interfaces ← infrastructure`.

```
src/procurement/
├── domain/                 # entità, value object (Money, SKU), SourcingRule, ApprovalRoutingPolicy
├── application/
│   ├── ports/              # repository, LLMAdapter, ErpGateway
│   ├── use_cases/          # UC-001 … UC-009
│   └── contract.py         # JSON della pipeline
├── interfaces/
│   ├── api/                # router FastAPI, DTO Pydantic, wiring con Depends
│   └── static/index.html   # UI minimale
└── infrastructure/         # modelli e repository SQLAlchemy, mock, seed, main.py
src/order_pdf_orchestration/  # stessa struttura, app separata
```

- **Domain** e **application** sono Python puro.
- **Interfaces** traduce HTTP ↔ use case e sceglie gli adapter.
- **Infrastructure** contiene database, adapter e avvio dell'app.

Dettagli: [docs/PROJECT.md](docs/PROJECT.md). Decisioni:

| ADR | Decisione |
|---|---|
| [001](docs/adr/ADR-001-clean-architecture.md) | Clean Architecture a quattro livelli |
| [002](docs/adr/ADR-002-price-tie-requires-clarification.md) | Parità di prezzo → chiarimento umano |
| [003](docs/adr/ADR-003-dependency-injection-via-ports.md) | Use case dipendono da porte, adapter iniettati |
| [004](docs/adr/ADR-004-llm-as-mocked-adapter.md) | LLM dietro una porta mockabile |
| [005](docs/adr/ADR-005-oci-punchout-out-of-scope.md) | OCI Punchout fuori scope |
| [006](docs/adr/ADR-006-erp-behind-a-gateway-port.md) | ERP dietro `ErpGateway` |
| [007](docs/adr/ADR-007-order-generation-is-llm-agent-based.md) | Generazione dell'ordine basata su agente, dietro una porta |
| [008](docs/adr/ADR-008-pydantic-validates-llm-output-at-the-boundary.md) | Pydantic valida l'output dell'agente al confine |

Tutti gli ADR sono **Proposed** finché il team non li accetta.

## UI e API

| App | Percorso | Scopo |
|---|---|---|
| Procurement | `/` | UI minimale |
| | `/docs` | Swagger / OpenAPI |
| | `/health` | health check |
| Order PDF Orchestration | `/` | UI demo |
| | `/docs` | Swagger / OpenAPI |

Endpoint del procurement (`/procurement-requests`):

- `POST /procurement-requests`: crea una richiesta da testo libero e la analizza (UC-001)
- `POST /procurement-requests/from-catalog`: crea una richiesta da catalogo (UC-005)
- `POST /procurement-requests/{id}/resolve`: sourcing (UC-002)
- `POST /procurement-requests/{id}/validate`: controllo del budget (UC-003)
- `POST /procurement-requests/{id}/create-order`: crea l'ordine e decide l'approvazione (UC-004)
- `POST /procurement-requests/{id}/approvals`: decisione di approvazione (UC-006)
- `POST /procurement-requests/{id}/send-order`: invio all'ERP (UC-007)
- `POST /procurement-requests/{id}/goods-receipt`: ricevimento merce (UC-008)
- `POST /procurement-requests/{id}/complete`: chiusura (UC-009)
- `GET /procurement-requests/{id}`: stato attuale

Ogni risposta usa il JSON della mappa: `requestId`, `status`, `parsedData`,
`resolvedData`, `validation`, `workflow`.

## Configurazione

L'unica variabile d'ambiente è `DATABASE_URL`, per esempio
`postgresql+psycopg2://user:password@host:5432/procurement`. Le credenziali non
vanno mai nel codice: in locale stanno in `.env`, già escluso da `.gitignore`;
in CI e in produzione stanno in GitHub Secrets o sulla piattaforma di hosting.

## Avvio in locale

```bash
bash scripts/setup-python.sh                   # .venv + requirements.txt (script del template)
.venv/bin/pip install -e ".[dev]"
docker compose up -d db                        # PostgreSQL 16
uvicorn procurement.infrastructure.main:app --reload
```

- UI: http://localhost:8000/ e API: http://localhost:8000/docs
- App OPO: `uvicorn order_pdf_orchestration.infrastructure.main:app --reload --port 8001`
- Senza installare nulla: `python demo.py` esegue la pipeline in memoria fino a `COMPLETED`.

## Test

| Livello | Cosa verifica | Comando | Numero |
|---|---|---|---|
| Unit | domain, application, adapter mock; senza DB | `pytest tests/unit` | 141 |
| Integration | repository SQLAlchemy su PostgreSQL | `pytest tests/integration` | 12 |
| E2E | stack HTTP completo con `TestClient` | `pytest tests/e2e` | 13 |

Integration ed e2e usano `DATABASE_URL`, che per default punta al Postgres di
`docker-compose.yml`. Il lint si lancia con `ruff check src tests`.

## Docker

```bash
docker build -t procurement-orchestrator .
docker compose up                              # app + PostgreSQL
```

## CI, release e CD

I workflow sono quelli del template AI-SDLC, completati per questo progetto.

- **CI** (`.github/workflows/ci.yml`), su push e pull request verso `main`:
  struttura AI-SDLC → lint + test unit → integration + e2e su PostgreSQL 16 →
  build dell'immagine Docker.
- **Release** (`.github/workflows/release.yml`): con un tag `vX.Y.Z` verifica
  la struttura, esegue i test unit e crea la GitHub Release.

  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```

- **CD** (`.github/workflows/cd.yml`): **non ancora attivo**. È il template
  inattivo e aspetta `scripts/deploy.sh`, `scripts/smoke-test.sh` e la variabile
  `CD_ENABLED=true`. Piattaforma, database e segreti sono da decidere con il
  team (fase 5, [docs/TASKS.md](docs/TASKS.md)).

## Agenti e MCP

- **Istruzioni condivise:** [AGENTS.md](AGENTS.md) fa da router delle fasi
  AI-SDLC; `skills/ai-sdlc-*` contiene la guida per ogni fase.
- **Setup:** `bash scripts/setup-skills.sh claude` (oppure `copilot`, `codex`,
  `all`…) espone le skill all'agente.
- **Agente e modello:** TODO (team). Indicate quale agente e quale modello
  avete usato, e perché: qualità, costo, velocità, accesso tramite LiteLLM FHNW.

### Server MCP

| | |
|---|---|
| **Server** | [GitMCP](https://gitmcp.io) per questo repository: `https://gitmcp.io/zTK47/Orchestration-Procurement` |
| **Perché** | dà all'agente il contesto di codice e documentazione del repo (README, `docs/`, ricerca nel codice), anche fuori dalla working copy locale |
| **Permessi** | solo lettura dei contenuti pubblici del repository; nessun token, nessuna scrittura su GitHub |
| **Configurazione** | `.mcp.json` (Claude Code, scope di progetto) e `.vscode/mcp.json` (VS Code); nessuna chiave nei file |

In alternativa, da riga di comando:
`claude mcp add --transport http orchestration-procurement-docs https://gitmcp.io/zTK47/Orchestration-Procurement`.

Claude Code chiede conferma prima di usare un server definito in `.mcp.json`.
Per provarlo, fate una domanda come "Spiega come è strutturato il nostro layer
API" e confrontate la risposta con e senza il server. Prova: TODO (team).

## Limiti noti

- LLM, ERP, PDF e fornitore sono mock: nessuna chiamata reale.
- Il contesto OPO salva i dati in memoria; la persistenza su PostgreSQL c'è solo
  nel contesto procurement.
- Le colonne CSV per i livelli di approvazione e per la cronologia sono una
  scorciatoia da prototipo, al posto di una tabella di audit.
- OCI Punchout, adapter SAP reale e una strategia configurabile per la parità di
  prezzo sono fuori scope.

## Licenza

Progetto a scopo didattico. `CITATION.cff` e `.zenodo.json` vengono dal template
AI-SDLC e citano il template stesso.
