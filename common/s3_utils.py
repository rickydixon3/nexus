import json
import boto3

_client = boto3.client("s3")


def put_json(bucket, key, data):
    """Write a Python dict/list to S3 as JSON."""
    _client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data).encode("utf-8"),
        ContentType="application/json",
    )


def get_json(bucket, key):
    """Read and parse a JSON object from S3."""
    response = _client.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())