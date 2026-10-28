"""Unit tests for the pullrequest prartifact module

The GitHub API is mocked with the responses library, which also intercepts the
calls PyGithub makes (PyGithub rides a plain requests session). PyGithub always
addresses api.github.com with an explicit :443 port, so the mocked URLs use the
same wire format.
"""

import pytest
import responses

from pullrequest import prartifact


@pytest.fixture()
def bot_token(monkeypatch):
    """Set a dummy BOT_TOKEN, without which get_pull_request exits"""
    monkeypatch.setenv("BOT_TOKEN", "test-token")


@pytest.fixture()
def github_api():
    """Mock the GitHub API and fail if a registered response is unused"""
    with responses.RequestsMock(assert_all_requests_are_fired=True) as mock:
        yield mock


repo_full_name = "openshift-helm-charts/development"
# URL the callers hand to the prartifact functions
pr_api_url = f"https://api.github.com/repos/{repo_full_name}/pulls/1"
# URL PyGithub actually puts on the wire when listing the PR files
files_wire_url = f"https://api.github.com:443/repos/{repo_full_name}/pulls/1/files"


def mock_pr_files(github_api, files):
    """Mock the GitHub API endpoint queried when listing the files of a PR"""
    github_api.get(files_wire_url, json=files)


def test_get_modified_files_returns_all_filenames(bot_token, github_api):
    """Files with any status (added, modified, removed) are all returned

    The prartifact callers rely on removed files being part of the list.
    """
    mock_pr_files(
        github_api,
        [
            {
                "filename": "charts/partners/acme/awesome/1.0.0/report.yaml",
                "status": "added",
            },
            {"filename": "charts/partners/acme/awesome/OWNERS", "status": "modified"},
            {
                "filename": "charts/partners/acme/awesome/0.9.0/report.yaml",
                "status": "removed",
            },
        ],
    )

    assert prartifact.get_modified_files(pr_api_url) == [
        "charts/partners/acme/awesome/1.0.0/report.yaml",
        "charts/partners/acme/awesome/OWNERS",
        "charts/partners/acme/awesome/0.9.0/report.yaml",
    ]
    # lazy=True keeps the PR resolution local, so listing the files is the
    # only request made
    assert len(github_api.calls) == 1


def test_get_modified_files_exits_on_github_error(bot_token, github_api):
    """A GitHub API error fails the run, as before

    The error message travels in the exit status, so callers can surface it
    (submission.py turns it into the PR comment message).
    """
    github_api.get(files_wire_url, json={"message": "Not Found"}, status=404)

    with pytest.raises(SystemExit) as exc_info:
        prartifact.get_modified_files(pr_api_url)

    assert exc_info.value.code.startswith("[ERROR] getting pr files: 404")


def test_get_modified_files_exits_without_bot_token(monkeypatch):
    """A missing BOT_TOKEN fails the run with an explicit message"""
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        prartifact.get_modified_files(pr_api_url)

    assert exc_info.value.code == "[ERROR] BOT_TOKEN environment variable is not set"


def test_get_pr_files_returns_file_objects_with_status(bot_token, github_api):
    """Each file exposes its status, so callers can tell added from modified"""
    mock_pr_files(
        github_api,
        [
            {"filename": "charts/partners/acme/awesome/OWNERS", "status": "added"},
            {
                "filename": "charts/partners/acme/awesome/1.0.0/report.yaml",
                "status": "modified",
            },
        ],
    )

    files = prartifact.get_pr_files(prartifact.get_pull_request(pr_api_url))

    assert [file.filename for file in files] == [
        "charts/partners/acme/awesome/OWNERS",
        "charts/partners/acme/awesome/1.0.0/report.yaml",
    ]
    assert [file.status for file in files] == ["added", "modified"]


def test_get_pull_request_resolves_without_api_calls(bot_token, github_api):
    """The owner, repository and PR number are extracted from the API URL

    Resolving the PR is purely local: no request is made until the files are
    listed, so get_modified_files costs a single API request. No response is
    registered, so any request raises instead of being served.
    """
    pr = prartifact.get_pull_request(pr_api_url)

    assert pr.number == 1


def test_get_pull_request_rejects_non_api_url(bot_token):
    """URLs that are not pull request API URLs are rejected explicitly"""
    with pytest.raises(ValueError):
        prartifact.get_pull_request(f"https://github.com/{repo_full_name}/pull/1")


def test_get_pr_files_follows_pagination(bot_token, github_api):
    """PRs spanning several pages of files are listed completely"""
    github_api.get(
        files_wire_url,
        json=[{"filename": "page1.yaml", "status": "added"}],
        headers={"Link": f'<{pr_api_url}/files/page2>; rel="next"'},
    )
    github_api.get(
        f"{files_wire_url}/page2",
        json=[{"filename": "page2.yaml", "status": "modified"}],
    )

    files = prartifact.get_pr_files(prartifact.get_pull_request(pr_api_url))

    assert [file.filename for file in files] == ["page1.yaml", "page2.yaml"]
