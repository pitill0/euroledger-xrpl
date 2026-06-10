class DomainError(Exception):
    """Base exception for domain-level errors."""


class InvalidPaymentIntentStatusTransitionError(DomainError):
    """Raised when a payment intent status transition is not allowed."""


class PaymentValidationError(DomainError):
    """Raised when a detected payment does not match a payment intent."""
