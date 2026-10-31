# Testing in a fork

To test workflow or script changes before submitting a PR to the development
repository, you need:

1. A second GitHub account to act as your "bot". This account performs
   approvals and interacts with GitHub Actions on the workflows' behalf,
   because you cannot approve your own PRs.
2. An OpenShift cluster (single-node OpenShift works for most cases) when the
   change requires running `chart-verifier` in the pipeline.

## Prepare the fork

1. Fork the repository.
2. Ensure the `gh-pages` branch exists in the fork; if not, pull it from origin
   and push it.
3. Enable GitHub Pages for the fork (do not use custom workflows for it).
4. Grant the bot account access to the fork as a collaborator.
5. Generate a personal access token for the bot account with write access to
   the repository (comments, approvals, merges) and store it as the `BOT_TOKEN`
   repository secret.

Never print or transmit the token value; pass it only through repository
secrets.

## Run the test

Push your change branch to the fork, open PRs against the fork as needed, and
let the bot account drive them through the same workflow the development
repository uses. The BDD tests in `tests/` automate this flow against the
sandbox repository; see `tests/README.md`.

Clean up test branches, releases, and Pages content on the fork when finished.
