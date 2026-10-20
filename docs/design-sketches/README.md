# Design sketches

The team's initial sketches (26–30 September), drawn on
[Excalidraw](https://excalidraw.com/#room=3c4bdb1147ddb60d24ab,gAuR7NMiUHYVB3bp2xksUQ).
They are input for SPECIFY and DESIGN, not approved decisions: final choices
are recorded as ADRs.

## Free Text Order Orchestration

![Free Text Order Orchestration](free-text-order-orchestration.png)

The user writes an order in free text; an LLM/agent generates an
`OrderRequest`, which is validated and then sent to the supplier automatically.

| Step | Actor |
|---|---|
| Upload the supplier offer (UI) | Human |
| User prompt (UI) | Human |
| Generate `OrderRequest` + PDF, based on Pydantic | System |
| Validate the `OrderRequest` | System/Human, or automated basic business rules |
| Send to supplier | System |

Open question: is this LLM/agent-based?

## Catalog Order Logic

![Catalog Order Logic](catalog-order-logic.png)

The natural-language prompt is broken down using master data and business
logic. Example: "I need 5 new Lenovo Laptop" →
`quantity: 5`, `productName: "Lenovo Laptop"`, `productCategory: "Laptop"`.

- **Business rule:** all orders are requested through the ERP (by prompting).
- **Three catalog types:** Catalog, Free text, OCI Punchout.
- **Entities:** Supplier, User, ProductCategory, CostCenter, ApprovalWorkflow,
  ProcurementRequest, ParsedRequest, CatalogItem, ContractType.
- **Value objects:** price, currency, amount, sku, quantity.
- **Workflow states:** CREATED → PARSED → RESOLVED → VALIDATED →
  PENDING_APPROVAL → APPROVED → ORDER_SENT → GOODS_RECEIPT → COMPLETED
  (then JSON → SAP API → Goods Receipt).
- **Layers:**
  - Domain: ProcurementRequest, SourcingRules, ParsedRequest
  - Application: ParseRequestUseCase, ResolveItemUseCase, CreateOrderUseCase
  - Infrastructure: FastAPI endpoints, SQLite repositories, LLM adapter
- **Example JSON:** `parsedData`, `resolvedData` (sku, supplierId,
  unitPrice, currency CHF), `validation` (budgetCheck, stockCheck,
  requiresApproval, approvalLevel MANAGER), `workflow` (currentState,
  nextState, history).

Open question: if more than one catalog offers the same product, which one is
chosen? The sketch suggests `min(matching_items, key=lambda x: x.unit_price)`,
or a company procurement strategy.
