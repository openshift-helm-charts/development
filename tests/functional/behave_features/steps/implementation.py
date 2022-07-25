from behave import given, when, then

############### Common step definitions ###############
@given(u'the vendor "{vendor}" has a valid identity as "{vendor_type}"')
def vendor_has_valid_identity(context, vendor, vendor_type):
    context.workflow_test.set_vendor(vendor, vendor_type)

@given(u'an error-free chart source is used in "{chart_path}"')
def chart_source_is_used(context, chart_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=False)
    context.workflow_test.push_chart(is_tarball=False)

@given(u'chart source is used in "{chart_path}"')
def user_has_used_chart_src(context, chart_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=False)

@given(u'an error-free chart tarball is used in "{chart_path}"')
def user_has_created_error_free_chart_tarball(context, chart_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=True)
    context.workflow_test.push_chart(is_tarball=True)

@given(u'an error-free chart tarball used in "{chart_path}" and report in "{report_path}"')
def user_has_created_error_free_chart_tarball_and_report(context, chart_path, report_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.update_test_report(report_path)

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=True)
    context.workflow_test.process_report()
    context.workflow_test.push_chart(is_tarball=True)

@given(u'an error-free chart source used in "{chart_path}" and report in "{report_path}"')
def user_has_created_error_free_chart_src_and_report(context, chart_path, report_path):
    context.workflow_test.update_test_chart(chart_path)
    context.workflow_test.update_test_report(report_path)

    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()
    context.workflow_test.process_chart(is_tarball=False)
    context.workflow_test.process_report()
    context.workflow_test.push_chart(is_tarball=False)

@given(u'a "{report_path}" is provided')
def user_generated_a_report(context, report_path):
    context.workflow_test.update_test_report(report_path)
    context.workflow_test.setup_git_context()
    context.workflow_test.setup_gh_pages_branch()
    context.workflow_test.setup_temp_dir()
    context.workflow_test.process_owners_file()

@when(u'the user sends a pull request with the report')
@when(u'the user sends a pull request with the chart')
@when(u'the user sends a pull request with the chart and report')
def user_sends_a_pull_request(context):
    context.workflow_test.send_pull_request()

@when(u'the user pushed the chart and created pull request')
def user_pushed_the_chart_and_created_pull_request(context):
    context.workflow_test.push_chart(is_tarball=False)
    context.workflow_test.send_pull_request()

@then(u'the user sees the pull request is merged')
def pull_request_is_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='success')
    context.workflow_test.check_pull_request_result(expect_merged=True)
    context.workflow_test.check_pull_request_labels()

@then(u'the index.yaml file is updated with an entry for the submitted chart')
def index_yaml_updated_with_submitted_chart(context):
    context.workflow_test.check_index_yaml()

@then(u'a release is published with corresponding report and chart tarball')
def release_is_published(context):
    context.workflow_test.check_release_result()

@then(u'the pull request is not merged')
def pull_request_is_not_merged(context):
    context.workflow_test.check_workflow_conclusion(expect_result='failure')
    context.workflow_test.check_pull_request_result(expect_merged=False)

@then(u'user gets the "{message}" in the pull request comment')
def user_gets_a_message(context, message):
    context.workflow_test.check_pull_request_comments(expect_message=message)

########## Unique step definitions #################

@given(u'README file is missing in the chart')
def readme_file_is_missing(context):
    context.workflow_test.remove_readme_file()

@then(u'the index.yaml file is updated with an entry for the submitted chart with correct providerType')
def index_yaml_is_updated_with_new_entry_with_correct_provider_type(context):
    context.workflow_test.check_index_yaml(check_provider_type=True)

@given(u'the report contains an "{invalid_url}"')
def invalid_url_in_the_report(context, invalid_url):
    context.workflow_test.process_report(update_url=True, url=invalid_url)

@given(u'user adds a non chart related file')
def user_adds_a_non_chart_related_file(context):
    context.workflow_test.add_non_chart_related_file()

@when(u'the user sends a pull request with both chart and non related file')
def user_sends_pull_request_with_chart_and_non_related_file(context):
    context.workflow_test.push_chart(is_tarball=False, add_non_chart_file=True)
    context.workflow_test.send_pull_request()

@given(u'provider delivery control is set to "{provider_control_owners}" in the OWNERS file')
def provider_delivery_control_set_in_owners(context, provider_control_owners):
    if provider_control_owners == "true":
        context.workflow_test.secrets.provider_delivery=True
    else:
        context.workflow_test.secrets.provider_delivery=False

@given(u'provider delivery control is set to "{provider_control_report}" in the report')
def provider_delivery_control_set_in_report(context, provider_control_report):
    if provider_control_report == "true":
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=True)
    else:
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=False)

@given(u'provider delivery controls is set to "{provider_control_report}" and a package digest is "{package_digest_set}" in the report')
def provider_delivery_control_and_package_digest_set_in_report(context, provider_control_report, package_digest_set=True):
    if package_digest_set == "true":
        no_package_digest = False
    else:
        no_package_digest = True

    if provider_control_report == "true":
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=True, unset_package_digest=no_package_digest)
    else:
        context.workflow_test.process_report(update_provider_delivery=True, provider_delivery=False, unset_package_digest=no_package_digest)

@then(u'the "{index_file}" is updated with an entry for the submitted chart')
def index_file_is_updated(context, index_file):
    context.workflow_test.secrets.index_file = index_file
    context.workflow_test.check_index_yaml(True)

@given(u'the report includes "{tested}" and "{supported}" OpenshiftVersion values and chart "{kubeversion}" value')
def report_includes_specified_versions(context, tested, supported, kubeversion):
    context.workflow_test.process_report(update_versions=True, supported_versions=supported, tested_version=tested, kube_version=kubeversion)

@given(u'the report has a "{check}" missing')
def report_has_a_check_missing(context, check):
    context.workflow_test.process_report(missing_check=check)