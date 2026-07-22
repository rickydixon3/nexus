import json
import boto3

_client = boto3.client("secretsmanager")
_cache = {}


def get_secret(secret_id):
    """Fetch and parse a JSON secret from Secrets Manager, with per-invocation caching."""
    if secret_id in _cache:
        return _cache[secret_id]

    response = _client.get_secret_value(SecretId=secret_id)
    secret = json.loads(response["SecretString"])
    _cache[secret_id] = secret
    return secret