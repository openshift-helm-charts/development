# Release Process

All paths below are repository-root-relative unless noted otherwise.

`release/release_info.json` is the single file that drives the cross-repository release process (see the repository [README.md](../../README.md) for the full narrative).

A local skill exists for the preparation of release assets. prepare-helm-cert-release.

## How it works

A release is started by modifying `release/release_info.json` alone in a PR against the development repository. The workflow at `.github/workflows/release.yml` then:

1. Clones the development, charts, and stage repositories.
2. Applies each repository's `merge`, `replace`, and `ignore` directives from `release_info.json`.
3. Opens PRs against the charts and stage repositories (merged manually after their tests pass) and a PR back into development with chart updates.
4. Auto-merges the `release_info.json` PR and creates the release.

## Conventions

- **A release PR contains only changes to `release_info.json`.**
- Directive semantics:
  - `merge` - overlay this directory/file onto the same path in the target repository.
  - `replace` - delete the path in the target repository and copy this repository's version in.
  - `edit` - run a named, predefined edit function against a file already present in the target repository. Unlike the other directives, this is an object mapping path → function name rather than a list of paths.
  - `ignore` - exclude specific paths that were part of a merge/replace.
- Directives are applied in a fixed order: `replace`, `edit`, `merge`, then `ignore`. `edit` acts on files placed by `replace`, and `ignore` deletes last regardless of which directive introduced the path.
- Version the release in the `version` field and describe content in `info`.

## Cautions

- There are two `ignore` lists under `development`, one per target repository, and they are not identical. Both pin development-only files that must not be copied out: `.github/workflows/release.yml`, `.github/workflows/nightly_test.yml`, `.github/workflows/metrics.yml`, `.github/workflows/codeql.yml`, `.github/workflows/python-test.yml`, `.github/workflows/test-smoke-on-label.yml`, and `.github/dependabot.yml`. The `stage` list additionally pins `.github/workflows/owners.yml` and `.github/workflows/check-locks-on-owners-submission.yml`. Renaming any of those files requires updating both lists in the same change.
- `edit` values resolve through the `EDIT_FUNCTIONS` allowlist in `scripts/src/release/releaser.py`. Only `switch_workflow_to_pull_request_target` is permitted today, and an unrecognized name fails the release. Adding a new edit function requires a code change alongside the `release_info.json` update.
- Mistakes in release directives propagate to three repositories at once - keep directives minimal and review path lists carefully.
