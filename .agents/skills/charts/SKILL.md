---
name: charts
description: Develop, test, and release the chart submission workflows and scripts for the openshift-helm-charts/charts product repository, working in the openshift-helm-charts/development repository. Use when the user mentions a GitHub workflow under .github/workflows (build.yml, test.yml, behave.yml, nightly_test.yml), the Python automation under scripts/src, ruff or black, the behave BDD tests or the sandbox repository, an OWNERS approver, or the release process (release_info.json merges/replaces/ignores).
license: Apache-2.0
---

# Charts product repository

The product repository is [openshift-helm-charts/charts](https://github.com/openshift-helm-charts/charts).
Its chart submission workflows and scripts are developed and tested in the
`openshift-helm-charts/development` repository before being released into the
charts and [stage](https://github.com/openshift-helm-charts/stage) repositories.

## Safety rules

- Never mix chart-related and non-chart changes in the same pull request; a PR
  must be entirely one or the other. Charts enter this repository only through
  the automated release process.
- Pushing a branch and opening a pull request are outward-facing actions:
  confirm with the user first.
- Never print, copy, or transmit cluster tokens, `BOT_TOKEN` values, or other
  repository secrets. Describe credential errors without exposing values.
- Do not run scripts or workflows that need a live cluster or registry
  credentials unless the user explicitly agrees.

## Procedure

### 1. Locate the change

- GitHub workflows: `.github/workflows/` (chart submission, release, and test
  workflows, e.g. `build.yml`, `behave.yml`).
- Automation code: `scripts/src/` (Python), configured by `scripts/pyproject.toml`
  and linted with `ruff`.
- BDD tests that exercise chart submission against the sandbox repository:
  `tests/`.

### 2. Make the change

Branch off `main`. Keep the change non-chart and focused on one concern.

### 3. Check the code style

Run from the `scripts/` directory:

```sh
make format lint
```

`make ci.format` is the CI variant; it fails if the formatter had to change
anything. Fix any reported issues before submitting.

### 4. Test in a fork

Workflow and script changes should be exercised against a fork before they are
submitted. The bot account, cluster, and secrets setup is described in
[references/fork-testing.md](references/fork-testing.md).

### 5. Submit the pull request

Before submitting, confirm the user is listed under `approver` in the
repository's `OWNERS` file — CI rejects workflow, script, and test PRs from
anyone else. Open a PR against `openshift-helm-charts/development` containing
only the non-chart change. Never include chart content (`charts/`) in the same
PR.

**Done when** the PR contains only the non-chart change, the `python-style`
and `python-test` checks pass, and the BDD tests against the sandbox
repository triggered by the PR are green.

### 6. Release

Changes reach the charts and stage repositories through the automated release
process, not by direct commits there. See
[references/release-process.md](references/release-process.md).
