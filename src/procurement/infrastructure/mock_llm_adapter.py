"""Mock implementation of the LLMAdapter port.

Deliberately does NOT call any external LLM provider. It uses a simple,
deterministic heuristic so that:
  - the domain/application pipeline can be built and unit-tested today,
    without needing an API key;
  - tests are fast and reproducible (no network calls, no flakiness).

See docs/adr/ADR-004-llm-as-mocked-adapter.md for the rationale, and
docs/TASKS.md for when this gets swapped for a real LiteLLM-backed adapter.
"""
from __future__ import annotations

import re

from procurement.application.ports.llm_adapter import LLMAdapter
from procurement.domain.value_objects import ParsedRequest

_FILLER_WORDS = {
    "i", "need", "want", "please", "order", "buy", "new", "some", "a", "an",
    "the", "for", "of", "to", "get",
}

# Trailing context words that describe *who* the item is for, not *what* it
# is -- stripped so they don't get mistaken for the product category.
_TRAILING_CONTEXT_WORDS = {
    "department", "team", "office", "company", "organization", "unit",
}


def _singularize(word: str) -> str:
    """Very small heuristic: 'Laptops' -> 'Laptop'. Good enough for a mock;
    a real LLM adapter would not need this at all."""
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


class MockLLMAdapter(LLMAdapter):
    def parse(self, raw_text: str) -> ParsedRequest:
        quantity_match = re.search(r"\d+", raw_text)
        quantity = int(quantity_match.group()) if quantity_match else 1

        words = re.sub(r"[^\w\s]", "", raw_text).split()
        meaningful_words = [
            w for w in words if w.lower() not in _FILLER_WORDS and not w.isdigit()
        ]
        # Drop trailing "for the IT department" style context, if present.
        while meaningful_words and meaningful_words[-1].lower() in _TRAILING_CONTEXT_WORDS:
            meaningful_words.pop()
            if meaningful_words:
                meaningful_words.pop()  # also drop the word right before it (e.g. "IT")

        product_name = " ".join(meaningful_words) if meaningful_words else "Unknown item"
        category = _singularize(meaningful_words[-1]) if meaningful_words else "Uncategorized"

        return ParsedRequest(
            quantity=quantity,
            product_name=product_name,
            category=category,
            confidence=0.95,
        )
