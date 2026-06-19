# Continuous Integration

This project uses Gitea Actions for continuous integration.

The CI workflow is defined in:

```text
.gitea/workflows/backend-ci.yml
```

## Current Checks

The current backend workflow validates:

- backend dependency installation;
- Ruff linting;
- Ruff formatting;
- Pytest test suite.

These checks run on every push to `main` and on pull requests.

## Known Warnings

At this stage, the backend test suite may show the following warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.

This warning comes from the FastAPI/Starlette test client dependency chain, not from EuroLedger XRPL application code.

The current test suite still passes successfully, so this warning is accepted temporarily while the project remains in early development.

A future maintenance task should review the recommended FastAPI/Starlette testing stack and decide whether to migrate to httpx2, adjust dependency versions or replace TestClient usage with another ASGI testing approach.
```


## Workflow Scope

The current CI scope is intentionally small.

At this stage, the goal is to validate the backend code quality before adding more complex checks involving PostgreSQL, Alembic migrations, XRPL Testnet flows or background workers.

## Local Runner

The workflow is executed by a self-hosted Gitea runner.

The runner is expected to provide a container-based execution environment compatible with Gitea Actions.

For local development, the runner may be executed on a trusted local machine using Podman.

## Runner Image

The current runner label should point to an image that includes:

- Python 3.12;
- Node.js;
- Git;
- basic CA certificates and shell utilities.

Node.js is required because some Gitea/GitHub-compatible actions, such as checkout actions, are JavaScript actions.

Python 3.12 is required because the backend package declares:

```toml
requires-python = ">=3.12"
```

A local custom image can be used for this purpose, for example:

```text
localhost/euroledger-ci-python-node:3.12
```

The exact image name is local infrastructure detail and may change depending on the runner environment.

## Runner Labels

The workflow currently uses:

```yaml
runs-on: ubuntu-latest
```

The self-hosted runner must provide a compatible label for `ubuntu-latest`.

In a local Podman-based setup, that label may map to a custom container image with Python, Node.js and Git installed.

## Security Notes

Self-hosted runners should only be used with trusted repositories and trusted workflows.

A runner with access to a container runtime socket can potentially control containers on the host machine. Do not expose this runner to untrusted repositories or unreviewed external pull requests.

Registration tokens, runner state files, local socket paths and machine-specific configuration must not be committed to this repository.

## Future Improvements

Planned CI improvements include:

- Docker/Podman image build validation;
- Compose configuration validation;
- Alembic migration checks;
- PostgreSQL-backed integration tests;
- payment intent lifecycle tests;
- XRPL Testnet worker tests;
- reconciliation export tests.

