from datetime import datetime
from decimal import Decimal
from hmac import compare_digest
from html import escape
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.payment_intent import PaymentIntent
from app.models.webhook import WebhookDelivery
from app.repositories.payment_intents import get_payment_intent_by_id_unscoped
from app.repositories.webhook_deliveries import list_webhook_deliveries_for_payment_intent

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    include_in_schema=False,
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

DashboardToken = Annotated[
    str | None,
    Query(
        min_length=1,
    ),
]


@router.get(
    "/payment-intents/{payment_intent_id}",
    response_class=HTMLResponse,
)
def payment_intent_dashboard_endpoint(
    payment_intent_id: str,
    db: DbSession,
    token: DashboardToken = None,
) -> HTMLResponse:
    settings = get_settings()

    if settings.dashboard_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard is not configured.",
        )

    if token is None or not compare_digest(token, settings.dashboard_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid dashboard token.",
        )

    payment_intent = get_payment_intent_by_id_unscoped(
        db,
        payment_intent_id,
    )

    if payment_intent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found.",
        )

    deliveries = list_webhook_deliveries_for_payment_intent(
        db,
        payment_intent_id=payment_intent.id,
        limit=20,
    )

    return HTMLResponse(
        content=render_payment_intent_dashboard(
            payment_intent=payment_intent,
            deliveries=deliveries,
        ),
    )


def render_payment_intent_dashboard(
    *,
    payment_intent: PaymentIntent,
    deliveries: list[WebhookDelivery],
) -> str:
    title = f"Payment intent {payment_intent.reference}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --el-bg: #f6f7fb;
      --el-card: #ffffff;
      --el-border: #dcdcde;
      --el-muted: #646970;
      --el-text: #1d2327;
      --el-accent: #3858e9;
      --el-success-bg: #edfaef;
      --el-success: #008a20;
      --el-warning-bg: #fcf9e8;
      --el-warning: #996800;
      --el-danger-bg: #fcf0f1;
      --el-danger: #b32d2e;
      --el-neutral-bg: #f0f0f1;
      --el-neutral: #50575e;
    }}
    body {{
      margin: 0;
      background: var(--el-bg);
      color: var(--el-text);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.2;
    }}
    .muted {{ color: var(--el-muted); }}
    .card {{
      background: var(--el-card);
      border: 1px solid var(--el-border);
      border-radius: 14px;
      box-shadow: 0 1px 2px rgba(0,0,0,.04);
      margin-bottom: 20px;
      overflow: hidden;
    }}
    .card h2 {{
      border-bottom: 1px solid var(--el-border);
      font-size: 16px;
      margin: 0;
      padding: 14px 18px;
    }}
    .grid {{
      display: grid;
      gap: 1px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      background: var(--el-border);
    }}
    .field {{
      background: var(--el-card);
      padding: 14px 18px;
      min-width: 0;
    }}
    .label {{
      color: var(--el-muted);
      display: block;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: .02em;
      margin-bottom: 5px;
      text-transform: uppercase;
    }}
    code {{
      background: #f6f7f7;
      border-radius: 5px;
      display: inline-block;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      max-width: 100%;
      overflow-wrap: anywhere;
      padding: 2px 5px;
    }}
    .badge {{
      border-radius: 999px;
      display: inline-block;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 10px;
      text-transform: uppercase;
    }}
    .status-confirmed, .status-delivered {{
      background: var(--el-success-bg);
      color: var(--el-success);
    }}
    .status-pending, .status-failed {{
      background: var(--el-warning-bg);
      color: var(--el-warning);
    }}
    .status-expired, .status-cancelled, .status-discarded {{
      background: var(--el-danger-bg);
      color: var(--el-danger);
    }}
    .status-unknown {{
      background: var(--el-neutral-bg);
      color: var(--el-neutral);
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
    }}
    th, td {{
      border-bottom: 1px solid var(--el-border);
      padding: 12px 14px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--el-muted); font-size: 12px; text-transform: uppercase; }}
    tr:last-child td {{ border-bottom: 0; }}
    @media (max-width: 760px) {{
      .hero {{ display: block; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div>
        <h1>{escape(payment_intent.reference)}</h1>
        <div class="muted">Payment intent {code(payment_intent.id)}</div>
      </div>
      {status_badge(status_value(payment_intent.status))}
    </section>

    <section class="card">
      <h2>Payment intent</h2>
      <div class="grid">
        {field("Amount", f"{payment_intent.amount} {payment_intent.currency}")}
        {field("Status", status_badge(status_value(payment_intent.status)), raw=True)}
        {field("Merchant ID", code(payment_intent.merchant_id), raw=True)}
        {field("Reference", code(payment_intent.reference), raw=True)}
        {field("Description", payment_intent.description)}
        {field("Expected destination", code(payment_intent.expected_destination), raw=True)}
        {field("XRPL transaction hash", code(payment_intent.xrpl_transaction_hash), raw=True)}
        {field("Cancellation reason", payment_intent.cancellation_reason)}
        {field("Created at", format_datetime(payment_intent.created_at))}
        {field("Updated at", format_datetime(payment_intent.updated_at))}
        {field("Expires at", format_datetime(payment_intent.expires_at))}
        {field("Cancelled at", format_datetime(payment_intent.cancelled_at))}
      </div>
    </section>

    <section class="card">
      <h2>Webhook deliveries</h2>
      {render_deliveries(deliveries)}
    </section>
  </main>
</body>
</html>
"""


def render_deliveries(deliveries: list[WebhookDelivery]) -> str:
    if not deliveries:
        return (
            '<div class="field muted">No webhook deliveries recorded for this payment intent.</div>'
        )

    rows = "".join(render_delivery_row(delivery) for delivery in deliveries)
    return f"""<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Event</th>
      <th>Attempts</th>
      <th>Last attempt</th>
      <th>Response</th>
      <th>Delivery ID</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""


def render_delivery_row(delivery: WebhookDelivery) -> str:
    response = "—"
    if delivery.response_status_code is not None:
        response = str(delivery.response_status_code)
    elif delivery.error_message:
        response = delivery.error_message

    return f"""<tr>
  <td>{status_badge(status_value(delivery.status))}</td>
  <td>{escape(delivery.event_type)}</td>
  <td>{delivery.attempt_count}</td>
  <td>{escape(format_datetime(delivery.last_attempt_at))}</td>
  <td>{escape(response)}</td>
  <td>{code(delivery.id)}</td>
</tr>"""


def field(label: str, value: Any, *, raw: bool = False) -> str:
    rendered = value if raw else escape(format_value(value))
    return f'<div class="field"><span class="label">{escape(label)}</span>{rendered}</div>'


def status_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def status_badge(value: str) -> str:
    known_statuses = {
        "pending",
        "confirmed",
        "expired",
        "cancelled",
        "delivered",
        "failed",
        "discarded",
    }
    css_value = value if value in known_statuses else "unknown"
    return f'<span class="badge status-{escape(css_value)}">{escape(value)}</span>'


def code(value: Any) -> str:
    formatted = format_value(value)
    if formatted == "—":
        return formatted

    return f"<code>{escape(formatted)}</code>"


def format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return format_datetime(value)

    return str(value)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"

    return value.isoformat().replace("+00:00", "Z")
