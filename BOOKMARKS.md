# Bookmarks

Curated references for task-specific context. Use the descriptions to decide what to load; these references are not intended to be read all at once. Paths are relative to the repository root.

## Architecture and behavior

- [Workflows](docs/agentrefs/workflows.md) - GitHub workflows and composite actions in `.github/`, actor gates, reusable workflow contracts, and release coupling. Read when changing certification automation.

## Development and testing

- [CI scripts (Python)](docs/agentrefs/scripts.md) - the `scripts/` layout, setup, formatting, linting, and compatibility constraints. Read when modifying CI scripts or infrastructure configuration.
- [Functional tests (Python)](docs/agentrefs/functional-tests.md) - Behave suites in `tests/`, scenario and fixture conventions, approver gates, and sandbox side effects. Read when changing tests or validating workflow changes.

## Release and submission contracts

- [Release process](docs/agentrefs/release-process.md) - `release/release_info.json`, cross-repository synchronization, and merge/replace/edit/ignore semantics. Read before changing release metadata or paths referenced by the release process. Use local skill **prepare-helm-cert-release** if needed.
- [Submission guide](docs/README.md) - user-facing chart/report submission requirements and troubleshooting. Read when changing submission behavior or documentation.
- [Pull request rules and fork-based testing](docs/pull-request.md) - PR content restrictions, authorization metadata, and fork-testing prerequisites. Read when changing PR handling or setting up workflow tests in a fork.
