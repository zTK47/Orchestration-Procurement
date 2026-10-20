"""Domain-level exceptions.

These represent violations of business rules (domain invariants), not
technical failures. They must never leak infrastructure details.
"""


class DomainError(Exception):
    """Base class for all domain rule violations."""


class IllegalStatusTransitionError(DomainError):
    """Raised when a ProcurementRequest is asked to move to a status that is
    not reachable from its current status (see the workflow state machine)."""


class SelectedItemUnavailableError(DomainError):
    """Raised when a user explicitly selects a CatalogItem (direct catalog
    intake, as opposed to free-text parsing) that turns out to be from an
    unapproved supplier or lacks sufficient stock."""


class RequiresClarificationError(DomainError):
    """Raised by the Sourcing Funnel when two or more CatalogItems are tied
    on price and the system cannot pick a winner automatically."""


class NoMatchingCatalogItemError(DomainError):
    """Raised by the Sourcing Funnel when no CatalogItem satisfies the
    approved-supplier / stock / lead-time filters."""


class DuplicateApprovalError(DomainError):
    """Raised when the same approver tries to record a second decision for
    the same approval level on the same ProcurementRequest."""


class BudgetExceededError(DomainError):
    """Raised when approving a request would make a CostCenter's spent
    amount exceed its total budget."""


class UnauthorizedApproverError(DomainError):
    """Raised when a user without the required role attempts to record an
    approval decision for a given approval level."""
