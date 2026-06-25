# Post-release readiness plan

After publishing WooCommerce Gateway `0.1.3`, the next phase should focus on repository and product readiness before making the project public.

## 1. Documentation audit

Review and reorganize:

- Main `README.md`.
- `docs/`.
- `plugin-woocommerce/`.
- Backend API documentation.
- Webhook documentation.
- Observability documentation.
- CI documentation.
- Release documentation.
- Merchant installation guide.

Goals:

- Remove duplicated or outdated content.
- Add a clear documentation index.
- Ensure every important document is linked from the main README.
- Separate developer, operator, and merchant-facing documentation.

## 2. Architecture documentation

Add or update diagrams for:

- Overall EuroLedger XRPL architecture.
- Backend services and database.
- XRPL worker flow.
- Payment intent lifecycle.
- Merchant webhook delivery flow.
- WooCommerce gateway flow.
- Observability stack.

Mermaid diagrams are likely enough for the first public version.

## 3. Publication readiness

Review:

- `.env.example` files.
- Docker Compose examples.
- Secret handling.
- Local-only references.
- Gitea-specific references.
- Badges.
- Screenshots.
- Release tags.
- Public issue templates if needed.

## 4. License review

Review the current license decision before public release.

Current candidate:

- Apache License 2.0.

Check before publishing:

- Dependency compatibility.
- WordPress/WooCommerce ecosystem expectations.
- Whether a `NOTICE` file is needed.
- Whether plugin headers should include license metadata.

## 5. GitHub publication plan

Preferred approach:

```bash
git remote add github git@github.com:YOUR_USER_OR_ORG/euroledger-xrpl.git
git push github main
git push github --tags
```

This avoids exposing the local Gitea instance.

After pushing:

- Create GitHub release for `woocommerce-gateway-v0.1.3`.
- Upload ZIP and SHA256 assets.
- Paste the public release notes.
- Review repository visibility and secrets one last time.
