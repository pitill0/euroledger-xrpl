# EuroLedger XRPL — License and Publication Review v1

This review captures the current licensing and publication-readiness state before publishing the repository outside the local Gitea environment.

This is a project-maintenance checklist, not legal advice.

## Current findings

### License

The repository currently uses Apache License 2.0.

Observed state:

```text
LICENSE
Apache License
Version 2.0, January 2004
```

The root `LICENSE` file also includes the standard Apache 2.0 boilerplate notice:

```text
Copyright 2026 EuroLedger XRPL contributors

Licensed under the Apache License, Version 2.0 (the "License");
```

Recommendation:

```text
Keep Apache-2.0 as the project license.
```

Rationale:

- It matches the license decision already present in the repository.
- It is permissive and suitable for a backend/API project.
- It includes an explicit patent grant.
- It is compatible with commercial and public-sector adoption.
- It does not force downstream users to publish their modifications.

### NOTICE file

No `NOTICE` or `NOTICE.md` file is currently present.

Observed state:

```text
./LICENSE
```

Recommendation:

```text
Do not add a NOTICE file yet unless the project needs to preserve explicit third-party attribution notices or project-level trademark/attribution statements.
```

Rationale:

- Apache 2.0 only creates special NOTICE redistribution obligations if the project includes a NOTICE file.
- Adding a NOTICE file unnecessarily increases downstream redistribution requirements.
- A NOTICE file can be added later if the project needs formal attribution notices.

### WordPress/WooCommerce plugin header

Current observed metadata:

```text
Version: 0.1.3
License: Apache-2.0
Text Domain: euroledger-xrpl-gateway
```

Recommended small improvement:

```php
 * License URI: https://www.apache.org/licenses/LICENSE-2.0
```

Suggested header shape:

```php
/**
 * Plugin Name: EuroLedger XRPL Gateway
 * Description: Accept EuroLedger XRPL payments in WooCommerce.
 * Version: 0.1.3
 * Author: EuroLedger XRPL contributors
 * License: Apache-2.0
 * License URI: https://www.apache.org/licenses/LICENSE-2.0
 * Text Domain: euroledger-xrpl-gateway
 */
```

Only add fields that are consistent with the current plugin header. Do not invent URLs or author metadata beyond what the project is ready to publish.

### Environment files

Observed files:

```text
./.env
./.env.example
./LICENSE
```

Recommendation:

```text
Keep .env.example.
Do not publish .env.
Ensure .env is ignored.
```

Before publication, run:

```bash
git check-ignore -v .env
git ls-files .env
```

Expected:

```text
git check-ignore -v .env
→ should show the .gitignore rule

git ls-files .env
→ should return no output
```

If `.env` is tracked, stop and remove it from Git before publishing.

### Internal roadmap

The repository contains:

```text
docs/internal/roadmap.md
```

Recommendation:

```text
Review docs/internal/roadmap.md before publishing.
```

Decision needed:

```text
A) Keep it public if it contains no sensitive/internal strategy.
B) Sanitize it and keep a public roadmap.
C) Remove it from the public repo and keep it private.
```

### Versioning docs

Observed reference:

```text
docs/woocommerce-plugin-versioning.md: Version: 0.1.0
```

Recommendation:

```text
Review whether this is an example snippet or stale version text.
```

If it is an example, label it clearly as an example.

If it is intended to represent the current version, update it to `0.1.3`.

### Release artifacts

`dist/` is ignored and should remain ignored.

Local release assets are acceptable outside Git:

```text
dist/euroledger-xrpl-gateway-0.1.3.zip
dist/euroledger-xrpl-gateway-0.1.3.zip.sha256
```

Recommendation:

```text
Do not commit dist/.
Upload release ZIP and checksum as GitHub/Gitea release assets.
```

### Empty placeholder directories

The repository currently has placeholder directories:

```text
sdk/.gitkeep
tests/.gitkeep
worker/.gitkeep
```

Recommendation:

```text
Decide before public release whether these directories are part of the public roadmap.
```

Options:

```text
A) Keep them with README.md files explaining planned purpose.
B) Remove them until they contain real code.
```

For a polished public repo, empty directories with only `.gitkeep` can make the project look unfinished.

## Suggested immediate changes

### 1. Add License URI to the WooCommerce plugin header

File:

```text
plugin-woocommerce/euroledger-xrpl-gateway/euroledger-xrpl-gateway.php
```

Add:

```php
 * License URI: https://www.apache.org/licenses/LICENSE-2.0
```

near the existing `License: Apache-2.0` header line.

### 2. Add this review document

File:

```text
docs/license-and-publication-review.md
```

### 3. Optionally update publication readiness plan

Review:

```text
docs/publication-readiness-plan.md
```

Make sure it references this review document after it is committed.

## Pre-publication checks

Run before publishing:

```bash
git status --short

git ls-files | grep -Ei '(__pycache__|\.pyc$|\.zip$|^dist/|\.env$|secrets/)'

git check-ignore -v .env
git ls-files .env

find . -type d -name "__pycache__" -o -type f -name "*.pyc" | sort | head -20

find . -maxdepth 3 -type f -name "*.zip" -o -path "./dist/*" | sort
```

Expected:

```text
git status --short
→ clean

git ls-files ...
→ no secrets, pycache, zip, dist, .env, or secrets output

git check-ignore -v .env
→ shows ignore rule

git ls-files .env
→ no output
```

## GitHub publication strategy

Preferred publication approach:

```bash
git remote add github git@github.com:YOUR_USER_OR_ORG/euroledger-xrpl.git
git push github main
git push github --tags
```

This avoids exposing the local Gitea instance.

After pushing:

1. Create the GitHub repository.
2. Push `main`.
3. Push tags.
4. Create a release for `woocommerce-gateway-v0.1.3`.
5. Upload:
   - `euroledger-xrpl-gateway-0.1.3.zip`
   - `euroledger-xrpl-gateway-0.1.3.zip.sha256`
6. Paste the public release notes from:
   - `docs/releases/woocommerce-gateway-0.1.3-public.md`

## Recommendation summary

Current state is good for publication after minor cleanup.

Recommended before publishing:

```text
- Keep Apache-2.0.
- Do not add NOTICE yet.
- Add License URI to WooCommerce plugin header.
- Verify .env is ignored and untracked.
- Review or sanitize docs/internal/roadmap.md.
- Decide whether sdk/, tests/, and worker/ placeholders should remain.
- Verify no ignored artifacts are tracked.
- Publish to GitHub by adding a remote and pushing from local Git.
```
