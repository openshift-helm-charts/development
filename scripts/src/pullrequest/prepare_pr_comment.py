import os
import sys

def get_success_coment():
    return "Congratulations! Your chart has been certified and will be published shortly."

def get_content_failure_message():
    return "One or more errors were found with the pull request:"

def get_community_review_message():
    return "Community charts require maintainer review and approval, a review will be conducted shortly."

def get_failure_comment():
    return "There were one or more errors while building and verifying your pull request."

def get_verifier_errors_comment():
    return "[ERROR] The submitted chart has failed certification. Reason(s):"

def get_verifier_errors_trailer():
    return "Please create a valid report with the [chart-verifier](https://github.com/redhat-certification/chart-verifier) \
and ensure all mandatory checks pass."

def prepare_failure_comment():
    msg = f"""\
{get_failure_comment()}
To see the console output with the error messages, click the "Details"
link next to "CI / Chart Certification" job status towards the end of this page.
"""
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += f""" 
{get_verifier_errors_comment()}

{errors}

{get_verifier_errors_trailer()}

"""
        print(f"::set-output name=error-message::{errors}")
    else:
        print(f"::set-output name=error-message::{get_failure_comment()}")
    return msg

def prepare_success_comment():
    msg = f"{get_success_coment()}.\n\n"
    return msg

def prepare_pr_content_failure_comment():
    msg = f"{get_content_failure_message()} \n"
    pr_content_error_msg = os.environ.get("PR_CONTENT_ERROR_MESSAGE", "")
    owners_error_msg = os.environ.get("OWNERS_ERROR_MESSAGE", "")
    if pr_content_error_msg:
        print(f"::set-output name=error-message::{pr_content_error_msg}")
        msg += f"{pr_content_error_msg}\n\n"
    if owners_error_msg:
        print(f"::set-output name=error-message::{owners_error_msg}")
        msg += f"{owners_error_msg}\n\n"
    return msg

def prepare_community_comment():
    msg = f"{get_community_review_message()}\n\n"
    if os.path.exists("./pr/errors"):
        errors = open("./pr/errors").read()
        msg += "However, please note that one or more errors were found while building and verifying your pull request:\n\n"
        msg += f"{errors}\n\n"
    return msg

def prepare_oc_install_fail_comment():
    msg = "Unfortunately the certification process failed to install OpenShift and could not complete.\n\n"
    msg += "This problem will be addressed by maintainers and no further action is required from the submitter at this time.\n\n"
    return msg

def get_comment_header(issue_number):
    msg = f"Thank you for submitting PR #{issue_number} for Helm Chart Certification!\n\n"
    return msg

def get_comment_footer(vendor_label, chart_name):
    msg = "\n---\n\n"
    msg += "For information on the certification process see:\n"
    msg += "- [Red Hat certification requirements and process for Kubernetes applications that are deployed using Helm charts.](https://redhat-connect.gitbook.io/partner-guide-for-red-hat-openshift-and-container/helm-chart-certification/overview).\n\n"
    msg += "For support, connect with our [Technology Partner Success Desk](https://redhat-connect.gitbook.io/red-hat-partner-connect-general-guide/managing-your-account/getting-help/technology-partner-success-desk).\n\n"
    msg += f'/metadata {{"vendor_label": "{vendor_label}", "chart_name": "{chart_name}"}}\n\n'
    return msg

def main():
    pr_content_result = sys.argv[1]
    verify_result = sys.argv[2]
    repository = sys.argv[3]
    issue_number = open("./pr/NR").read().strip()
    vendor_label = open("./pr/vendor").read().strip()
    chart_name = open("./pr/chart").read().strip()
    msg = get_comment_header(issue_number)
    oc_install_result = os.environ.get("OC_INSTALL_RESULT", False)
    if pr_content_result == "failure":
        msg += prepare_pr_content_failure_comment()
        print(f"::set-output name=pr_passed::false")
    elif verify_result == "failure":
        community_manual_review = os.environ.get("COMMUNITY_MANUAL_REVIEW",False)
        if community_manual_review:
            msg += prepare_community_comment()
            print(f"::set-output name=pr_passed::true")
        else:
            msg += prepare_failure_comment()
            print(f"::set-output name=pr_passed::false")
    elif oc_install_result == "failure":
        msg += prepare_oc_install_fail_comment()
        print(f"::set-output name=pr_passed::false")
    else:
        print(f"::set-output name=pr_passed::true")
        msg += prepare_success_comment()

    msg += get_comment_footer(vendor_label, chart_name)

    with open("./pr/comment", "w") as fd:
        fd.write(msg)
        print(f"::set-output name=message-file::{fd.name}")

if __name__ == "__main__":
    main()
