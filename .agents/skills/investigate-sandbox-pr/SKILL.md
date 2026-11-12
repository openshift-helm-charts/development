---
name: investigate-sandbox-pr
description: Investigate a single sandbox PR failure. Fetches PR details and its workflow log, classifies the root cause, and returns structured findings.
compatibility: Requires authenticated GitHub CLI. Read-only access should be sufficient.
---

# Investigating a single pull request to the sandbox.

You investigate a single PR in a sandbox repository to determine why its CI workflow failed.

## Tools

Use `gh` CLI to interact with GitHub. STOP and prompt the user if `gh` is not found or is not authenticated.
Text search is demonstrated using ripgrep (`rg`) throughout. If ripgrep is unavailable, fall back to grep. Examples may need to be adjusted.

## Inputs

You receive these values from the caller:

- **PR number** - the sandbox PR to investigate
- **Sandbox repo** - e.g. `openshift-helm-charts/sandbox-2025-11`
- **Workflow run ID** (optional) - if known; otherwise extract from the PR's status checks

## Process

### 1. Fetch PR details

```bash
gh pr view <PR> --repo <sandbox-repo> --json number,title,state,url,statusCheckRollup
```

### 2. Resolve the workflow run ID

If no run ID was provided, extract it from the `statusCheckRollup` field - look for check runs with a `detailsUrl` containing `/actions/runs/`.

### 3. Fetch the sandbox workflow log

Redirect to a temp file - never read full logs into context:

```bash
gh run view <runID> --repo <sandbox-repo> --log-failed > <tmpdir>/sandbox-run-<runID>.txt 2>&1
```

### 4. Search for root cause patterns

Search the temp file:

```bash
rg -i "resource not accessible|403|401|token expired|permission" <tmpdir>/sandbox-run-<runID>.txt
rg -i "timed out|timeout" <tmpdir>/sandbox-run-<runID>.txt
rg -i "404|not found|unable to compute SHA256" <tmpdir>/sandbox-run-<runID>.txt
rg -i "error|exception|traceback|failed" <tmpdir>/sandbox-run-<runID>.txt
```

### 5. Classify the failure

Assign one of these categories based on the evidence:

| Category | Typical symptoms |
|---|---|
| **No workflow ran** | Empty log or no check runs on the PR |
| **Auth / credential error** | 403, 401, "token expired", "Resource not accessible" |
| **Timeout** | "timed out", "timeout", context deadline exceeded |
| **Chart verification failure** | Chart lint/template errors, schema validation failures |
| **CDN propagation** | 404 on release assets, "unable to compute SHA256 digest" |
| **Infrastructure** | Runner failures, OOM, disk full, network errors |
| **Unknown** | None of the above patterns matched |

### 6. Return structured results

Return to the caller:

- **PR link** - URL to the sandbox PR
- **Workflow run link** - `https://github.com/<sandbox-repo>/actions/runs/<runID>`
- **Failure category** - one of the categories above
- **Root cause summary** - 1-2 sentence explanation
- **Log snippets** - the most relevant error lines (max 15 lines)
- **Remediation** - what to do about it

### 7. Clean up

```bash
rm -f <tmpdir>/sandbox-run-<runID>.txt
```
