#!/usr/bin/env python3
"""Local EuroLedger XRPL webhook receiver using only Python stdlib."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999
DEFAULT_PATH = "/webhook"
DEFAULT_MAX_TIMESTAMP_AGE_SECONDS = 300

HEADER_EVENT = "X-EuroLedger-Event"
HEADER_DELIVERY = "X-EuroLedger-Delivery"
HEADER_TIMESTAMP = "X-EuroLedger-Timestamp"
HEADER_SIGNATURE = "X-EuroLedger-Signature"


@dataclass(frozen=True)
class ReceiverConfig:
    secret: str
    path: str
    max_timestamp_age_seconds: int
    skip_timestamp_check: bool
    force_status: int | None


def json_bytes(
    payload: dict[str, Any],
) -> bytes:
    return json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")


def verify_signature(
    *,
    secret: str,
    timestamp: str,
    raw_body: bytes,
    received_signature: str,
) -> bool:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected_signature = (
        "sha256="
        + hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(expected_signature, received_signature)


def validate_timestamp(
    timestamp: str,
    *,
    max_age_seconds: int,
) -> None:
    try:
        sent_at = int(timestamp)
    except ValueError as exc:
        raise ValueError("Invalid webhook timestamp.") from exc

    age_seconds = abs(time.time() - sent_at)

    if age_seconds > max_age_seconds:
        raise ValueError("Webhook timestamp is outside the accepted window.")


class EuroLedgerWebhookHandler(BaseHTTPRequestHandler):
    server: EuroLedgerWebhookServer

    def log_message(
        self,
        format: str,
        *args: Any,
    ) -> None:
        print(
            "http",
            self.address_string(),
            "-",
            format % args,
        )

    def do_POST(self) -> None:
        config = self.server.receiver_config

        if self.path != config.path:
            self.respond(
                HTTPStatus.NOT_FOUND,
                {
                    "error": "Not found",
                },
            )
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        event_type = self.headers.get(HEADER_EVENT)
        delivery_id = self.headers.get(HEADER_DELIVERY)
        timestamp = self.headers.get(HEADER_TIMESTAMP)
        signature = self.headers.get(HEADER_SIGNATURE)

        missing_headers = [
            header
            for header, value in [
                (HEADER_EVENT, event_type),
                (HEADER_DELIVERY, delivery_id),
                (HEADER_TIMESTAMP, timestamp),
                (HEADER_SIGNATURE, signature),
            ]
            if not value
        ]

        if missing_headers:
            self.respond(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": "Missing webhook headers",
                    "missing_headers": missing_headers,
                },
            )
            return

        assert event_type is not None
        assert delivery_id is not None
        assert timestamp is not None
        assert signature is not None

        try:
            if not config.skip_timestamp_check:
                validate_timestamp(
                    timestamp,
                    max_age_seconds=config.max_timestamp_age_seconds,
                )

            valid_signature = verify_signature(
                secret=config.secret,
                timestamp=timestamp,
                raw_body=raw_body,
                received_signature=signature,
            )

            if not valid_signature:
                raise ValueError("Invalid webhook signature.")

            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self.respond(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": str(exc),
                },
            )
            return

        print(
            json.dumps(
                {
                    "event": event_type,
                    "delivery_id": delivery_id,
                    "payload": payload,
                },
                indent=2,
                sort_keys=True,
            )
        )

        response_status = config.force_status or HTTPStatus.OK
        self.respond(
            response_status,
            {
                "status": "accepted",
                "event": event_type,
                "delivery_id": delivery_id,
            },
        )

    def respond(
        self,
        status_code: int,
        payload: dict[str, Any],
    ) -> None:
        body = json_bytes(payload)

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class EuroLedgerWebhookServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[EuroLedgerWebhookHandler],
        *,
        receiver_config: ReceiverConfig,
    ) -> None:
        super().__init__(
            server_address,
            handler_class,
        )
        self.receiver_config = receiver_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local EuroLedger XRPL webhook receiver.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind host. Defaults to {DEFAULT_HOST}.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Bind port. Defaults to {DEFAULT_PORT}.",
    )
    parser.add_argument(
        "--path",
        default=DEFAULT_PATH,
        help=f"Webhook path. Defaults to {DEFAULT_PATH}.",
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("EUROLEDGER_WEBHOOK_SECRET"),
        help="Endpoint secret. Defaults to EUROLEDGER_WEBHOOK_SECRET.",
    )
    parser.add_argument(
        "--max-timestamp-age-seconds",
        type=int,
        default=DEFAULT_MAX_TIMESTAMP_AGE_SECONDS,
        help=(
            "Maximum accepted timestamp age in seconds. "
            f"Defaults to {DEFAULT_MAX_TIMESTAMP_AGE_SECONDS}."
        ),
    )
    parser.add_argument(
        "--skip-timestamp-check",
        action="store_true",
        help="Disable timestamp freshness validation for local debugging.",
    )
    parser.add_argument(
        "--force-status",
        type=int,
        default=None,
        help="Always return this HTTP status after a valid signature.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.secret:
        raise SystemExit(
            "Missing webhook secret. Set EUROLEDGER_WEBHOOK_SECRET or --secret.",
        )

    config = ReceiverConfig(
        secret=args.secret,
        path=args.path,
        max_timestamp_age_seconds=args.max_timestamp_age_seconds,
        skip_timestamp_check=args.skip_timestamp_check,
        force_status=args.force_status,
    )
    server = EuroLedgerWebhookServer(
        (args.host, args.port),
        EuroLedgerWebhookHandler,
        receiver_config=config,
    )

    print(
        f"Listening on http://{args.host}:{args.port}{args.path}",
        flush=True,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping receiver.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
