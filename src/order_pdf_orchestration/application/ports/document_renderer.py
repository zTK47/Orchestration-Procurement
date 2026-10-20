"""Port for rendering an OrderRequest as a document (PDF)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from order_pdf_orchestration.domain.entities import OrderRequest, Supplier


class DocumentRenderer(ABC):
    @abstractmethod
    def render(self, order: OrderRequest, supplier: Supplier) -> str:
        """Renders the order and returns a reference to the stored document."""

    @abstractmethod
    def read(self, pdf_reference: str) -> bytes:
        """Returns the bytes of a previously rendered document."""
