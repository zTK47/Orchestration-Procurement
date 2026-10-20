# ADR-006: ERP hand-off behind an `ErpGateway` port

## Status
Proposed (2026-09-28). Acceptance: pending team review.

## Context
The whiteboard ends in `ORDER_SENT → GOODS_RECEIPT → COMPLETED` with a JSON call to SAP. A real SAP connection is not available or in scope, but the workflow must be complete and testable.

## Alternatives
- Stop the workflow at `APPROVED` and leave the last states unused (previous state of the repo).
- Call an ERP HTTP API directly from the use cases.
- Port `ErpGateway` with a mock adapter now.

## Decision
`SendOrderToErpUseCase` and `RecordGoodsReceiptUseCase` call `ErpGateway`. `MockErpGateway` returns `PO-<id>` and records calls. The gateway is called only after the transition was checked, and the request changes only after the ERP call succeeded.

## Consequences
- The pipeline runs from raw text to `COMPLETED` and is testable, including ERP failure (502).
- A SAP adapter is a new class in `infrastructure/`; no use case changes.
- The mock proves the flow, not the SAP integration.
