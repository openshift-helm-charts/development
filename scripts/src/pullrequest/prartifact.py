import os
import re
import sys

import requests
from github import Auth, Github
from github.File import File
from github.GithubException import GithubException
from github.PullRequest import PullRequest

pr_labels = []
xRateLimit = "X-RateLimit-Limit"
xRateRemain = "X-RateLimit-Remaining"

pr_api_url_pattern = re.compile(
    r"^https://api\.github\.com/repos/([^/]+/[^/]+)/pulls/(\d+)$"
)


def get_pull_request(api_url: str) -> PullRequest:
    """Resolve the API URL of a PR to a PyGithub PullRequest object

    Args:
        api_url (str): URL of the GitHub PR, e.g.
            https://api.github.com/repos/<owner>/<repo>/pulls/<number>

    Returns:
        PullRequest: PyGithub object representing the PR

    Raises:
        ValueError: if api_url is not a pull request API URL
        SystemExit: with an error message, if BOT_TOKEN is not set
    """
    bot_token = os.environ.get("BOT_TOKEN")
    if not bot_token:
        sys.exit("[ERROR] BOT_TOKEN environment variable is not set")
    match = pr_api_url_pattern.match(api_url)
    if not match:
        raise ValueError(f"Not a pull request API URL: {api_url}")
    repository, pr_number = match.groups()
    return (
        # lazy=True resolves the PR from the URL alone, so listing its files
        # costs a single API request
        Github(auth=Auth.Token(bot_token), per_page=100, lazy=True)
        .get_repo(repository)
        .get_pull(int(pr_number))
    )


def get_pr_files(pr: PullRequest) -> list[File]:
    """Return the list of files changed by the PR, with each file's status

    This is the single shared way to list the files of a PR. Every file the PR
    touches is returned (added, modified, removed, renamed), so callers can
    distinguish how the PR touches each file.

    Args:
        pr (PullRequest): PyGithub object representing the PR

    Returns:
        list[File]: PyGithub File objects, exposing .filename and .status
    """
    return list(pr.get_files())


def get_modified_files(api_url):
    """Returns the list of files modified by the PR

    Args:
        api_url (str): URL of the GitHub PR

    Returns:
        list[str]: List of modified files

    Raises:
        SystemExit: with an error message, if the files cannot be listed
    """
    try:
        return [
            file.filename
            for file in get_pr_files(get_pull_request(api_url))
            if file.filename
        ]
    except (GithubException, ValueError) as e:
        # The message is carried in the exit status (SystemExit.code), so
        # callers that catch it can surface it (submission.py puts it in the
        # PR comment); uncaught, the interpreter prints it and exits 1
        sys.exit(f"[ERROR] getting pr files: {e}")


def get_labels(api_url):
    if not pr_labels:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f'Bearer {os.environ.get("BOT_TOKEN")}',
        }
        r = requests.get(api_url, headers=headers)
        pr_data = r.json()

        if xRateLimit in r.headers:
            print(f"[DEBUG] {xRateLimit} : {r.headers[xRateLimit]}")
        if xRateRemain in r.headers:
            print(f"[DEBUG] {xRateRemain}  : {r.headers[xRateRemain]}")

        if "message" in pr_data:
            print(f'[ERROR] getting pr files: {pr_data["message"]}')
            sys.exit(1)
        if "labels" in pr_data:
            for label in pr_data["labels"]:
                pr_labels.append(label["name"])

    return pr_labels
