from app.domain.references import generate_payment_reference


def test_generate_payment_reference_format() -> None:
    reference = generate_payment_reference()

    assert reference.startswith("EL-")
    assert len(reference) == 15


def test_generate_payment_reference_random_part_is_uppercase_hex() -> None:
    reference = generate_payment_reference()

    random_part = reference.removeprefix("EL-")

    assert random_part == random_part.upper()
    int(random_part, 16)
