# Scope

## In Scope

The initial scope of EuroLedger XRPL includes:

- XRPL Testnet experimentation.
- Demo EUR issued currency.
- Payment intent creation.
- Invoice/payment reference generation.
- XRPL transaction monitoring.
- Payment confirmation.
- Basic reconciliation exports.
- Local development environment.
- Experimental WooCommerce plugin in a later phase.
- Compliance-by-design documentation.

## Out of Scope for the MVP

The MVP does not include:

- real stablecoin issuance;
- real custody of funds;
- production financial services;
- real KYC/KYB;
- real SEPA integration;
- banking integrations;
- regulatory licensing;
- investment functionality;
- XRP trading;
- a complete end-user wallet;
- a mobile app.

## MVP Success Definition

The MVP succeeds if it can demonstrate the following testnet-only flow:

1. A merchant creates a 25 EUR payment request.
2. The system generates a unique payment reference.
3. A customer pays using a demo EUR token on XRPL Testnet.
4. The backend detects the transaction.
5. The backend validates amount, issuer, destination and reference.
6. The payment is marked as confirmed.
7. The operation can be exported for reconciliation.
