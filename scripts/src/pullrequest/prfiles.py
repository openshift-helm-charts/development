"""Single source of truth for "which files did this change touch?".

Every call site in this repository resolves modified files through this module,
either by importing it or, from workflow steps, through the `pr-files` console
script. Please do not add another implementation: this module replaced six of
them (see issue #459), which had drifted to the point that the same pull request
could be described three different ways depending on which one asked.

The two behaviours worth knowing about:

- Truncation is an error, never a short list. GitHub caps the pull request file
  list at 3000 files. Silently returning the first 3000 makes every gating caller
  in this repository fail *permissively* -- `check_if_only_charts_are_included`
  answers "yes" because everything it saw was a chart -- so we raise instead.
- The status is reported raw. Whether a renamed OWNERS file counts as net-new is
  a policy question, and the answer differs between partner and community charts.
  That decision belongs to the caller, not here.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

import requests

from tools import gitutils

# GitHub serves a maximum of 3000 files for a pull request, 100 per page.
PER_PAGE = 100
MAX_PAGES = 30

# The compare endpoint returns its files on the first page only and serves at
# most 300 of them. Unlike the pull request endpoint it cannot be paginated, so
# hitting this number is the only signal that files were dropped.
COMPARE_MAX_FILES = 300

# Distinct pull requests to keep file lists for. See list_pr_files.
CACHE_SIZE = 128

XRATELIMIT = "X-RateLimit-Limit"
XRATEREMAIN = "X-RateLimit-Remaining"


class FileStatus(str, Enum):
    """The status GitHub reports for a single file in a diff.

    UNRECOGNISED is ours, not GitHub's: it stands in for a status this module
    does not know. See _to_pr_file for why it exists.
    """

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    RENAMED = "renamed"
    COPIED = "copied"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    UNRECOGNISED = "unrecognised"


@dataclass(frozen=True)
class PRFile:
    """One entry from a GitHub diff.

    Attributes:
        path (str): the file's path relative to the repository root. For a
            rename this is the NEW path.
        status (FileStatus): what happened to the file, or UNRECOGNISED if
            GitHub reported something this module does not know. Callers that
            branch on the status must reject UNRECOGNISED rather than treat it
            as a normal modification.
        previous_path (str | None): the path before a rename, otherwise None.
    """

    path: str
    status: FileStatus
    previous_path: str | None = None


class PRFilesError(Exception):
    """Raised when the list of modified files could not be retrieved."""


class TruncatedFileListError(PRFilesError):
    """Raised when GitHub truncated the file list.

    The partial list is deliberately not returned: every caller in this
    repository would treat it as complete and reach a permissive conclusion.
    """


def _headers():
    """Builds request headers, resolving the token at call time.

    Resolved here rather than passed in so that a token can never end up in
    list_pr_files' cache key.

    Raises:
        PRFilesError: if BOT_TOKEN is unset. Querying anonymously would work
            for a handful of calls and then start failing on GitHub's 60/hour
            unauthenticated limit, which surfaces as an unrelated-looking 403
            partway through a run. A missing token is a configuration error, so
            it is reported as one here.
    """
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise PRFilesError(
            "BOT_TOKEN is not set. It is required to query the GitHub API for "
            "the list of files a change touches."
        )
    return {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }


def _get(url, headers):
    """Performs a single GET and returns (response, decoded_body).

    Raises:
        PRFilesError: on a transport failure, a non-200 status, or a body that
            is not valid JSON.
    """
    print(f"[INFO] Query files : {url}")
    try:
        r = requests.get(url, headers=headers)
    except requests.RequestException as e:
        raise PRFilesError(f"request to {url} failed: {e}") from e

    if XRATELIMIT in r.headers:
        print(f"[DEBUG] {XRATELIMIT} : {r.headers[XRATELIMIT]}")
    if XRATEREMAIN in r.headers:
        print(f"[DEBUG] {XRATEREMAIN}  : {r.headers[XRATEREMAIN]}")

    try:
        body = r.json()
    except (ValueError, UnicodeDecodeError) as e:
        if r.status_code != requests.codes.ok:
            raise PRFilesError(f"GitHub returned HTTP {r.status_code} for {url}") from e
        raise PRFilesError(f"GitHub returned a non-JSON body for {url}: {e}") from e

    if r.status_code != requests.codes.ok:
        # GitHub puts a human-readable explanation in "message" on errors.
        detail = body.get("message") if isinstance(body, dict) else body
        raise PRFilesError(f"GitHub returned HTTP {r.status_code} for {url}: {detail}")

    return r, body


def _to_pr_file(entry):
    """Converts one GitHub diff entry into a PRFile.

    A status this module does not know becomes FileStatus.UNRECOGNISED rather
    than an error, so that callers which only want paths keep working. It is
    never silently treated as a modification: callers that branch on the status
    to decide whether to auto-merge reject UNRECOGNISED.

    Raises:
        PRFilesError: if the entry is malformed.
    """
    if not isinstance(entry, dict):
        raise PRFilesError(
            f"expected a JSON object per file, got {type(entry).__name__}"
        )

    path = entry.get("filename")
    if not path:
        raise PRFilesError(f"diff entry is missing a filename: {entry}")

    raw_status = entry.get("status")
    try:
        status = FileStatus(raw_status)
    except ValueError:
        # Degrade to UNRECOGNISED rather than raising. Most callers only want
        # paths, and failing the whole list would take every chart submission
        # down the moment GitHub adds a status value. The callers that do read
        # the status reject UNRECOGNISED explicitly, so this stays fail-closed
        # exactly where it matters.
        print(
            f"[WARNING] GitHub reported an unrecognised status {raw_status!r} for "
            f"{path}. Known values: "
            f"{', '.join(s.value for s in FileStatus if s is not FileStatus.UNRECOGNISED)}."
        )
        status = FileStatus.UNRECOGNISED

    return PRFile(
        path=path,
        status=status,
        previous_path=entry.get("previous_filename"),
    )


@lru_cache(maxsize=CACHE_SIZE)
def list_pr_files(api_url):
    """Returns every file touched by a pull request.

    Cached on api_url, so the repeated calls made within a single run (releasechecker
    asks up to three times) cost one round trip. The cache key deliberately excludes
    the token, and the return value is a tuple rather than a list because every
    caller is handed the same cached object.

    The cache is bounded rather than unbounded: metrics walks every pull request the
    charts repository has ever seen, and retaining each one's file list for the
    lifetime of that run would cost hundreds of megabytes. Every deduplication this
    is actually here for is a repeat call for the *same* pull request, so a small
    cache captures all of the benefit.

    Args:
        api_url (str): the pull request's API URL, e.g.
            https://api.github.com/repos/<org>/<repo>/pulls/<number>

    Returns:
        tuple[PRFile, ...]: the files, in the order GitHub returned them. Several
            callers pattern-match on the first entry, so the order matters.

    Raises:
        PRFilesError: if the list could not be retrieved.
        TruncatedFileListError: if the pull request exceeds GitHub's 3000 file cap.
    """
    if not api_url:
        raise PRFilesError("an api_url is required to list pull request files")

    headers = _headers()
    url = f"{api_url.rstrip('/')}/files?per_page={PER_PAGE}"

    collected = []
    for _ in range(MAX_PAGES):
        response, body = _get(url, headers)
        if not isinstance(body, list):
            raise PRFilesError(
                f"expected a JSON array of files from {url}, got "
                f"{type(body).__name__}: {body}"
            )

        collected.extend(_to_pr_file(entry) for entry in body)

        # Follow GitHub's own "next" link rather than guessing from the page
        # size: the length heuristic costs an extra request whenever the total
        # is an exact multiple of PER_PAGE, and it cannot tell "last page" from
        # "cap reached". The link already carries per_page and page, so it is
        # followed verbatim.
        next_link = response.links.get("next")
        if not next_link or not next_link.get("url"):
            return tuple(collected)
        url = next_link["url"]

    raise TruncatedFileListError(
        f"{api_url} has more than {PER_PAGE * MAX_PAGES} files, which is GitHub's "
        "maximum for this endpoint. Refusing to continue with a partial list, "
        "because callers would treat it as complete."
    )


def list_compare_files(repository, base, head):
    """Returns every file that differs between two commits.

    This is the answer for a `push` event, where there is no pull request to
    ask about.

    Args:
        repository (str): "<owner>/<repo>".
        base (str): commit to compare from, e.g. a push event's "before" SHA.
        head (str): commit to compare to, e.g. a push event's "after" SHA.

    Returns:
        tuple[PRFile, ...]: the files, in the order GitHub returned them.

    Raises:
        PRFilesError: if the comparison could not be retrieved. A base commit
            GitHub no longer has 404s here, which happens when a force-push has
            left it unreachable or when a branch was just created and reports an
            all-zero SHA. Both are reported as failures rather than as an empty
            list, which a caller would read as "nothing changed".
        TruncatedFileListError: if the comparison exceeds the endpoint's cap.
    """
    for name, value in (("repository", repository), ("base", base), ("head", head)):
        if not value:
            raise PRFilesError(f"a {name} is required to compare two commits")

    url = f"{gitutils.GITHUB_BASE_URL}/repos/{repository}/compare/{base}...{head}"
    _, body = _get(url, _headers())

    if not isinstance(body, dict):
        raise PRFilesError(
            f"expected a JSON object from {url}, got {type(body).__name__}: {body}"
        )

    # "behind" or "diverged" rather than "ahead" means the branch moved between
    # the event firing and this call, typically a force-push. The comparison is
    # still the correct delta between the two commits we were asked about, so it
    # is used -- but the action this replaced treated it as fatal, so it is
    # worth a line in the log when a result looks unexpected.
    comparison = body.get("status")
    if comparison != "ahead":
        print(
            f"[WARNING] {base}...{head} compares as {comparison!r} rather than "
            "'ahead', which usually means the branch was force-pushed. Using the "
            "comparison regardless: it is still the delta between those commits."
        )

    files = body.get("files") or []
    if not isinstance(files, list):
        raise PRFilesError(
            f"expected a JSON array of files from {url}, got {type(files).__name__}"
        )

    if len(files) >= COMPARE_MAX_FILES:
        raise TruncatedFileListError(
            f"{base}...{head} differs by at least {COMPARE_MAX_FILES} files, which "
            "is the maximum this endpoint serves, and it cannot be paginated. "
            "Refusing to continue with a possibly partial list."
        )

    # The commit list caps out before the file list does. A short one means the
    # comparison as a whole was truncated, so the files cannot be trusted either.
    total_commits = body.get("total_commits")
    commits = body.get("commits") or []
    if isinstance(total_commits, int) and total_commits > len(commits):
        raise TruncatedFileListError(
            f"{base}...{head} spans {total_commits} commits but GitHub returned "
            f"only {len(commits)}, so the comparison is truncated."
        )

    return tuple(_to_pr_file(entry) for entry in files)


def paths(files, *, exclude=()):
    """Reduces PRFiles to a plain list of paths.

    Args:
        files (Iterable[PRFile]): the files to reduce.
        exclude (Container[FileStatus]): statuses to leave out. Empty by default,
            so deletions are included -- which is what every existing caller
            expects.

    Returns:
        list[str]: a fresh, mutable list, so callers may modify it without
            disturbing list_pr_files' cache.
    """
    return [f.path for f in files if f.status not in exclude]


def _emit_github_output(files):
    """Writes the file list to $GITHUB_OUTPUT, grouped by status.

    Values are JSON arrays so that workflows can index them with
    fromJSON(...)[0]. The space-delimited format this replaced could not
    represent a filename containing a space.
    """
    by_status = {status: [] for status in FileStatus}
    for f in files:
        by_status[f.status].append(f.path)

    for status, matched in by_status.items():
        gitutils.add_output(status.value, json.dumps(matched))
    gitutils.add_output("all", json.dumps([f.path for f in files]))


def main():
    parser = argparse.ArgumentParser(
        description="List the files touched by a pull request."
    )
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        help="API URL of the pull request",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="compare two commits instead of reading a pull request, for events "
        "where no pull request exists (a push, typically)",
    )
    parser.add_argument(
        "--repository",
        dest="repository",
        type=str,
        help='"<owner>/<repo>" to compare within. Requires --compare',
    )
    parser.add_argument(
        "--base",
        dest="base",
        type=str,
        help="commit to compare from. Requires --compare",
    )
    parser.add_argument(
        "--head",
        dest="head",
        type=str,
        help="commit to compare to. Requires --compare",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="output_format",
        choices=["paths", "json", "github-output"],
        default="paths",
        help="how to render the result (default: paths)",
    )
    args = parser.parse_args()

    # The two modes take disjoint arguments. Reject a mix rather than silently
    # ignoring whichever half does not apply.
    compare_args = {
        "--repository": args.repository,
        "--base": args.base,
        "--head": args.head,
    }
    if args.compare:
        if args.api_url:
            parser.error("--api-url cannot be combined with --compare")
        missing = [name for name, value in compare_args.items() if not value]
        if missing:
            parser.error(f"--compare requires {', '.join(missing)}")
    else:
        supplied = [name for name, value in compare_args.items() if value]
        if supplied:
            parser.error(f"{', '.join(supplied)} may only be used with --compare")
        if not args.api_url:
            parser.error("--api-url is required unless --compare is given")

    try:
        if args.compare:
            files = list_compare_files(args.repository, args.base, args.head)
        else:
            files = list_pr_files(args.api_url)
    except PRFilesError as e:
        print(f"[ERROR] {e}")
        return 1

    if args.output_format == "paths":
        for f in files:
            print(f.path)
    elif args.output_format == "json":
        print(
            json.dumps(
                [
                    {
                        "path": f.path,
                        "status": f.status.value,
                        "previous_path": f.previous_path,
                    }
                    for f in files
                ]
            )
        )
    else:
        _emit_github_output(files)

    return 0


if __name__ == "__main__":
    sys.exit(main())
