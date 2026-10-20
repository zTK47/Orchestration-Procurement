# UC-001 — Parse Request

## Intent
Turn a free-text purchase need into structured data (`ParsedRequest`) so the pipeline can act on it.

## Actors
Requester (employee); `LLMAdapter` (system, mocked for now — ADR-004).

## Preconditions
A `ProcurementRequest` exists in `CREATED` with non-empty `raw_text`.

## Flow
1. The adapter extracts quantity, product name, category and confidence.
2. The request stores the result and moves to `PARSED`; it is saved.

## Errors
- `raw_text` missing → `ValueError`, no state change.
- Adapter output violates `ParsedRequest` invariants (quantity ≤ 0, confidence outside 0..1) → `ValueError`.

## Acceptance
- Given raw text, when parsing runs, then status is `PARSED` and `parsed_data` is set.
- Given no raw text, when parsing runs, then it fails and the status stays `CREATED`.

## Tests
| Level | Test |
|---|---|
| Unit | `tests/unit/application/test_parse_request_use_case.py`, `tests/unit/infrastructure/test_mock_llm_adapter.py` |
| E2E | `tests/e2e/test_free_text_pipeline_e2e.py` |
