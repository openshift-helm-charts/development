---
name: troubleshoot-e2e-run
description: Facilitates the investigation of E2E test failures. Identifies the failed jobs, spawns investigative agents to parse the failed logs, evaluate GitHub API availability, and produces a report of findings.
compatibility: Requires authenticated GitHub CLI. Read-only access should be sufficient.
---

# Troubleshooting E2E Run Failures

You coordinate the investigation of a failed GitHub Actions workflow run by dispatching subagents to analyze individual job logs and sandbox PR failures. You have subagents at your disposal to analyze failure logs, investigate test pull requests in the sandbox repository, and investigate/correlate GitHub service outages.

## Tools

Use `gh` CLI to interact with GitHub. STOP and prompt the user if `gh` is not found or is not authenticated.
Text search is demonstrated using ripgrep (`rg`) throughout. If ripgrep is unavailable, fall back to grep. Examples may need to be adjusted.

## Process

### 1. Extract repo and run ID

From the provided URL (e.g. `https://github.com/org/repo/actions/runs/12345`), extract:
- **Repository**: `owner/repo`
- **Run ID**: numeric ID

### 2. Fetch the workflow summary

Fetch the summary only - do **not** use `--log-failed` at this level:

```bash
gh run view <runID> --repo <repo>
```

### 3. Read the sandbox repo name

For example:

```bash
rg "^TEST_REPO" tests/functional/behave_features/common/utils/setttings.py 2>/dev/null || grep "^TEST_REPO" tests/functional/behave_features/common/utils/setttings.py
```

Extract the value (e.g. `openshift-helm-charts/sandbox-2025-11`).

### 4. Identify failed jobs

Parse the summary output. Lines starting with `X` indicate failed jobs. Extract:
- **Job name** - the feature file / test name
- **Job ID** - numeric ID

Skip these non-investigable jobs:
- `get-features`
- `Communicate Outcome`

### 5. Spawn log analyzers

In subagents, call the local skill **analyze-ci-logs** for each failed job, providing it the following data:
- Job ID
- Source repo
- Sandbox repo
- Run ID

### 6. Check for GitHub service outages

Call local skill **check-github-status** in a subagent to check for GitHub infrastructure outages during the test timeframe.

**Inputs:** Provide the workflow's start time and end time (extract from `gh run view <runID> --repo <repo> --json startedAt,updatedAt`).

**Outputs:** Returns matching GitHub status incidents (with impact, affected services, and correlation) or a message that none were found.

Include the subagent's findings in your report. The subagent filters to incidents that overlap the timeframe - it will not return outages resolved hours before the CI failure, so trust its correlation assessment.

### 7. Report Format

using the [failure report template](assets/e2e-test-failure-report-TEMPLATE.md), write the final report to the current working directory using a descriptive filename (e.g., `e2e-test-failure-report-<runID>.md`).

