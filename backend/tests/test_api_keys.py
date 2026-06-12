from app.domain.api_keys import (
    api_key_digest_matches,
    generate_api_key,
    parse_api_key,
)

PEPPER = "test-pepper-with-at-least-thirty-two-characters"


def test_generated_api_key_has_expected_format() -> None:
    generated = generate_api_key(
        pepper=PEPPER,
    )

    parsed = parse_api_key(
        generated.value,
    )

    assert generated.value.startswith("elk_")
    assert len(generated.key_prefix) == 12
    assert parsed.key_prefix == generated.key_prefix
    assert len(generated.key_digest) == 64


def test_generated_key_digest_matches() -> None:
    generated = generate_api_key(
        pepper=PEPPER,
    )

    assert api_key_digest_matches(
        generated.value,
        expected_digest=generated.key_digest,
        pepper=PEPPER,
    )


def test_modified_key_does_not_match() -> None:
    generated = generate_api_key(
        pepper=PEPPER,
    )

    modified = generated.value + "x"

    assert not api_key_digest_matches(
        modified,
        expected_digest=generated.key_digest,
        pepper=PEPPER,
    )


def test_same_key_with_different_pepper_does_not_match() -> None:
    generated = generate_api_key(
        pepper=PEPPER,
    )

    assert not api_key_digest_matches(
        generated.value,
        expected_digest=generated.key_digest,
        pepper=("another-test-pepper-with-more-than-32-characters"),
    )
