# ADR-001: Clean Architecture with four layers

## Status
Proposed (2026-09-28). Acceptance: pending team review — record name, date and review reference here.

## Context
The module requires enterprise-grade architecture, separation of business logic from framework code, and a domain that can be tested without infrastructure.

## Alternatives
- Simple three-layer architecture (presentation / business / data): less structure, but business rules tend to depend on the ORM and are harder to test in isolation.
- Framework-centric FastAPI app (logic in routes and models): fastest to write, no isolation.

## Decision
`domain ← application ← interfaces ← infrastructure`. `domain/` and `application/` import no third-party framework.

## Consequences
- Unit tests for domain and application need no database or web framework.
- Persistence or LLM/ERP providers change in `infrastructure/` only.
- More files and ports than a flat app.
