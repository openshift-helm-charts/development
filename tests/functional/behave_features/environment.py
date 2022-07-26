from behave import fixture, use_fixture
from common.utils.chart_certification import ChartCertificationE2ETestSingle

@fixture
def workflow_test(context):
    context.workflow_test = ChartCertificationE2ETestSingle(test_name=context.test_name)
    yield context.workflow_test
    context.workflow_test.cleanup()

def before_scenario(context, scenario):
    context.test_name = scenario.name.split('@')[0][:-4].split(']')[1]
    use_fixture(workflow_test, context)
