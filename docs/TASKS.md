# TASKS.md

PHASE: 3
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

## Current Use Case

None active. DEVELOP is done and verified for both bounded contexts:

- Procurement: docs/specs/UC-001 … UC-009
- Order PDF Orchestration: docs/specs/OPO-UC-001 … OPO-UC-006

Next phase (4 = VALIDATE) starts as ready once the team selects it.

## Backlog

- [ ] Team decision on ADR-001 … ADR-008 (all Proposed): accept, change or reject, with review reference
- [ ] VALIDATE: green CI on the pull request (incl. `docker-build`), coverage check, release tag `v0.1.0`
- [ ] DEPLOY: hosting platform, database and secrets; activate `.github/workflows/cd.yml`; record the live smoke test here
- [ ] Document at least one MCP server: which, why, which permissions (course SW4)
- [ ] Record agent and model choice with rationale (course SW3)
- [ ] Complete `docs/LEARNINGS.md`; rewrite `README.md` for the project
- [ ] Trim comments/docstrings to the "avoid unnecessary comments" rule
- [ ] Later: real LLM via the FHNW LiteLLM gateway, configurable price-tie strategy, `ApprovalWorkflow` entity, OPO persistence and Dockerfile entry for the second app

## Working agreement

- Keep one active use case small enough to deliver vertically.
- Update this file when the lifecycle phase or active use case changes.
- Link decisions and validation evidence from the relevant project artefact.

## Migration to this template (2026-10-20)

Scope: move code, tests, specs, ADRs and learnings from
`zTK47/Procurement-Orchestrator-Project` (branch `claude/trusting-carson-khiovk`)
into this repository, created from the AI-SDLC template. Reason: the old
repository had modified template files (`AGENTS.md`, `skills/`,
`scripts/setup-skills.sh`, workflows). Template files are kept as delivered;
only `docs/PROJECT.md`, `docs/TASKS.md`, `.vscode/launch.json` (entry point) and
the CI/release workflows (test jobs added for VALIDATE) were completed.
No feature, API or data change. Acceptance: the full test suite passes unchanged.

The rules the old `AGENTS.md` added (dependency constraints, ADR acceptance,
regression tests first) are not in the router: changing it needs human review.
The architecture constraints are recorded in `docs/PROJECT.md`.

## Validation evidence

| Date | Command | Result |
|---|---|---|
| 2026-09-28 | `tests/unit` via a stdlib pytest shim (pytest could not be installed) | 64 passed |
| 2026-09-28 | `python demo.py` | pipeline reaches COMPLETED |
| 2026-10-01 | `pytest tests/unit/order_pdf_orchestration` | 77 passed |
| 2026-10-01 | `pytest tests/e2e/order_pdf_orchestration` | 4 passed |
| 2026-10-01 | `pytest tests` (Postgres 16 local, all contexts) | 166 passed |
| 2026-10-01 | `ruff check src tests` | all checks passed |
| 2026-10-20 | `ruff check src tests` (after migration) | all checks passed |
| 2026-10-20 | `pytest tests/unit` (Python 3.13) | 141 passed |
| 2026-10-20 | `pytest tests` (Postgres 16 local, Python 3.13) | 166 passed, 1 deprecation warning (Starlette TestClient/httpx) |
| 2026-10-20 | `python demo.py` | pipeline reaches COMPLETED |
| 2026-10-20 | `docker build` | not verified locally (Docker Hub 429 in the sandbox); checked by the CI `docker-build` job |

## OPO TDD log (2026-10-01)

Commit hashes refer to `zTK47/Procurement-Orchestrator-Project`, branch
`claude/trusting-carson-khiovk`. Every test was committed failing before its
implementation. Most red steps fail at import (the module did not exist yet);
`e9a2937` is a real assertion failure — a gap found while reviewing OPO-UC-002
(the agent could regenerate a request in NEEDS_CLARIFICATION, bypassing the
human). The dependency-rule test is a guard: it passed on its first run, so it
was checked by injecting a forbidden import once.

| Step | Commit | Change | pytest |
|---|---|---|---|
| red | `01cbdcc` | test(opo): Money value object (red) | 1 error in 0.11s |
| green | `af610db` | feat(opo): Money value object (green) | 6 passed in 0.02s |
| red | `18e382b` | test(opo): rules 3 and 4 - line item invariants and order total (red) | 1 error in 0.10s |
| green | `cbf1fc5` | feat(opo): OrderLineItem invariants and OrderRequest total (green) | 13 passed in 0.03s |
| red | `efbcec2` | test(opo): state machine, rule 1, rule 6, PDF before send (red) | 1 error in 0.11s |
| green | `a6c8bd4` | feat(opo): OrderRequest state machine, rules 1 and 6, PDF before send (green) | 27 passed in 0.04s |
| red | `579db86` | test(opo): rule 2 - line items must match the supplier offer (red) | 1 error in 0.11s |
| green | `fed79f6` | feat(opo): OrderValidationRule for rules 1 and 2 (green) | 32 passed in 0.05s |
| red | `c6b1597` | test(opo): OPO-UC-001 upload supplier offer (red) | 1 error in 0.10s |
| green | `b244af7` | feat(opo): OPO-UC-001 upload supplier offer (green) | 36 passed in 0.06s |
| red | `c6ecb4a` | test(opo): OPO-UC-002 generate order request (red) | 1 error in 0.11s |
| green | `aba148e` | feat(opo): OPO-UC-002 generate order request via the agent port (green) | 40 passed in 0.06s |
| red | `e9a2937` | test(opo): agent generation must not bypass the human revision (red) | 2 failed, 40 passed in 0.09s |
| green | `4c93efd` | fix(opo): only a DRAFT is generated by the agent (green) | 42 passed in 0.06s |
| red | `9df323a` | test(opo): OPO-UC-003 validate order request (red) | 1 error in 0.10s |
| green | `6df6e62` | feat(opo): OPO-UC-003 validate order request (green) | 46 passed in 0.06s |
| red | `f72148b` | test(opo): OPO-UC-006 revise order line items (red) | 1 error in 0.11s |
| green | `91b256a` | feat(opo): OPO-UC-006 revise order line items (green) | 50 passed in 0.07s |
| red | `2773e16` | test(opo): OPO-UC-004 render order PDF (red) | 1 error in 0.15s |
| green | `25c418c` | feat(opo): OPO-UC-004 render order PDF via the renderer port (green) | 52 passed in 0.07s |
| red | `698e6e5` | test(opo): OPO-UC-005 send order to supplier (red) | 1 error in 0.11s |
| green | `73be10a` | feat(opo): OPO-UC-005 send order to supplier (green) | 57 passed in 0.10s |
| red | `5119212` | test(opo): mock order generation agent and its Pydantic boundary (red) | 1 error in 0.11s |
| green | `7e675f7` | feat(opo): mock order generation agent, raw output schema-checked with Pydantic (green) | 68 passed in 0.44s |
| red | `cf1c7fd` | test(opo): mock document renderer writes a real PDF (red) | 1 error in 0.10s |
| green | `f80d9cd` | feat(opo): mock document renderer writes a real PDF with fpdf2 (green) | 71 passed in 0.39s |
| green | `abd292b` | test(opo): guard the Dependency Rule and context independence (guard test, passes on first run) | 3 passed in 0.03s |
| guard-check | — | injected `import pydantic` into domain/entities.py, guard went red, file restored (not committed) | 1 failed, 2 passed |
| red | `7bc95b9` | test(opo): JSON contract builder (red) | 1 error in 0.11s |
| green | `017efa7` | feat(opo): JSON contract builder (green) | 77 passed in 0.41s |
| red | `67f00f2` | test(opo): end-to-end HTTP flow for OPO-UC-001..006 (red) | 1 warning, 4 errors in 0.37s |
| green | `0d85949` | feat(opo): HTTP API, Depends wiring, separate app and demo page (green) | 4 passed, 1 warning in 0.77s |

## Decisions

See `docs/adr/`. No decision is Accepted yet.
