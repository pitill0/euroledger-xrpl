# Architecture

## High-Level Architecture

```text
Merchant / SME / WooCommerce Plugin
        |
        v
EuroLedger Plugin / Client SDK
        |
        v
Backend API
- payment request creation
- unique reference generation
- invoice/payment intent creation
- XRPL monitoring
- payment confirmation
- reconciliation
- accounting export
        |
        v
XRPL Testnet / Devnet / future Mainnet
- demo EUR issuer account
- demo EUR token
- trust lines
- tokenized EUR payments
- memos/references
- traceability
        |
        v
Dashboard
- payments
- invoices
- statuses
- audit trail
- logs
- exports
