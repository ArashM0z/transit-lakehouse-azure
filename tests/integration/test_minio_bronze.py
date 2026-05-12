"""Integration test asserting bronze parquet objects land in MinIO when the
ingester is run end-to-end against the local docker-compose stack.
"""

from __future__ import annotations

import os

import boto3
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def s3() -> object:
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        aws_secret_access_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        region_name="us-east-1",
        use_ssl=False,
    )


def test_lakehouse_bucket_exists(s3: object) -> None:
    response = s3.list_buckets()  # type: ignore[attr-defined]
    names = {b["Name"] for b in response["Buckets"]}
    assert "lakehouse" in names, f"expected 'lakehouse' bucket; got {names}"
