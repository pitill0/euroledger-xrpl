from uuid import uuid4

PAYMENT_REFERENCE_PREFIX = "EL"
PAYMENT_REFERENCE_RANDOM_LENGTH = 12


def generate_payment_reference() -> str:
    random_part = uuid4().hex[:PAYMENT_REFERENCE_RANDOM_LENGTH].upper()
    return f"{PAYMENT_REFERENCE_PREFIX}-{random_part}"
