# Functional Tests

All paths below are repository-root-relative unless noted otherwise.

Behavior-driven (Behave) functional tests that exercise the chart submission workflows end-to-end against the [sandbox repository](https://github.com/openshift-helm-charts/sandbox).

Layout:

- `tests/functional/behave_features/` - Gherkin `.feature` files (one per scenario family, `HC-01` … `HC-20`), plus `environment.py`, `steps/`, and `common/`
- `tests/data/` - sample charts and reports used as fixtures by the features

## What the tests do

Two suites, both implemented by workflows in [`.github/`](../../.github/):

- **PR-triggered tests** (`test.yml`, on `pull_request_target`): for PRs touching `.github/workflows/`, `scripts/src/`, or `tests/` from an approver listed in `OWNERS`, runs Behave with the `smoke` tags (the `full` set on charts release PRs), creating branches/releases in the sandbox, running the submission flow, and cleaning up afterwards.
- **Nightly tests** (`nightly_test.yml`, on a schedule): runs the `full` Behave suite.

## Conventions

- Each feature file groups the scenarios for one submission-situation family (`HC-01` … `HC-20`); many files contain several scenarios. Fixtures live under `tests/data/` and are referenced by name from the features and steps.
- Feature files are dispatched individually by `.github/workflows/behave.yml` (a `workflow_call` workflow taking `tags` and `pr-body` inputs). This is to allow for concurrency in the GitHub Actions workflow.

## Validation

Pull requests to this repository trigger Behave tests. Behave testing creates artifacts in the sandbox configured in [settings.py](../../tests/functional/behave_features/common/utils/setttings.py). There is no supported local-only run because the suites create real PRs in an actual repository. When adding a feature:

1. Add the `.feature` file under `tests/functional/behave_features/`.
2. Add or reuse fixtures under `tests/data/`. Call out fixture reuse.
3. Implement or extend steps in `tests/functional/behave_features/steps/`.
4. Rely on the CI run of `behave.yml`/`test.yml` to validate.

## Cautions

- Tests perform real GitHub operations (PRs, releases, cleanup) in the sandbox repository - do not point them at production repositories.
- `tests/data/` contains intentionally broken charts and reports (invalid URLs, failing checks, timeouts); do not "fix" them.
