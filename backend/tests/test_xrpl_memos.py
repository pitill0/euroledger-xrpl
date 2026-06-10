from app.xrpl.memos import decode_memo_data, encode_memo_data


def test_encode_memo_data_as_uppercase_hex() -> None:
    assert encode_memo_data("EL-ABC123DEF456") == "454C2D414243313233444546343536"


def test_decode_memo_data_from_hex() -> None:
    assert decode_memo_data("454C2D414243313233444546343536") == "EL-ABC123DEF456"
