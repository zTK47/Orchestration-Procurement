# ADR-002: A price tie in the Sourcing Funnel needs human clarification

## Status
Proposed (2026-09-28). Acceptance: pending team review.

## Context
The whiteboard suggested `min(matching_items, key=unit_price)`. On equal prices `min()` silently returns the first item, so the choice would depend on list order and leave no trace.

## Alternatives
- `min()` by price: simple, but arbitrary and unauditable on ties.
- Configurable company procurement strategy (preferred supplier, shortest lead time): the whiteboard's open question; more realistic, more scope.
- Raise an error and ask a human.

## Decision
`SourcingRule.resolve` raises `RequiresClarificationError` when two or more items tie for the lowest price. The API answers 422.

## Consequences
- A tie stops the pipeline instead of guessing.
- A configurable strategy remains possible later without changing this rule's callers.
- If the team prefers `min()`, this ADR is superseded, not edited.
