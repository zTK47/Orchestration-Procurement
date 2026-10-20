# ADR-005: OCI Punchout is out of scope

## Status
Proposed (2026-09-28). Acceptance: pending team review.

## Context
The whiteboard lists three intake types: Catalog, Free text, OCI Punchout. Punchout needs an external hosted-catalog session and cXML exchange.

## Alternatives
- Implement Punchout with a fake supplier: large effort, little architectural learning.
- Implement two intake modes and document the third as future work.

## Decision
Only Catalog (UC-005) and Free text (UC-001/002) are implemented.

## Consequences
- Two of three modes are complete and tested.
- Punchout is listed in `docs/PROJECT.md` under Scope.
