# Repository Agent Guide

## Purpose

This repository is used to develop and test the workflows and scripts that drive Helm chart certification for the OpenShift Helm Charts repositories. Certification DOES NOT occur in this repository.

## Working in This Repository

The major components of this repository are:
- GitHub Actions Workflows: Workflows and composite actions drive the primary production workflow for Helm chart certification submissions. See [Workflows](docs/agentrefs/workflows.md) for guidance on developing and modifying workflows.
- CI scripts, implemented in Python, which implement the core logic of the GitHub Actions workflows. See [Python scripts](docs/agentrefs/scripts.md) for `scripts/` setup, formatting, linting, and `make` targets.
- Behavioral tests, ensuring The GitHub Actions and CI scripts function correctly. See [Functional tests](docs/agentrefs/functional-tests.md) for how Python tests and Behave suites run through the workflows in `.github/workflows/`.

## Repository-Wide Constraints

- You MUST prompt the user for approval prior to initiating workflows (e.g. via workflow_dispatch) on the repository.
- You SHOULD ask the user their policy on using git to push content to the repository. If multiple remotes exist, be clear as to which remote you should push.
- You MUST NOT modify content in `charts/`. These are a snapshot of the submitted content in production. None of this content is submitted to this repository.
- Pull requests that touch `.github/workflows/`, `scripts/src/`, or `tests/` require the author be listed in the top-level `OWNERS` file, and trigger the automated sandbox tests once authorized.

## Task-Specific Context

- Before task-specific code or design work, consult [BOOKMARKS.md](BOOKMARKS.md). It is the curated, on-demand index for workflow, development, testing, release, and submission references. Load only entries relevant to the task rather than duplicating their details here.
