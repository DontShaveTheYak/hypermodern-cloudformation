from pathlib import Path

import pytest

from cloud_radar.cf.unit import Template


@pytest.fixture(scope='session')
def template_path() -> Path:
    base_path = Path(__file__).parent
    template_path = base_path / Path('../../templates/log-bucket.template.yaml')
    return template_path.resolve()


def test_ephemeral_bucket(template_path: Path):

    # Create a Template object using the path
    # to a Cloudformation template.
    template = Template.from_yaml(template_path)

    prefix = "hypermodern-cf"
    region = "us-west-2"

    # Create a dictionary of parameters for our template.
    params = {"BucketPrefix": prefix, "KeepBucket": "FALSE"}

    # Render the template using our parameters and region.
    result = template.render(params, region)

    # Make sure the correct resources are being created.
    assert "RetainLogsBucket" not in result["Resources"]
    assert "RetainLogsBucketPolicy" not in result["Resources"]
    assert "LogsBucket" in result["Resources"]
    assert "LogsBucketPolicy" in result["Resources"]

    # Test LogsBucket
    logs_bucket = result["Resources"]['LogsBucket']
    bucket_name = logs_bucket['Properties']['BucketName']

    assert prefix in bucket_name
    assert region in bucket_name

    # Test Bucket Policy
    policy_resource = result["Resources"]['LogsBucketPolicy']
    attached_bucket = policy_resource['Properties']['Bucket']
    statement = policy_resource['Properties']['PolicyDocument']['Statement'][0]

    assert attached_bucket == 'LogsBucket'
    assert 'LogsBucket/*' in statement['Resource']
    assert template.AccountId in statement['Principal']['AWS']

    # Test outputs
    bucket_output = result['Outputs']['LogsBucketName']

    assert bucket_output['Value'] == 'LogsBucket'
    assert prefix in bucket_output['Export']['Name']

def test_retains_bucket(template_path: Path):

    # Create a Template object using the path
    # to a Cloudformation template.
    template = Template.from_yaml(template_path)

    prefix = "hypermodern-cf"
    region = "us-west-2"

    # Create a dictionary of parameters for our template.
    params = {"BucketPrefix": prefix, "KeepBucket": "TRUE"}

    # Render the template using our parameters and region.
    result = template.render(params, region)

    # Make sure the correct resources are being created.
    assert "RetainLogsBucket" in result["Resources"]
    assert "RetainLogsBucketPolicy" in result["Resources"]
    assert "LogsBucket" not in result["Resources"]
    assert "LogsBucketPolicy" not in result["Resources"]

    # Test LogsBucket
    logs_bucket = result["Resources"]['RetainLogsBucket']
    bucket_name = logs_bucket['Properties']['BucketName']

    assert prefix in bucket_name
    assert region in bucket_name

    # Test Bucket Policy
    policy_resource = result["Resources"]['RetainLogsBucketPolicy']
    attached_bucket = policy_resource['Properties']['Bucket']
    statement = policy_resource['Properties']['PolicyDocument']['Statement'][0]

    assert attached_bucket == 'RetainLogsBucket'
    assert 'LogsBucket/*' in statement['Resource']
    assert template.AccountId in statement['Principal']['AWS']

    # Test outputs
    bucket_output = result['Outputs']['LogsBucketName']

    assert bucket_output['Value'] == 'RetainLogsBucket'
    assert prefix in bucket_output['Export']['Name']
