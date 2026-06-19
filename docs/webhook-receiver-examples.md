# Webhook Receiver Examples

These examples show how a merchant can receive EuroLedger XRPL webhook events
and verify the `X-EuroLedger-Signature` HMAC header.

For manual local testing without extra dependencies, use the stdlib receiver in
[`../examples/webhook_receiver_stdlib.py`](../examples/webhook_receiver_stdlib.py).

The same verification rules apply to real payment intent events and to
`webhook_endpoint.test` events sent through:

```text
POST /webhook-endpoints/{endpoint_id}/test
```

## Verification Rules

Every receiver should:

1. read the raw request body before JSON parsing;
2. read `X-EuroLedger-Timestamp`;
3. read `X-EuroLedger-Signature`;
4. compute `hmac_sha256(secret, f"{timestamp}.{raw_body}")`;
5. compare the expected signature with constant-time comparison;
6. reject missing or invalid signatures;
7. reject old timestamps in production.

EuroLedger sends signatures in this format:

```text
sha256=<hex digest>
```

The timestamp tolerance in these examples is five minutes.

## FastAPI

```python
import hashlib
import hmac
import time

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI()

WEBHOOK_SECRET = "replace-with-the-endpoint-secret"
MAX_TIMESTAMP_AGE_SECONDS = 300


def verify_signature(
    *,
    secret: str,
    timestamp: str,
    raw_body: bytes,
    received_signature: str,
) -> bool:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)


def validate_timestamp(timestamp: str) -> None:
    try:
        sent_at = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid timestamp") from exc

    if abs(time.time() - sent_at) > MAX_TIMESTAMP_AGE_SECONDS:
        raise HTTPException(status_code=400, detail="Stale timestamp")


@app.post("/euroledger-webhooks")
async def receive_euroledger_webhook(
    request: Request,
    x_euroledger_event: str = Header(alias="X-EuroLedger-Event"),
    x_euroledger_delivery: str = Header(alias="X-EuroLedger-Delivery"),
    x_euroledger_timestamp: str = Header(alias="X-EuroLedger-Timestamp"),
    x_euroledger_signature: str = Header(alias="X-EuroLedger-Signature"),
) -> dict[str, str]:
    raw_body = await request.body()

    validate_timestamp(x_euroledger_timestamp)

    if not verify_signature(
        secret=WEBHOOK_SECRET,
        timestamp=x_euroledger_timestamp,
        raw_body=raw_body,
        received_signature=x_euroledger_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()

    # Process the event idempotently using x_euroledger_delivery.
    print(
        "received",
        x_euroledger_event,
        x_euroledger_delivery,
        payload,
    )

    return {"status": "ok"}
```

## Flask

```python
import hashlib
import hmac
import time

from flask import Flask, abort, request

app = Flask(__name__)

WEBHOOK_SECRET = "replace-with-the-endpoint-secret"
MAX_TIMESTAMP_AGE_SECONDS = 300


def verify_signature(
    *,
    secret: str,
    timestamp: str,
    raw_body: bytes,
    received_signature: str,
) -> bool:
    signed_payload = timestamp.encode("utf-8") + b"." + raw_body
    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)


def validate_timestamp(timestamp: str) -> None:
    try:
        sent_at = int(timestamp)
    except ValueError:
        abort(400, "Invalid timestamp")

    if abs(time.time() - sent_at) > MAX_TIMESTAMP_AGE_SECONDS:
        abort(400, "Stale timestamp")


@app.post("/euroledger-webhooks")
def receive_euroledger_webhook():
    raw_body = request.get_data()
    event_type = request.headers.get("X-EuroLedger-Event")
    delivery_id = request.headers.get("X-EuroLedger-Delivery")
    timestamp = request.headers.get("X-EuroLedger-Timestamp")
    signature = request.headers.get("X-EuroLedger-Signature")

    if not all([event_type, delivery_id, timestamp, signature]):
        abort(400, "Missing webhook headers")

    validate_timestamp(timestamp)

    if not verify_signature(
        secret=WEBHOOK_SECRET,
        timestamp=timestamp,
        raw_body=raw_body,
        received_signature=signature,
    ):
        abort(400, "Invalid signature")

    payload = request.get_json()

    # Process the event idempotently using delivery_id.
    print("received", event_type, delivery_id, payload)

    return {"status": "ok"}
```

## Node.js and Express

Express must keep the raw body available for signature verification. This
example uses `express.raw()` for the webhook route and parses JSON only after
the signature is valid.

```javascript
const crypto = require("crypto");
const express = require("express");

const app = express();

const WEBHOOK_SECRET = "replace-with-the-endpoint-secret";
const MAX_TIMESTAMP_AGE_SECONDS = 300;

function verifySignature({
  secret,
  timestamp,
  rawBody,
  receivedSignature,
}) {
  const signedPayload = Buffer.concat([
    Buffer.from(`${timestamp}.`, "utf8"),
    rawBody,
  ]);
  const digest = crypto
    .createHmac("sha256", secret)
    .update(signedPayload)
    .digest("hex");
  const expectedSignature = `sha256=${digest}`;
  const expected = Buffer.from(expectedSignature);
  const received = Buffer.from(receivedSignature);

  return (
    expected.length === received.length &&
    crypto.timingSafeEqual(expected, received)
  );
}

function validateTimestamp(timestamp) {
  const sentAt = Number.parseInt(timestamp, 10);

  if (Number.isNaN(sentAt)) {
    throw new Error("Invalid timestamp");
  }

  const ageSeconds = Math.abs(Date.now() / 1000 - sentAt);

  if (ageSeconds > MAX_TIMESTAMP_AGE_SECONDS) {
    throw new Error("Stale timestamp");
  }
}

app.post(
  "/euroledger-webhooks",
  express.raw({ type: "application/json" }),
  (req, res) => {
    const eventType = req.header("X-EuroLedger-Event");
    const deliveryId = req.header("X-EuroLedger-Delivery");
    const timestamp = req.header("X-EuroLedger-Timestamp");
    const signature = req.header("X-EuroLedger-Signature");

    if (!eventType || !deliveryId || !timestamp || !signature) {
      return res.status(400).json({ error: "Missing webhook headers" });
    }

    try {
      validateTimestamp(timestamp);

      const validSignature = verifySignature({
        secret: WEBHOOK_SECRET,
        timestamp,
        rawBody: req.body,
        receivedSignature: signature,
      });

      if (!validSignature) {
        return res.status(400).json({ error: "Invalid signature" });
      }

      const payload = JSON.parse(req.body.toString("utf8"));

      // Process the event idempotently using deliveryId.
      console.log("received", eventType, deliveryId, payload);

      return res.json({ status: "ok" });
    } catch (error) {
      return res.status(400).json({ error: error.message });
    }
  },
);

app.listen(3000, () => {
  console.log("EuroLedger webhook receiver listening on port 3000");
});
```

## Operational Notes

- Store the endpoint secret outside source control.
- Use one secret per endpoint.
- Process each `X-EuroLedger-Delivery` idempotently.
- Return a 2xx response only after the event has been accepted.
- Return a non-2xx response when the event should be retried.
- Avoid logging full payloads in production if they may contain customer data.
