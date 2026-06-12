# n8n Alertmanager Workflow

This repository includes an example n8n workflow for receiving and routing EuroLedger XRPL alerts.

## Workflow File

```text
automation/n8n/euroledger-alertmanager-router.json
```

The workflow contains no credentials and no provider-specific notification nodes.

## Behavior

The workflow:

1. receives an Alertmanager webhook at `POST /webhook/euroledger-alerts`;
2. expands grouped Alertmanager notifications into individual alert items;
3. normalizes labels, annotations, timestamps and routing fields;
4. separates `firing`, `resolved` and unclassified events;
5. separates firing alerts by `critical`, `warning` and unknown severity;
6. separates firing alerts by component:
   - `backend`;
   - `xrpl-worker`;
   - `payment-intent-expirer`;
   - other components.

## Import

n8n stores workflows as JSON and supports importing them through the UI.

In n8n:

1. choose **Import from File**;
2. select `euroledger-alertmanager-router.json`;
3. review the Webhook node;
4. save and publish the workflow.

The production webhook only works after the workflow is published.

## Production URL

Inside Compose:

```text
http://n8n:5678/webhook/euroledger-alerts
```

The test URL uses `/webhook-test/` and only works while n8n is listening for a test event.

## Manual Test

```bash
curl -i   -X POST   http://localhost:5678/webhook/euroledger-alerts   -H 'Content-Type: application/json'   -d '{
    "receiver": "critical-webhook",
    "status": "firing",
    "commonLabels": {
      "alertname": "ManualWorkflowTest",
      "severity": "critical",
      "component": "backend"
    },
    "commonAnnotations": {
      "summary": "Manual n8n workflow test"
    },
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "ManualWorkflowTest",
          "severity": "critical",
          "component": "backend"
        }
      }
    ]
  }'
```

## Extending It

Add destination nodes after the relevant Switch output:

- email;
- Telegram;
- Slack;
- Discord;
- database;
- HTTP Request;
- custom internal service.

The normalized fields include:

```text
status
severity
component
alertname
summary
description
startsAt
endsAt
labels
annotations
```

## Security

The workflow intentionally contains no credentials. Configure credentials inside n8n after import and do not commit exported secrets.
