# ADR-008: Pydantic validates the agent's raw output at the infrastructure boundary

## Status
Proposed (2026-10-01). Acceptance: pending team review.

## Context
The whiteboard says the OrderRequest is generated "based on Pydantic". An LLM or agent
returns loosely structured data (JSON) that can be malformed: missing fields, negative
quantities, prices as strings. The Dependency Rule of this repository forbids Pydantic
in `domain/` and `application/` (AGENTS.md, ADR-001).

## Alternatives
- Make domain entities Pydantic models: less code, but couples the core to a framework
  and breaks the rule already enforced in `src/procurement`.
- Validate by hand in the use case: no framework in the core, but duplicates the checks
  the schema library already does well, and puts parsing concerns in the application layer.
- Validate the raw output with a Pydantic model inside the adapter, then convert to
  plain-Python domain objects.

## Decision
`MockOrderGenerationAgent` (and any future real adapter) validates its raw output with a
private Pydantic model (`_AgentOutput`) and only then builds `OrderLineItem` domain
objects. A schema violation raises `OrderGenerationError` (port-level error, HTTP 502).
The domain still enforces its own invariants (quantity > 0, price ≥ 0) independently.
A unit test scans `domain/` and `application/` and fails if they import Pydantic,
FastAPI, SQLAlchemy or the `procurement` package.

## Consequences
- Malformed agent output never reaches the domain.
- Two layers of checks (schema at the edge, invariants in the domain) — intentional, not duplication by accident.
- The "based on Pydantic" note on the sketch maps to a concrete, testable place in the code.
