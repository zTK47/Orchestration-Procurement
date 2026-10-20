"""Port for the LLM/agent that turns a prompt plus an offer into line items (ADR-007)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from order_pdf_orchestration.domain.entities import OrderLineItem, SupplierOffer


class OrderGenerationError(Exception):
    """The agent failed or returned output that does not fit the expected schema."""


class OrderGenerationAgent(ABC):
    @abstractmethod
    def generate(self, prompt_text: str, offer: SupplierOffer) -> list[OrderLineItem]:
        """Proposes line items; the domain rules decide whether they are acceptable."""
