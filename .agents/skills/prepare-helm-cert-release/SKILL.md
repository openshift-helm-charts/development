---
name: prepare-helm-cert-release
description: Prepare a release PR for openshift-helm-charts/development by generating changelog from merged PRs, inferring semantic version, and updating release_info.json.
compatibility: Requires authenticated GitHub CLI. Read-only access should be sufficient.
---

You are preparing a release for the openshift-helm-charts/development repository.

# Objective

Create a release by:
1. Working in a git worktree (unless user explicitly requests otherwise)
2. Determining the next semantic version based on merged PRs since the last release
3. Generating a changelog from those PRs
4. Updating `release/release_info.json` with the new version and changelog
5. Creating a branch with the changes ready for the user to review, commit, and push

# Constraints

- **Do NOT commit**: Only prepare the changes
- **Do NOT push**: User handles this
- **Do NOT create a PR**: User will do this after pushing
- **Use worktree by default**: Unless user explicitly says otherwise
- **Confirm version**: Always ask user to confirm the inferred semantic version

# Tools

Use `gh` CLI to interact with GitHub. STOP and prompt the user if `gh` is not found or is not authenticated.
Text search is demonstrated using ripgrep (`rg`) throughout. If ripgrep is unavailable, fall back to grep. Examples may need to be adjusted.

# Process

## 1. Determine Current State

Read `<repo_root>release/release_info.json` to get the current version.

Query the latest release tag:
```bash
gh release list --repo openshift-helm-charts/development --limit 1 --json tagName,publishedAt
```

## 2. Get Merged PRs Since Last Release

Query merged PRs since the last release date:
```bash
gh pr list --repo openshift-helm-charts/development \
  --state merged \
  --limit 100 \
  --json number,title,author,mergedAt,labels \
  --search "merged:>YYYY-MM-DD"
```

Replace `YYYY-MM-DD` with the date from the last release.

## 3. Infer Semantic Version

Unless provided by the user, analyze PR titles and labels to infer the version bump:

- **MAJOR** (X.0.0): HALT - the human should execute major version changes
- **MINOR** (x.Y.0): New features, enhancements, dependencies updates
  - Labels: `enhancement`, `feature`, `dependencies`, `minor`
  - Title keywords: `feat:`, `feature`, `add`, `new`, most dependency bumps
- **PATCH** (x.y.Z): Bug fixes, docs, tests, small improvements
  - Labels: `bug`, `bugfix`, `fix`, `documentation`, `patch`
  - Title keywords: `fix:`, `bug`, `patch`, `docs`

Present the inferred version to the user with reasoning. Ask them to confirm or provide an alternate version.

## 4. Generate Changelog

Format merged PRs into changelog entries matching this pattern:
```
"<PR title> (#<number>) by @<author>"
```

Example:
```
"Bump the core-scripts group across 1 directory with 5 updates (#533) by @dependabot[bot]"
```

Sort entries:
1. Breaking changes first
2. Features/enhancements
3. Bug fixes
4. Dependencies/internal changes
5. Documentation

## 5. Create Worktree and Update release_info.json

Unless explicitly told otherwise, work in a worktree:

```bash
git worktree add <tmpdir>/release-<version> -b release-<version>
```

In the worktree, update `release/release_info.json`:
- Change `"version"` field to the new version
- Replace the `"info"` array with the new changelog entries
- Keep all other fields unchanged

## 6. Present Changes

Show the user:
- The branch name: `release-<version>`
- The worktree location
- A diff of the changes to `release/release_info.json`
- Next steps: review, commit with message "Release <version>.", and push

Do NOT commit or push. The user will do this manually.

# Example Workflow

```bash
# 1. Get current version
cat release/release_info.json | jq -r '.version'
# Output: 1.9.6

# 2. Get last release date
gh release view 1.9.6 --repo openshift-helm-charts/development --json publishedAt -q '.publishedAt'
# Output: 2026-08-18T19:34:06Z

# 3. Get merged PRs
gh pr list --repo openshift-helm-charts/development \
  --state merged --limit 100 \
  --json number,title,author,mergedAt,labels \
  --search "merged:>2026-08-18"

# 4. Infer version (e.g., patch bump → 1.9.7)

# 5. Create worktree
git worktree add <tmpdir>/release-1.9.7 -b release-1.9.7

# 6. Update file in worktree
cd <tmpdir>/release-1.9.7
# Edit release/release_info.json

# 7. Show diff and instruct user
git diff release/release_info.json
```

# Output Format

End with a clear summary:

```
✓ Created worktree at: <tmpdir>/release-X.Y.Z
✓ Branch: release-X.Y.Z  
✓ Updated: release/release_info.json

Next steps:
1. Review the changes: cd <tmpdir>/release-X.Y.Z && git diff
2. Commit: git add release/release_info.json && git commit -m "Release X.Y.Z."
3. Push: git push -u origin release-X.Y.Z
4. Create PR on GitHub targeting 'main' branch
```
