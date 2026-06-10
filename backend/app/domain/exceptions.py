class DomainError(Exception):
    """Base exception for domain-level errors."""


class InvalidPaymentIntentStatusTransitionError(DomainError):
    """Raised when a payment intent status transition is not allowed."""
