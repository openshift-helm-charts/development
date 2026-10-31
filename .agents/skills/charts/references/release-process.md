# Release process

Workflows and scripts are periodically released from the development repository
into the charts and stage repositories, and charts added to the charts
repository are pulled back into the development repository. The process is
automated and is started by a repository approver.

## Start a release

1. Edit `release/release_info.json` with:
   - the new release version and a description of its content;
   - per repository (charts, development, stage):
     - `merges`: a directory or file merged into the same path in the other
       repository;
     - `replaces`: a directory or file deleted in the other repository and
       replaced by this repository's version (also covers new directories);
     - `ignores`: paths excluded from a merge or replace (also covers deleted
       files).
2. Open a pull request against the development repository containing **only**
   the `release/release_info.json` change.

## What the release workflow does

1. Clones the development, charts, and stage repositories.
2. Updates each repository according to `release/release_info.json`.
3. Creates a PR against the charts repository with the workflow updates —
   merged manually once all tests are clean.
4. Creates a PR against the stage repository with the workflow updates — also
   merged manually.
5. Creates a PR against the development repository with the chart updates —
   auto-merged in subsequent steps.
6. If all is good, auto-merges the `release/release_info.json` PR and creates a
   release; when the incoming chart-update PR is detected, merges it and
   creates a release.

Do not merge the downstream PRs automatically on the user's behalf without
confirming that the checks are clean.
