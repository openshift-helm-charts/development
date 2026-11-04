---
name: analyze-ci-logs
description: Analyze one failed parent Helm certification E2E GitHub Actions job. Find unexpected assertions and setup/teardown errors, distinguish expected negative-path sandbox failures, correlate scenario PR/run IDs, and investigate or hand off affected sandbox PRs. Use for a single job, or as a troubleshoot-e2e-run helper.
compatibility: Requires authenticated GitHub CLI, GitHub network access, local temporary-file access, and a text search tool like ripgrep. Read-only access should be sufficient. Sandbox follow-up uses the companion investigate-sandbox-pr skill.
---

You analyze the failed log for a single CI job, extract failure details, and call local skill **investigate-sandbox-pr** for each affected pull request.

## Tools

Use `gh` CLI to interact with GitHub. STOP and prompt the user if `gh` is not found or is not authenticated.
Text search is demonstrated using ripgrep (`rg`) throughout. If ripgrep is unavailable, fall back to grep. Examples may need to be adjusted.

## Inputs

You receive these values from the caller:

- **Job ID** - the GitHub Actions job ID to analyze
- **Source repo** - the repo that owns the workflow (e.g. `openshift-helm-charts/development`)
- **Sandbox repo** - the sandbox repo where test PRs are created (e.g. `openshift-helm-charts/sandbox-2025-11`)
- **Run ID** - the parent workflow run ID (for constructing links)

## Process

### 1. Fetch the job log

Redirect to a temp file - never read full logs into context:

```bash
gh run view --repo <source-repo> --job <jobID> --log-failed > <tmpdir>/job-<jobID>.txt 2>&1
```

### 2. Search for ASSERT failures

```bash
rg -i "ASSERT" <tmpdir>/job-<jobID>.txt 2>/dev/null || grep -i "ASSERT" <tmpdir>/job-<jobID>.txt
```

### 3. Extract PR numbers and run IDs

PR numbers appear in patterns like `PR: 123`, `PR123`, `PR 123`, or `PRxxxx`:

```bash
rg -oP "PR:?\s*(\d+)" <tmpdir>/job-<jobID>.txt | rg -oP "\d+" | sort -u
```

Run IDs appear in patterns like `run id: 12345` or `Workflow 12345`:

```bash
rg -oiP "(run id:?\s*|Workflow\s+)(\d+)" <tmpdir>/job-<jobID>.txt | rg -oP "\d+" | sort -u
```

### 4. Pair PRs with run IDs

Match each PR number to its associated run ID from nearby log context. If a PR has no associated run ID, pass it to the sandbox investigator without one - the investigator will resolve it from the PR's status checks.

### 5. Spawn sandbox investigators

For each PR/run pair, call local skill **investigate-sandbox-pr** in a subagent.

- Pass: PR number, sandbox repo, workflow run ID (if known)
- Collect the structured results from each investigator

If necessary, spawn these in parallel.

### 6. Handle non-ASSERT failures

If no ASSERT lines are found, search for other error patterns:

```bash
rg -i "exception|traceback" <tmpdir>/job-<jobID>.txt | head -20
rg -i "timeout|timed out" <tmpdir>/job-<jobID>.txt | head -10
rg -E "(4[0-9]{2}|5[0-9]{2})" <tmpdir>/job-<jobID>.txt | head -10
```

Summarize any errors found - these don't spawn investigators but should be included in the results.

### 7. Return structured results

Return to the caller:

- **Feature name** - the test feature file name (from the job name)
- **Job link** - `https://github.com/<source-repo>/actions/runs/<runID>/job/<jobID>`
- **Per-PR results** - array of results from sandbox investigators
- **Other errors** - any non-ASSERT errors found (if applicable)

If no errors can be identified, inform the user that you are unsure of what caused this failure.

### 8. Clean up

```bash
rm -f <tmpdir>/job-<jobID>.txt
```
