PY_BIN ?= python3

# The virtualenv containing code style tools.
VENV_CODESTYLE = venv.codestyle
VENV_CODESTYLE_BIN = $(VENV_CODESTYLE)/bin

# The virtualenv containing our CI scripts
VENV_TOOLS = venv.tools
VENV_TOOLS_BIN = $(VENV_TOOLS)/bin

# The virtualenv containing the uv-managed lint tools. It is deliberately NOT
# the project environment: `uv sync` is exact, so syncing --only-group lint
# into the shared env would prune the project and its test dependencies back
# out of it, breaking an env that `make install` had just populated.
# Matched by the `venv.*/` rule in .gitignore.
VENV_LINT ?= venv.lint
UV_LINT_ENV = UV_PROJECT_ENVIRONMENT=$(VENV_LINT)

# This is what we pass to git ls-files.
LS_FILES_INPUT_STR ?= 'src/*.py'

.PHONY: default
default: format lint

# Install the project and its test dependencies.
# CI sets UV_PROJECT_ENVIRONMENT=$(GITHUB_WORKSPACE)/ve1 so that the existing
# `ve1/bin/<command>` invocations keep working unchanged. Locally, with that
# variable unset, uv builds scripts/.venv instead.
.PHONY: install
install:
	uv sync --locked --group test

# Install ONLY black and ruff -- not the project, not its runtime deps.
# This reproduces what venv.codestyle gave us: a minimal, isolated lint env.
.PHONY: install.lint
install.lint:
	$(UV_LINT_ENV) uv sync --locked --only-group lint

# The same as format, but will throw a non-zero exit code
# if the formatter had to make changes.
.PHONY: ci.format
ci.format: format
	git diff --exit-code

# --- Retained for one release; removed in a follow-up PR. ---
# Nothing in CI calls these any more. They are kept so this change can be
# reverted cleanly, and for anyone with the muscle memory.

venv.codestyle:
	$(MAKE) venv.codestyle.always-reinstall

# This target will always install the codestyle venv.
# Useful for development cases.
.PHONY: venv.codestyle.always-reinstall
venv.codestyle.always-reinstall:
	$(PY_BIN) -m venv $(VENV_CODESTYLE)
	./$(VENV_CODESTYLE_BIN)/pip install --upgrade \
		black \
		ruff

.PHONY: format
format: install.lint
	$(UV_LINT_ENV) uv run --only-group lint black \
		--verbose \
		$$(git ls-files $(LS_FILES_INPUT_STR))

.PHONY: lint
lint: install.lint
	$(UV_LINT_ENV) uv run --only-group lint ruff \
		check \
		$$(git ls-files $(LS_FILES_INPUT_STR))

venv.tools:
	$(MAKE) venv.tools.always-reinstall

# This target will always install the tools at the venv.
# Useful for development cases.
.PHONY: venv.tools.always-reinstall
venv.tools.always-reinstall:
	$(PY_BIN) -m venv $(VENV_TOOLS)
	./$(VENV_TOOLS_BIN)/pip install .
