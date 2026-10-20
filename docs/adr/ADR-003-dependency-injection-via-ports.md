# ADR-003: Use cases depend on ports; adapters are injected

## Status
Proposed (2026-09-28). Acceptance: pending team review.

## Context
Use cases need persistence and, later, LLM and ERP access without knowing the technology (Dependency Inversion, Lecture 2).

## Alternatives
- Use cases instantiate SQLAlchemy sessions or HTTP clients directly: hard to test, tightly coupled.
- A DI container library: more machinery than this project needs.
- Abstract base classes as ports plus FastAPI `Depends`.

## Decision
Ports live in `application/ports/`. `interfaces/api/dependencies.py` is the only place that picks concrete adapters. Unit tests use the in-memory repositories.

## Consequences
- Swapping in-memory for SQLAlchemy, or mock for real LLM/ERP, touches one file.
- Every new external dependency needs a port first.
