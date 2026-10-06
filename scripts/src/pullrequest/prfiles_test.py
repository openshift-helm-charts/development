"""Unit tests for prfiles.

Grouped by the function under test: list_pr_files first, then pagination and
error handling, then caching, paths, list_compare_files, and the CLI.
"""

import dataclasses
import json

import pytest
import requests
import responses

from pullrequest import prfiles

API_URL = "https://api.github.com/repos/openshift-helm-charts/charts/pulls/42"
FILES_URL = f"{API_URL}/files"
COMPARE_URL = (
    "https://api.github.com/repos/openshift-helm-charts/charts/compare/base1...head2"
)


@pytest.fixture(autouse=True)
def clear_cache(monkeypatch):
    """list_pr_files is cached for the lifetime of the process, so a result
    would otherwise leak from one test into the next."""
    prfiles.list_pr_files.cache_clear()
    monkeypatch.setenv("BOT_TOKEN", "a-token")
    yield
    prfiles.list_pr_files.cache_clear()


def entry(filename, status="modified", previous_filename=None):
    """Builds a GitHub diff entry, trimmed to the fields this module reads."""
    e = {"filename": filename, "status": status}
    if previous_filename:
        e["previous_filename"] = previous_filename
    return e


def link_header(url):
    return {"Link": f'<{url}>; rel="next"'}


def compare_body(files, status="ahead", total_commits=1, commits=1):
    return {
        "status": status,
        "total_commits": total_commits,
        "commits": [{"sha": f"c{i}"} for i in range(commits)],
        "files": files,
    }


# list_pr_files


@responses.activate
def test_single_page():
    responses.get(
        FILES_URL,
        json=[entry("charts/partners/acme/vault/OWNERS", "added")],
    )

    files = prfiles.list_pr_files(API_URL)

    assert files == (
        prfiles.PRFile(
            path="charts/partners/acme/vault/OWNERS",
            status=prfiles.FileStatus.ADDED,
        ),
    )


@responses.activate
def test_empty_pr():
    responses.get(FILES_URL, json=[])
    assert prfiles.list_pr_files(API_URL) == ()


@responses.activate
def test_all_status_values_are_understood():
    responses.get(
        FILES_URL,
        json=[
            entry(f"f{i}", status.value) for i, status in enumerate(prfiles.FileStatus)
        ],
    )

    files = prfiles.list_pr_files(API_URL)

    assert [f.status for f in files] == list(prfiles.FileStatus)


@responses.activate
def test_rename_carries_previous_path():
    responses.get(
        FILES_URL,
        json=[
            entry(
                "charts/partners/acme/new/OWNERS",
                "renamed",
                previous_filename="charts/partners/acme/old/OWNERS",
            )
        ],
    )

    (renamed,) = prfiles.list_pr_files(API_URL)

    assert renamed.path == "charts/partners/acme/new/OWNERS"
    assert renamed.previous_path == "charts/partners/acme/old/OWNERS"
    assert renamed.status == prfiles.FileStatus.RENAMED


@responses.activate
def test_unrecognised_status_becomes_unrecognised(capsys):
    """A status we do not know must not stop callers that only want paths.

    Guessing "modified" would let an unreviewed change through an OWNERS gate,
    so it is surfaced as UNRECOGNISED for the callers that branch on it to
    reject, rather than as a value they would act on.
    """
    responses.get(FILES_URL, json=[entry("charts/a/OWNERS", "teleported")])

    files = prfiles.list_pr_files(API_URL)

    assert files == (
        prfiles.PRFile("charts/a/OWNERS", prfiles.FileStatus.UNRECOGNISED),
    )
    assert "unrecognised status 'teleported'" in capsys.readouterr().out


@responses.activate
def test_missing_filename_is_fatal():
    responses.get(FILES_URL, json=[{"status": "added"}])

    with pytest.raises(prfiles.PRFilesError, match="missing a filename"):
        prfiles.list_pr_files(API_URL)


def test_empty_api_url_is_rejected():
    with pytest.raises(prfiles.PRFilesError, match="api_url is required"):
        prfiles.list_pr_files("")


# Pagination


@responses.activate
def test_follows_next_link_across_pages():
    page2 = f"{FILES_URL}?per_page=100&page=2"
    responses.get(
        FILES_URL,
        json=[entry(f"page1-{i}") for i in range(100)],
        headers=link_header(page2),
    )
    responses.get(page2, json=[entry("page2-0")])

    files = prfiles.list_pr_files(API_URL)

    assert len(files) == 101
    assert files[0].path == "page1-0"
    assert files[-1].path == "page2-0"


@responses.activate
def test_stops_without_a_next_link_even_on_a_full_page():
    """A page of exactly PER_PAGE is the last page unless GitHub says
    otherwise; the old length heuristic spent a request finding that out."""
    responses.get(FILES_URL, json=[entry(f"f{i}") for i in range(100)])

    assert len(prfiles.list_pr_files(API_URL)) == 100
    assert len(responses.calls) == 1


@responses.activate
def test_next_link_is_followed_verbatim():
    """The link already carries per_page and page. Re-appending them produces
    a duplicated query string and a wrong page."""
    page2 = (
        "https://api.github.com/repositories/1234/pulls/42/files?per_page=100&page=2"
    )
    responses.get(FILES_URL, json=[entry("f0")], headers=link_header(page2))
    responses.get(page2, json=[])

    prfiles.list_pr_files(API_URL)

    assert responses.calls[1].request.url == page2


@responses.activate
def test_truncation_raises_rather_than_returning_a_partial_list():
    """Every gating caller treats a short list as complete and answers
    permissively, so the partial result must not escape."""
    for page in range(1, prfiles.MAX_PAGES + 1):
        responses.get(
            f"{FILES_URL}?per_page=100&page={page}" if page > 1 else FILES_URL,
            json=[entry(f"p{page}-{i}") for i in range(100)],
            headers=link_header(f"{FILES_URL}?per_page=100&page={page + 1}"),
        )

    with pytest.raises(prfiles.TruncatedFileListError):
        prfiles.list_pr_files(API_URL)


def test_truncation_error_is_a_prfiles_error():
    """Callers that only care about failure can catch the base class."""
    assert issubclass(prfiles.TruncatedFileListError, prfiles.PRFilesError)


# Error handling


@responses.activate
def test_non_200_raises():
    responses.get(
        FILES_URL,
        json={"message": "Not Found"},
        status=404,
    )

    with pytest.raises(prfiles.PRFilesError, match="404"):
        prfiles.list_pr_files(API_URL)


@responses.activate
def test_error_message_from_github_is_surfaced():
    responses.get(
        FILES_URL,
        json={"message": "API rate limit exceeded"},
        status=403,
    )

    with pytest.raises(prfiles.PRFilesError, match="API rate limit exceeded"):
        prfiles.list_pr_files(API_URL)


@responses.activate
def test_non_json_body_raises():
    responses.get(FILES_URL, body="<html>502 Bad Gateway</html>", status=200)

    with pytest.raises(prfiles.PRFilesError, match="non-JSON"):
        prfiles.list_pr_files(API_URL)


@responses.activate
def test_json_object_where_an_array_was_expected_raises():
    """A 200 carrying an object is a protocol violation, not an empty PR."""
    responses.get(FILES_URL, json={"message": "Moved Permanently"}, status=200)

    with pytest.raises(prfiles.PRFilesError, match="expected a JSON array"):
        prfiles.list_pr_files(API_URL)


@responses.activate
def test_connection_error_raises():
    responses.get(
        FILES_URL,
        body=requests.exceptions.ConnectionError("no route to host"),
    )

    with pytest.raises(prfiles.PRFilesError, match="failed"):
        prfiles.list_pr_files(API_URL)


# Caching and authentication


@responses.activate
def test_repeated_calls_hit_the_api_once():
    responses.get(FILES_URL, json=[entry("charts/a/Chart.yaml")])

    prfiles.list_pr_files(API_URL)
    prfiles.list_pr_files(API_URL)

    assert len(responses.calls) == 1


@responses.activate
def test_distinct_urls_are_cached_separately():
    """The module global this replaced was not keyed, so a second pull request
    in the same process received the first one's files."""
    other_url = "https://api.github.com/repos/openshift-helm-charts/charts/pulls/43"
    responses.get(FILES_URL, json=[entry("charts/a/Chart.yaml")])
    responses.get(f"{other_url}/files", json=[entry("charts/b/Chart.yaml")])

    assert prfiles.list_pr_files(API_URL)[0].path == "charts/a/Chart.yaml"
    assert prfiles.list_pr_files(other_url)[0].path == "charts/b/Chart.yaml"


@responses.activate
def test_result_is_immutable():
    """Callers share one cached object, so a mutable result would let one
    caller corrupt another's view."""
    responses.get(FILES_URL, json=[entry("charts/a/Chart.yaml")])

    files = prfiles.list_pr_files(API_URL)

    with pytest.raises(AttributeError):
        files.append(prfiles.PRFile("x", prfiles.FileStatus.ADDED))
    with pytest.raises(dataclasses.FrozenInstanceError):
        files[0].path = "y"


@responses.activate
def test_token_is_not_part_of_the_cache_key(monkeypatch):
    """Resolved inside the function so it cannot leak into the key."""
    responses.get(FILES_URL, json=[entry("charts/a/Chart.yaml")])

    prfiles.list_pr_files(API_URL)
    monkeypatch.setenv("BOT_TOKEN", "a-different-token")
    prfiles.list_pr_files(API_URL)

    assert len(responses.calls) == 1


@responses.activate
def test_token_is_sent_as_a_bearer_header():
    responses.get(FILES_URL, json=[])

    prfiles.list_pr_files(API_URL)

    assert responses.calls[0].request.headers["Authorization"] == "Bearer a-token"


@responses.activate
def test_absent_token_is_rejected_before_any_request(monkeypatch):
    """Anonymous requests would succeed a few times, then start failing on
    GitHub's 60/hour limit as a 403 that looks like something else."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    responses.get(FILES_URL, json=[])

    with pytest.raises(prfiles.PRFilesError, match="BOT_TOKEN is not set"):
        prfiles.list_pr_files(API_URL)

    assert len(responses.calls) == 0


# paths()

PATHS_FILES = (
    prfiles.PRFile("added.yaml", prfiles.FileStatus.ADDED),
    prfiles.PRFile("gone.yaml", prfiles.FileStatus.REMOVED),
    prfiles.PRFile("changed.yaml", prfiles.FileStatus.MODIFIED),
)


def test_paths_includes_every_status_by_default():
    """The seven prartifact callers rely on deletions being present."""
    assert prfiles.paths(PATHS_FILES) == ["added.yaml", "gone.yaml", "changed.yaml"]


def test_paths_exclude_filters_by_status():
    assert prfiles.paths(PATHS_FILES, exclude={prfiles.FileStatus.REMOVED}) == [
        "added.yaml",
        "changed.yaml",
    ]


def test_paths_returns_a_fresh_mutable_list():
    first = prfiles.paths(PATHS_FILES)
    first.append("extra")

    assert "extra" not in prfiles.paths(PATHS_FILES)


def test_paths_preserves_order():
    assert prfiles.paths(PATHS_FILES) == [f.path for f in PATHS_FILES]


# list_compare_files


@responses.activate
def test_compare_returns_files_in_order():
    responses.get(
        COMPARE_URL,
        json=compare_body(
            [
                entry("charts/a/OWNERS", "added"),
                entry("charts/b/OWNERS", "modified"),
            ]
        ),
    )

    files = prfiles.list_compare_files("openshift-helm-charts/charts", "base1", "head2")

    assert files == (
        prfiles.PRFile("charts/a/OWNERS", prfiles.FileStatus.ADDED),
        prfiles.PRFile("charts/b/OWNERS", prfiles.FileStatus.MODIFIED),
    )


@responses.activate
def test_compare_with_no_differences():
    responses.get(COMPARE_URL, json=compare_body([]))

    assert (
        prfiles.list_compare_files("openshift-helm-charts/charts", "base1", "head2")
        == ()
    )


@responses.activate
def test_compare_force_push_is_used_anyway(capsys):
    """A non-'ahead' status is what the action this replaced died on. The
    comparison is still the delta we asked for, so it is used."""
    responses.get(
        COMPARE_URL,
        json=compare_body([entry("charts/a/OWNERS", "added")], status="diverged"),
    )

    files = prfiles.list_compare_files("openshift-helm-charts/charts", "base1", "head2")

    assert len(files) == 1
    assert "[WARNING]" in capsys.readouterr().out


@responses.activate
def test_compare_file_cap_raises():
    responses.get(
        COMPARE_URL,
        json=compare_body([entry(f"charts/c{i}/OWNERS", "added") for i in range(300)]),
    )

    with pytest.raises(prfiles.TruncatedFileListError):
        prfiles.list_compare_files("openshift-helm-charts/charts", "base1", "head2")


@responses.activate
def test_compare_truncated_commit_list_raises():
    """The commit list caps out before the file list does, so a short one means
    the files cannot be trusted either."""
    responses.get(
        COMPARE_URL,
        json=compare_body(
            [entry("charts/a/OWNERS", "added")], total_commits=400, commits=250
        ),
    )

    with pytest.raises(prfiles.TruncatedFileListError):
        prfiles.list_compare_files("openshift-helm-charts/charts", "base1", "head2")


@responses.activate
def test_compare_unknown_base_raises_rather_than_returning_empty():
    """A garbage-collected or all-zero base 404s. That must not read as
    'nothing changed'."""
    zeros = "0" * 40
    responses.get(
        f"https://api.github.com/repos/openshift-helm-charts/charts/compare/{zeros}...head2",
        json={"message": "Not Found"},
        status=404,
    )

    with pytest.raises(prfiles.PRFilesError, match="404"):
        prfiles.list_compare_files("openshift-helm-charts/charts", zeros, "head2")


@pytest.mark.parametrize(
    ("repository", "base", "head"),
    [("", "base1", "head2"), ("o/r", "", "head2"), ("o/r", "base1", "")],
)
def test_compare_missing_argument_raises(repository, base, head):
    """An empty identifier would silently change the endpoint being called."""
    with pytest.raises(prfiles.PRFilesError, match="required"):
        prfiles.list_compare_files(repository, base, head)


# main()


@responses.activate
def test_main_paths_format(monkeypatch, capsys):
    responses.get(FILES_URL, json=[entry("charts/a/Chart.yaml"), entry("b.yaml")])
    monkeypatch.setattr("sys.argv", ["pr-files", "--api-url", API_URL])

    assert prfiles.main() == 0

    out = capsys.readouterr().out
    assert "charts/a/Chart.yaml" in out
    assert "b.yaml" in out


@responses.activate
def test_main_json_format(monkeypatch, capsys):
    responses.get(
        FILES_URL,
        json=[entry("new/OWNERS", "renamed", previous_filename="old/OWNERS")],
    )
    monkeypatch.setattr(
        "sys.argv", ["pr-files", "--api-url", API_URL, "--format", "json"]
    )

    assert prfiles.main() == 0

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload == [
        {
            "path": "new/OWNERS",
            "status": "renamed",
            "previous_path": "old/OWNERS",
        }
    ]


@responses.activate
def test_main_github_output_format_writes_json_arrays(monkeypatch, tmp_path):
    """JSON arrays so fromJSON(...)[0] works, and so a filename containing a
    space stops being a failure mode."""
    output_file = tmp_path / "github_output"
    output_file.touch()
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    responses.get(
        FILES_URL,
        json=[
            entry("charts/a b/OWNERS", "added"),
            entry("charts/c/Chart.yaml", "removed"),
        ],
    )
    monkeypatch.setattr(
        "sys.argv",
        ["pr-files", "--api-url", API_URL, "--format", "github-output"],
    )

    assert prfiles.main() == 0

    written = dict(
        line.split("=", 1) for line in output_file.read_text().strip().splitlines()
    )
    assert json.loads(written["added"]) == ["charts/a b/OWNERS"]
    assert json.loads(written["removed"]) == ["charts/c/Chart.yaml"]
    assert json.loads(written["modified"]) == []
    assert json.loads(written["all"]) == [
        "charts/a b/OWNERS",
        "charts/c/Chart.yaml",
    ]


@responses.activate
def test_main_returns_nonzero_on_failure(monkeypatch, capsys):
    responses.get(FILES_URL, json={"message": "Not Found"}, status=404)
    monkeypatch.setattr("sys.argv", ["pr-files", "--api-url", API_URL])

    assert prfiles.main() == 1
    assert "[ERROR]" in capsys.readouterr().out


@responses.activate
def test_main_compare_github_output(monkeypatch, tmp_path):
    output_file = tmp_path / "github_output"
    output_file.touch()
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    responses.get(
        COMPARE_URL,
        json=compare_body(
            [
                entry("charts/a/OWNERS", "added"),
                entry("charts/b/OWNERS", "modified"),
            ]
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "pr-files",
            "--compare",
            "--repository",
            "openshift-helm-charts/charts",
            "--base",
            "base1",
            "--head",
            "head2",
            "--format",
            "github-output",
        ],
    )

    assert prfiles.main() == 0

    written = dict(
        line.split("=", 1) for line in output_file.read_text().strip().splitlines()
    )
    assert json.loads(written["added"]) == ["charts/a/OWNERS"]
    assert json.loads(written["modified"]) == ["charts/b/OWNERS"]


@pytest.mark.parametrize(
    "argv",
    [
        ["pr-files"],
        ["pr-files", "--compare"],
        ["pr-files", "--compare", "--repository", "o/r", "--base", "b"],
        [
            "pr-files",
            "--compare",
            "--api-url",
            API_URL,
            "--repository",
            "o/r",
            "--base",
            "b",
            "--head",
            "h",
        ],
        ["pr-files", "--api-url", API_URL, "--base", "b"],
    ],
)
def test_main_rejects_incompatible_arguments(monkeypatch, argv):
    """The two modes take disjoint arguments; a mix must not silently pick one
    and ignore the rest."""
    monkeypatch.setattr("sys.argv", argv)

    with pytest.raises(SystemExit) as e:
        prfiles.main()

    assert e.value.code == 2
