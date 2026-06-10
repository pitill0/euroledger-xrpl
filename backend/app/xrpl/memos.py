from app.xrpl.transactions import decode_hex_string


def encode_memo_data(value: str) -> str:
    return value.encode("utf-8").hex().upper()


def decode_memo_data(value: str) -> str:
    return decode_hex_string(value)
