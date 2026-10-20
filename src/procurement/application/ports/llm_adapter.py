"""Port for the LLM text-parsing capability.

The Application layer only knows this abstraction. Whether the concrete
implementation is a hardcoded mock (for tests and early development, see
infrastructure/mock_llm_adapter.py) or a real call to a provider via LiteLLM
is an Infrastructure concern -- see ADR-004.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from procurement.domain.value_objects import ParsedRequest


class LLMAdapter(ABC):
    @abstractmethod
    def parse(self, raw_text: str) -> ParsedRequest:
        """Extracts structured (quantity, product_name, category, confidence)
        data from a free-text procurement request."""
        ...
