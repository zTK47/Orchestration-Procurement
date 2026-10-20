"""OPO-UC-002 - see docs/specs/OPO-UC-002-generate-order-request.md"""
from decimal import Decimal

import pytest

from order_pdf_orchestration.application.ports.order_generation_agent import (
    OrderGenerationAgent,
    OrderGenerationError,
)
from order_pdf_orchestration.application.use_cases.generate_order_request import (
    GenerateOrderRequestUseCase,
)
from order_pdf_orchestration.domain.entities import (
    OrderLineItem,
    OrderRequest,
    OrderStatus,
    SupplierOffer,
)
from order_pdf_orchestration.domain.exceptions import (
    IllegalStatusTransitionError,
    UnknownSupplierOfferError,
)
from order_pdf_orchestration.domain.value_objects import Money
from order_pdf_orchestration.infrastructure.in_memory_repositories import (
    InMemoryOrderRequestRepository,
    InMemorySupplierOfferRepository,
)

LAPTOPS = OrderLineItem(id="LI-1", description="Dell Latitude 5440 Laptop", quantity=3,
                        unit_price=Money(Decimal("1250.00"), "CHF"))


class FakeAgent(OrderGenerationAgent):
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._result = result if result is not None else [LAPTOPS]
        self._error = error

    def generate(self, prompt_text, offer):
        self.calls.append((prompt_text, offer.id))
        if self._error:
            raise self._error
        return self._result


def setup(agent: FakeAgent):
    offers = InMemorySupplierOfferRepository()
    offers.save(SupplierOffer(id="OF-1", supplier_id="SUP-1", raw_text="Dell Latitude 5440 Laptop CHF 1250"))
    orders = InMemoryOrderRequestRepository()
    return GenerateOrderRequestUseCase(agent=agent, offer_repository=offers, order_repository=orders), orders


def draft(offer_id: str = "OF-1") -> OrderRequest:
    return OrderRequest(id="OR-1", supplier_offer_id=offer_id, prompt_text="3 Dell Latitude laptops")


def test_generate_asks_the_agent_and_stores_a_generated_request():
    agent = FakeAgent()
    use_case, orders = setup(agent)

    result = use_case.execute(draft())

    assert agent.calls == [("3 Dell Latitude laptops", "OF-1")]
    assert result.status == OrderStatus.GENERATED
    assert result.line_items == [LAPTOPS]
    assert orders.get_by_id("OR-1") is result


def test_unknown_offer_is_refused_before_calling_the_agent():
    agent = FakeAgent()
    use_case, orders = setup(agent)

    with pytest.raises(UnknownSupplierOfferError):
        use_case.execute(draft(offer_id="OF-404"))

    assert agent.calls == []
    assert orders.get_by_id("OR-1") is None


def test_a_request_that_is_not_draft_is_not_regenerated():
    agent = FakeAgent()
    use_case, _ = setup(agent)
    order = draft()
    order.mark_generated([LAPTOPS])

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(order)

    assert agent.calls == []


def test_agent_failure_stores_nothing():
    use_case, orders = setup(FakeAgent(error=OrderGenerationError("schema violation")))
    order = draft()

    with pytest.raises(OrderGenerationError):
        use_case.execute(order)

    assert order.status == OrderStatus.DRAFT
    assert orders.get_by_id("OR-1") is None


def test_a_request_needing_clarification_is_not_regenerated_by_the_agent():
    agent = FakeAgent()
    use_case, _ = setup(agent)
    order = draft()
    order.mark_generated([LAPTOPS])
    order.mark_needs_clarification(["check"])

    with pytest.raises(IllegalStatusTransitionError):
        use_case.execute(order)

    assert agent.calls == []
