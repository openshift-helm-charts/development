# Python Scripts

All paths below are repository-root-relative unless noted otherwise.

Python source for the CI scripts invoked by the workflows in [`.github/`](../../.github/). Layout:

- `scripts/src/` - Python packages implementing certification logic, called in GitHub Actions workflows.

## Setup and validation

Everything runs through `scripts/Makefile` using two virtualenvs in `scripts/`: `venv.codestyle` (Black and Ruff, used by `format`/`lint`) and `venv.tools` (the CI scripts package, built from `scripts/requirements.txt` plus the package itself). Run these commands from `scripts/`:

```bash
make venv.tools # Installs CI scripts to venv.tools. Append .always-reinstall after making changes.
make format     # Installs dependencies before running style tools
make lint       # Installs dependencies before running lint tools
```

Code style is checked with Ruff (configured in `scripts/ruff.toml`); run `make format` before submitting.

Unit tests for `scripts/src/` run with pytest. To run them locally, install the tools virtualenv (`make venv.tools` from `scripts/`) and run pytest from it:

```bash
./venv.tools/bin/pytest src/
```

## Conventions

- CI logic in `scripts/` is released into the charts and stage repositories - keep public interfaces (entry points, function signatures used by workflows) backwards compatible where practical.

## Cautions

- Changes to `scripts/src/` trigger the sandbox-based Behave tests on PRs from approvers (see [Functional tests](functional-tests.md)).
- See [Python tooling README](../../scripts/README.md) for cluster token/secret management (`scripts/get-secrets`) - never commit credentials.
