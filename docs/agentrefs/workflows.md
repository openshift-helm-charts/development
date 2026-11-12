# Workflows

All paths below are repository-root-relative unless noted otherwise.

GitHub Actions for development work as well as GitHub Actions for the certification pipeline live in `.github/`:

- `.github/workflows/` - the repository workflows (submission handling, testing, release, metrics, code scanning). Some of these are disabled by design, as they only apply in production repositories.
- `.github/actions/` - reusable composite actions, utilized by various workflows mentioned above.

Not all workflows from this repository are pushed to production. This is controlled via `release/release_info.json`.

## Conventions

- Certification workflows that check out contributed content (e.g. submission tests) gate on approved actors; preserve those gates when editing.
- Several workflows are `workflow_call`-based (e.g. `behave.yml`) and are invoked from other workflows - check callers before changing their inputs.
- Some workflows (e.g. `build.yml` and `owners-redhat.yml`) run against pull-request targets on the charts repository and must have their event trigger changed on release; the release process edits them via `release/release_info.json` (see [Release process](release-process.md)).

## Key workflows

| Workflow | Purpose |
| --- | --- |
| `build.yml` | Main chart submission workflow (partner/redhat/community paths) |
| `release.yml` | Drives the cross-repository release process |
| `test.yml` | Sandbox-based certification tests, triggered by pull requests |
| `nightly_test.yml` | Sandbox-based certification tests, run on a schedule |
| `behave.yml` | Runs the Behave suites (see [Functional tests](functional-tests.md)) |
| `python-style.yml`, `python-test.yml` | Lint and unit-test `scripts/src` |
| `check-contributor.yml`, `check-locks-on-owners-submission.yml`, `lock-sanity-check.yml` | Submission hygiene checks |
| `owners.yml`, `owners-redhat.yml` | Partner/Red Hat OWNERS-file verification |
| `mercury_bot.yml`, `metrics.yml`, `test-cluster-access.yml`, `test-smoke-on-label.yml` | Bot, metrics, and smoke tests |

## Validation

- Workflow changes are exercised end-to-end by the sandbox tests described in [Functional tests](functional-tests.md).
- Only PRs by owners defined in [OWNERS](../../OWNERS) will trigger workflows. This gate is implemented as a Job or Step in relevant workflows.

## Cautions

- Do not rename workflows referenced by `release/release_info.json` (`release.yml`, `nightly_test.yml`, `metrics.yml`, `codeql.yml`, `python-test.yml`, `test-smoke-on-label.yml`) without updating the release configuration. The `release_info.json` file can be changed. So long as the semantic version is not changed outside of a release, release automation does not execute.
- Composite actions under `.github/actions/` are consumed by workflows in this repository and in the charts/stage repositories after release; keep their inputs/outputs backwards compatible.
