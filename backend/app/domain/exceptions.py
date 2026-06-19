class DomainError(Exception):
    """Base exception for domain-level errors."""


class InvalidPaymentIntentStatusTransitionError(DomainError):
    """Raised when a payment intent status transition is not allowed."""


class PaymentIntentCancellationConflictError(DomainError):
    """Raised when a cancellation replay uses a different reason."""


class InvalidPaymentIntentCursorError(DomainError):
    """Raised when a payment intent pagination cursor is invalid."""


class InvalidPaymentIntentListFilterError(DomainError):
    """Raised when payment intent list filters are inconsistent."""


class MerchantAlreadyExistsError(DomainError):
    """Raised when a merchant slug is already registered."""


class MerchantNotFoundError(DomainError):
    """Raised when a merchant cannot be found."""


class PaymentValidationError(DomainError):
    """Raised when a detected payment does not match a payment intent."""


class WebhookDeliveryRetryConflictError(DomainError):
    """Raised when a webhook delivery cannot be manually retried."""
