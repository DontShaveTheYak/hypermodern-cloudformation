import os
from pathlib import Path
from typing import Dict, List

import pytest

from cloud_radar.cf.e2e._stack import Stack

@pytest.fixture(scope='session')
def template_path() -> Path:
    base_path = Path(__file__).parent
    template_path = base_path / Path('../../templates/log-bucket.template.yaml')
    return template_path.resolve()


@pytest.fixture()
def default_params() -> Dict[str, str]:
    parameters = {
        "BucketPrefix": "taskcat-$[taskcat_random-string]",
        "KeepBucket": "FALSE",
    }

    return parameters


@pytest.fixture()
def regions() -> List[str]:
    return ["us-west-1", "us-west-2"]


@pytest.mark.e2e
def test_ephemeral_bucket(template_path: Path, default_params, regions):

    buckets = []

    with Stack(template_path, default_params, regions) as stacks:

        for stack in stacks:

            session = stack.region.session

            s3 = session.resource("s3")

            bucket_name = ""

            for output in stack.outputs:

                if output.key == "LogsBucketName":
                    bucket_name = output.value
                    break


            bucket = s3.Bucket(bucket_name)
            bucket.wait_until_exists()
            buckets.append(bucket)

        assert len(stacks) == 2

    for bucket in buckets:
        bucket.wait_until_not_exists()

@pytest.mark.e2e
def test_retain_bucket(template_path: Path, default_params, regions):

    default_params["KeepBucket"] = "TRUE"

    with Stack(template_path, default_params, regions) as stacks:
        pass

    for stack in stacks:
        session = stack.region.session

        s3 = session.resource("s3")

        for output in stack.outputs:

            if output.key == "LogsBucketName":
                bucket = s3.Bucket(output.value)
                bucket.wait_until_exists()
                bucket.delete()
                bucket.wait_until_not_exists()
                break

    assert len(stacks) == 2
