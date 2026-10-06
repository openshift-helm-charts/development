import argparse
import sys

from pullrequest import prfiles
from submission import submission
from tools import gitutils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u",
        "--api-url",
        dest="api_url",
        type=str,
        required=True,
        help="API URL for the pull request",
    )
    parser.add_argument(
        "-c",
        "--allowed-category",
        dest="categories",
        required=True,
        help="Allowed category for this chart (community, partners, or redhat). Can be specified multiple times",
        action="append",
        choices=["community", "partners", "redhat"],
    )
    args = parser.parse_args()

    # Initiate submission and pull modified files
    s = submission.Submission(args.api_url)

    gitutils.add_output("pr_files", s.modified_files)

    # Fail early if there isn't exactly one modified file
    if not s.modified_files:
        print("The PR doesn't contain any files")
        gitutils.add_output("merge_pr", "false")
        gitutils.add_output("msg", "ERROR: PR doesn't contain any files")
        sys.exit(10)

    if len(s.modified_files) > 1:
        print("The PR contains multiple files.")
        gitutils.add_output("merge_pr", "false")
        gitutils.add_output("msg", "ERROR: PR contains multiple files.")
        sys.exit(20)

    # modified_files and files are filled by the same API call, so the single
    # file counted above has to be here too. Guarded anyway because the
    # calling workflows read its status below to decide whether to run the
    # chart name lock check, and an absent or uninterpretable status reads as
    # "not a new file", which would skip that check.
    if not s.files or s.files[0].status is prfiles.FileStatus.UNRECOGNISED:
        print("The PR file is missing status information.")
        gitutils.add_output("merge_pr", "false")
        gitutils.add_output(
            "msg", "ERROR: could not determine the status of the file in the PR."
        )
        sys.exit(40)

    # Parse the modified file to classify the file
    try:
        s.parse_modified_files()
    except submission.SubmissionError:
        # Errors that may occur while parsing the files are irrelevant in this case
        pass

    if len(s.modified_owners) == 1 and s.chart.category in args.categories:
        print("An OWNERS file has been modified or added")
        gitutils.add_output("merge_pr", "true")
    else:
        print(
            f"The file in the PR is not a {'/'.join(x for x in args.categories)} OWNERS file"
        )
        gitutils.add_output("merge_pr", "false")
        gitutils.add_output(
            "msg",
            f"ERROR: PR does not include a {'/'.join(x for x in args.categories)} OWNERS file.",
        )
        sys.exit(30)

    gitutils.add_output("category", s.chart.category)
    gitutils.add_output("organization", s.chart.organization)
    gitutils.add_output("chart-name", s.chart.name)

    # Emit the raw status rather than a "net new" verdict: the workflows
    # calling this disagree on whether a rename counts as new, so each applies
    # its own policy to this value.
    owners_file = s.files[0]
    print(f"The file {owners_file.path} has a status of {owners_file.status.value}")
    gitutils.add_output("file-status", owners_file.status.value)
    if owners_file.previous_path:
        gitutils.add_output("previous-filename", owners_file.previous_path)


if __name__ == "__main__":
    main()
