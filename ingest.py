import json
from datetime import datetime, timedelta, timezone

from common.secrets import get_secret
from common.s3_utils import put_json
from common.sources import guardian, nyt, currents

import boto3

lambda_client = boto3.client("lambda")

RAW_BUCKET = "nexus-raw-articles-rickydixon3"
DEFAULT_WINDOW_HOURS = 6


def ingest(event, context):
    print("ingest function started")
    now = datetime.now(timezone.utc)

    from_date = event.get("from_date") if event else None
    to_date = event.get("to_date") if event else None

    if not from_date:
        from_date = (now - timedelta(hours=DEFAULT_WINDOW_HOURS))
    else:
        from_date = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if not to_date:
        to_date = now
    else:
        to_date = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    api_keys = get_secret("nexus/api-keys")
    print("Secrets retrieved successfully")
    timestamp = now.strftime('%Y-%m-%dT%H-%M-%S')
    summary = []
    any_succeeded = False

    sources = [
        ("guardian", guardian, api_keys["guardian_api_key"], "%Y-%m-%d"),
        ("nyt", nyt, api_keys["nyt_api_key"], "%Y%m%d"),
        ("currents", currents, api_keys["currents_api_key"], "%Y-%m-%dT%H:%M:%SZ"),
    ]

    for name, module, key, fmt in sources:
        try:
            articles = module.fetch_articles(
                key,
                from_date.strftime(fmt),
                to_date.strftime(fmt),
            )
            print(f"{name} done: {len(articles)} articles")
            put_json(RAW_BUCKET, f"{name}/{timestamp}.json", articles)
            summary.append(f"{len(articles)} {name} articles")
            any_succeeded = True
        except Exception as e:
            print(f"{name} ingest failed: {e}")
            summary.append(f"{name} failed: {e}")

    if any_succeeded:
        lambda_client.invoke(
            FunctionName="nexus-dev-normalize",
            InvocationType="Event",
            Payload=json.dumps({"timestamp": timestamp}).encode("utf-8"),
        )
        print("Triggered normalize")
    else:
        print("All sources failed, normalize not triggered")

    return {
        "statusCode": 200,
        "body": f"Ingested: {', '.join(summary)}",
    }