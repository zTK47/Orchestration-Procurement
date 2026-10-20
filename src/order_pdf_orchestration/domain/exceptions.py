"""Business-rule violations of the Order PDF Orchestration context."""


class DomainError(Exception):
    """Base class for all domain rule violations."""


class InvalidLineItemError(DomainError):
    """A line item has a blank description or a quantity that is not positive."""


class IllegalStatusTransitionError(DomainError):
    """The OrderRequest cannot reach the requested status from its current one."""


class EmptyOrderRequestError(DomainError):
    """An OrderRequest needs at least one line item to be validated or revised."""


class OrderNotValidatedError(DomainError):
    """The action (e.g. rendering the PDF) needs a VALIDATED OrderRequest."""


class PdfNotRenderedError(DomainError):
    """An order is only sent to the supplier together with its rendered PDF."""


class InvalidSupplierOfferError(DomainError):
    """A supplier offer needs non-blank text."""


class UnknownSupplierError(DomainError):
    """The referenced supplier does not exist."""


class UnknownSupplierOfferError(DomainError):
    """The referenced supplier offer does not exist."""
