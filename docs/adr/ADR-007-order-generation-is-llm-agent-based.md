# ADR-007: Order generation is LLM/agent-based, behind a mockable port

## Status
Proposed (2026-10-01). Acceptance: pending team review.

## Context
The whiteboard sketch "Free Text Order Orchestration" leaves one question open:
"is this LLM/Agent based?". A buyer writes a free-text prompt ("3 Dell laptops and
5 keyboards") against a supplier offer that is also free text. Turning both into
structured line items is a language task: wording, plurals, quantities and product
names vary from offer to offer.

## Alternatives
- Rule-based parser only (regex + keyword table): deterministic and cheap, but breaks
  on every new offer layout and phrasing; becomes a maintenance burden.
- LLM/agent called directly from the use case: realistic, but tests need network,
  a key and money, and become non-deterministic.
- LLM/agent-shaped port, deterministic mock for now, real adapter later.

## Decision
Yes, it is LLM/agent-based by design. `GenerateOrderRequestUseCase` depends on the
`OrderGenerationAgent` port (`generate(prompt_text, offer) -> list[OrderLineItem]`).
`MockOrderGenerationAgent` is a deterministic regex/keyword heuristic used for tests
and the demo. A real adapter would call a model through the FHNW LiteLLM gateway,
with the key read from an environment variable (SW3, slide 55) and never committed.
The agent only proposes line items; business rules (OPO-UC-003) and a human
(OPO-UC-006) decide what is sent.

## Consequences
- The open question on the sketch is answered explicitly and can be reversed by
  swapping one adapter in `interfaces/api/dependencies.py`.
- Tests stay fast and offline; the mock is not a language model — say so in the presentation.
- LLM output is untrusted input: it is schema-checked at the boundary (ADR-008) and
  checked against the offer by domain rules before it can be sent.
