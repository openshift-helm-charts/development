"""Unit tests for check_for_owners.

The outputs asserted here are consumed directly by mercury_bot.yml and
check-locks-on-owners-submission.yml, which use them to gate auto-merging an
OWNERS file. Getting file-status wrong either blocks legitimate partner
updates or merges an OWNERS file for a locked chart name, and neither workflow
is reachable from a unit test, so they are pinned here instead.
"""

import pytest
import responses

from pullrequest import check_for_owners, prfiles

API_URL = "https://api.github.com/repos/openshift-helm-charts/charts/pulls/42"
FILES_URL = f"{API_URL}/files"
PARTNER_OWNERS = "charts/partners/acme/awesome/OWNERS"


@pytest.fixture(autouse=True)
def github_env(monkeypatch, tmp_path):
    """Point GITHUB_OUTPUT at a temp file and drop the memoized file list.

    list_pr_files is cached on api_url, so without clearing it every test here
    would be handed the first test's mocked file.
    """
    output_file = tmp_path / "github_output"
    output_file.touch()
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))
    monkeypatch.setenv("BOT_TOKEN", "a-token")
    prfiles.list_pr_files.cache_clear()
    yield output_file
    prfiles.list_pr_files.cache_clear()


def run_check(monkeypatch, files, categories=("partners",)):
    """Run main() against a mocked file list, returning the outputs it wrote."""
    responses.get(FILES_URL, json=files)
    argv = ["check-for-owners", "--api-url", API_URL]
    for category in categories:
        argv += ["--allowed-category", category]
    monkeypatch.setattr("sys.argv", argv)

    check_for_owners.main()


def read_outputs(output_file):
    """Parse $GITHUB_OUTPUT. Later writes win, as they do in Actions."""
    return dict(
        line.split("=", 1) for line in output_file.read_text().strip().splitlines()
    )


def entry(filename, status, previous_filename=None):
    e = {"filename": filename, "status": status}
    if previous_filename:
        e["previous_filename"] = previous_filename
    return e


# The status is emitted raw. Each workflow applies its own "net new" policy to
# it, because they disagree on whether a rename counts.


@responses.activate
@pytest.mark.parametrize("status", ["added", "modified", "removed", "changed"])
def test_status_is_emitted_verbatim(monkeypatch, github_env, status):
    run_check(monkeypatch, [entry(PARTNER_OWNERS, status)])

    outputs = read_outputs(github_env)
    assert outputs["merge_pr"] == "true"
    assert outputs["file-status"] == status
    assert "previous-filename" not in outputs


@responses.activate
def test_rename_emits_previous_filename(monkeypatch, github_env):
    run_check(
        monkeypatch,
        [
            entry(
                PARTNER_OWNERS,
                "renamed",
                previous_filename="charts/partners/old-acme/awesome/OWNERS",
            )
        ],
    )

    outputs = read_outputs(github_env)
    assert outputs["merge_pr"] == "true"
    assert outputs["file-status"] == "renamed"
    assert outputs["previous-filename"] == "charts/partners/old-acme/awesome/OWNERS"


@responses.activate
def test_chart_identity_is_emitted(monkeypatch, github_env):
    run_check(monkeypatch, [entry(PARTNER_OWNERS, "added")])

    outputs = read_outputs(github_env)
    assert outputs["category"] == "partners"
    assert outputs["organization"] == "acme"
    assert outputs["chart-name"] == "awesome"


# Every rejection below sets merge_pr=false and exits non-zero, which is what
# stops the calling workflow from reaching its merge step.


@responses.activate
def test_rejects_pr_with_no_files(monkeypatch, github_env):
    with pytest.raises(SystemExit) as e:
        run_check(monkeypatch, [])

    assert e.value.code == 10
    assert read_outputs(github_env)["merge_pr"] == "false"


@responses.activate
def test_rejects_pr_with_multiple_files(monkeypatch, github_env):
    with pytest.raises(SystemExit) as e:
        run_check(
            monkeypatch,
            [
                entry(PARTNER_OWNERS, "added"),
                entry("charts/partners/acme/other/OWNERS", "added"),
            ],
        )

    assert e.value.code == 20
    assert read_outputs(github_env)["merge_pr"] == "false"


@responses.activate
def test_rejects_file_that_is_not_an_owners_file(monkeypatch, github_env):
    with pytest.raises(SystemExit) as e:
        run_check(
            monkeypatch,
            [entry("charts/partners/acme/awesome/1.4.0/report.yaml", "added")],
        )

    assert e.value.code == 30
    outputs = read_outputs(github_env)
    assert outputs["merge_pr"] == "false"
    assert "file-status" not in outputs


@responses.activate
def test_rejects_owners_file_from_a_disallowed_category(monkeypatch, github_env):
    """A community OWNERS file must not be merged by the partners-only
    workflow, even though it is a well-formed OWNERS submission."""
    with pytest.raises(SystemExit) as e:
        run_check(
            monkeypatch,
            [entry("charts/community/acme/awesome/OWNERS", "added")],
            categories=("partners",),
        )

    assert e.value.code == 30
    assert read_outputs(github_env)["merge_pr"] == "false"


@responses.activate
def test_rejects_unrecognised_status(monkeypatch, github_env):
    """An unrecognised status must not fall through as a mergeable file.

    prfiles keeps the file rather than failing the whole list, so the rejection
    has to happen here: this is the caller that branches on the status, and a
    status it cannot read means it cannot tell a new OWNERS file from an edit.
    """
    responses.get(FILES_URL, json=[{"filename": PARTNER_OWNERS, "status": "nope"}])
    monkeypatch.setattr(
        "sys.argv",
        [
            "check-for-owners",
            "--api-url",
            API_URL,
            "--allowed-category",
            "partners",
        ],
    )

    with pytest.raises(SystemExit) as e:
        check_for_owners.main()

    assert e.value.code == 40
    outputs = read_outputs(github_env)
    assert outputs["merge_pr"] == "false"
    assert "status" in outputs["msg"]
