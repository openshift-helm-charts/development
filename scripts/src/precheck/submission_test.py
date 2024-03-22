import contextlib
import pytest
import responses

from dataclasses import dataclass, field

from precheck import submission

expected_category = "partners"
expected_organization = "acme"
expected_name = "awesome"
expected_version = "1.42.0"

expected_chart = submission.Chart(
    category=expected_category,
    organization=expected_organization,
    name=expected_name,
    version=expected_version,
)


@dataclass
class SubmissionInitScenario:
    api_url: str
    modified_files: list[str]
    expected_submission: submission.Submission = None
    excepted_exception: contextlib.ContextDecorator = field(
        default_factory=lambda: contextlib.nullcontext()
    )


scenarios_submission_init = [
    # PR contains a unique and unsigned report.yaml
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=False,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
    ),
    # PR contains a signed report
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/2",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml.asc",
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/2",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml.asc",
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=True,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
    ),
    # PR contains the chart's source
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/3",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/Chart.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/buildconfig.yam"
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/deployment.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/imagestream.yam"
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/route.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/service.yaml",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.schema.json",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.yaml",
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/3",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/Chart.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/buildconfig.yam"
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/deployment.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/imagestream.yam"
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/route.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/templates/service.yaml",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.schema.json",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/values.yaml",
            ],
            chart=expected_chart,
            source=submission.Source(
                found=True,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/src/Chart.yaml",
            ),
        ),
    ),
    # PR contains an unsigned tarball
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/4",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz"
            ],
            chart=expected_chart,
            tarball=submission.Tarball(
                found=True,
                provenance=None,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            ),
        ),
    ),
    # PR contains a signed tarball
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/5",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/5",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
            ],
            chart=expected_chart,
            tarball=submission.Tarball(
                found=True,
                provenance=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz.prov",
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/{expected_name}-{expected_version}.tgz",
            ),
        ),
    ),
    # PR contains an OWNERS file
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/6",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
        ],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/6",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
    ),
    # PR contains additional files, not fitting into any expected category
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/7",
        modified_files=["charts/path/to/some/file"],
        expected_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/7",
            modified_files=["charts/path/to/some/file"],
            modified_unknown=["charts/path/to/some/file"],
        ),
    ),
    # Invalid PR contains multiple reports, referencing multiple charts
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/101",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            f"charts/{expected_category}/{expected_organization}/other-chart/{expected_version}/report.yaml",
        ],
        excepted_exception=pytest.raises(submission.DuplicateChartError),
    ),
    # Invalid PR contains a tarball with an incorrect name
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/102",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/incorrectly-named.tgz"
        ],
        excepted_exception=pytest.raises(submission.SubmissionError),
    ),
    # Invalid PR references a Chart with a version that is not Semver compatible
    SubmissionInitScenario(
        api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/103",
        modified_files=[
            f"charts/{expected_category}/{expected_organization}/{expected_name}/0.1.2.3.4/report.yaml"
        ],
        excepted_exception=pytest.raises(submission.VersionError),
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_submission_init)
@responses.activate
def test_submission_init(test_scenario):
    """Test the instantiation of a Submission in different scenarios"""

    # Mock GitHub API
    responses.get(
        f"{test_scenario.api_url}/files",
        json=[{"filename": file} for file in test_scenario.modified_files],
    )

    with test_scenario.excepted_exception:
        s = submission.Submission(api_url=test_scenario.api_url)
        assert s == test_scenario.expected_submission


@responses.activate
def test_submission_not_exist():
    """Test creating a Submission for an unexisting PR"""
    api_url_doesnt_exist = (
        "https://api.github.com/repos/openshift-helm-charts/charts/pulls/9999"
    )

    responses.get(
        f"{api_url_doesnt_exist}/files",
        json={
            "message": "Not Found",
            "documentation_url": "https://docs.github.com/rest/pulls/pulls#list-pull-requests-files",
        },
    )

    with pytest.raises(submission.SubmissionError):
        submission.Submission(api_url=api_url_doesnt_exist)


@dataclass
class CertificationScenario:
    input_submission: submission.Submission
    expected_is_valid_certification: bool
    expected_reason: str = ""


scenarios_certification_submission = [
    # Valid certification Submission contains only a report
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=False,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
        expected_is_valid_certification=True,
    ),
    # Invalid certification Submission contains OWNERS file
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
        expected_is_valid_certification=False,
        expected_reason="[ERROR] Send OWNERS file by itself in a separate PR.",
    ),
    # Invalid certification Submission contains unknown files
    CertificationScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=["charts/path/to/some/file"],
            modified_unknown=["charts/path/to/some/file"],
        ),
        expected_is_valid_certification=False,
        expected_reason="[ERROR] PR includes one or more files not related to charts:",
    ),
]


@pytest.mark.parametrize("test_scenario", scenarios_certification_submission)
def test_is_valid_certification(test_scenario):
    is_valid_certification, reason = (
        test_scenario.input_submission.is_valid_certification_submission()
    )
    assert test_scenario.expected_is_valid_certification == is_valid_certification
    assert test_scenario.expected_reason in reason


@dataclass
class OwnersScenario:
    input_submission: submission.Submission
    expected_is_valid_owners: bool
    expected_reason: str = ""


scenarios_owners_submission = [
    # Valid submission contains only one OWNERS file
    OwnersScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS"
            ],
        ),
        expected_is_valid_owners=True,
    ),
    # Invalid submission contains multiple OWNERS file
    OwnersScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS",
                f"charts/{expected_category}/{expected_organization}/another_chart/OWNERS",
            ],
            modified_owners=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/OWNERS",
                f"charts/{expected_category}/{expected_organization}/another_chart/OWNERS",
            ],
        ),
        expected_is_valid_owners=False,
        expected_reason="[ERROR] Send OWNERS file by itself in a separate PR.",
    ),
    # Invalid submission contains unknown files
    OwnersScenario(
        input_submission=submission.Submission(
            api_url="https://api.github.com/repos/openshift-helm-charts/charts/pulls/1",
            modified_files=[
                f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml"
            ],
            chart=expected_chart,
            report=submission.Report(
                found=True,
                signed=False,
                path=f"charts/{expected_category}/{expected_organization}/{expected_name}/{expected_version}/report.yaml",
            ),
        ),
        expected_is_valid_owners=False,
        expected_reason="No OWNERS file provided",
    ),
    # Invalid submission doesn't contain an OWNER file
]


@pytest.mark.parametrize("test_scenario", scenarios_owners_submission)
def test_is_valid_owners(test_scenario):
    is_valid_owners, reason = (
        test_scenario.input_submission.is_valid_owners_submission()
    )
    assert test_scenario.expected_is_valid_owners == is_valid_owners
    assert test_scenario.expected_reason in reason
