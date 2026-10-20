# ADR-004: LLM parsing sits behind a mockable port

## Status
Proposed (2026-09-28). Acceptance: pending team review.

## Context
Free-text parsing is non-deterministic, needs network and an API key, and costs money. The business rules must stay testable and auditable.

## Alternatives
- Call an LLM directly from the use case: realistic, but tests become flaky and slow.
- Build the whole app around an autonomous agent: out of scope for a testable domain and for the timeline.
- Port plus deterministic mock now, real adapter later.

## Decision
`ParseRequestUseCase` depends on `LLMAdapter`. `MockLLMAdapter` is a regex heuristic. A LiteLLM adapter can replace it in `get_llm_adapter`.

## Consequences
- Tests are fast and reproducible offline.
- The "AI" is at the edge; core rules are plain Python.
- The mock is not a real language model — say so in the presentation.
