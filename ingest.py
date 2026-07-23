from datetime import datetime, timedelta, timezone

from common.secrets import get_secret
from common.s3_utils import put_json
from common.sources import guardian, nyt, currents

RAW_BUCKET = "nexus-raw-articles-rickydixon3"
DEFAULT_WINDOW_HOURS = 6


def ingest(event, context):
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
    timestamp = now.strftime('%Y-%m-%dT%H-%M-%S')
    summary = []

    # The Guardian
    guardian_articles = guardian.fetch_articles(
        api_keys["guardian_api_key"],
        from_date.strftime("%Y-%m-%d"),
        to_date.strftime("%Y-%m-%d"),
    )
    put_json(RAW_BUCKET, f"guardian/{timestamp}.json", guardian_articles)
    summary.append(f"{len(guardian_articles)} Guardian articles")

    # New York Times
    nyt_articles = nyt.fetch_articles(
        api_keys["nyt_api_key"],
        from_date.strftime("%Y%m%d"),
        to_date.strftime("%Y%m%d"),
    )
    put_json(RAW_BUCKET, f"nyt/{timestamp}.json", nyt_articles)
    summary.append(f"{len(nyt_articles)} NYT articles")

    # Currents News
    currents_articles = currents.fetch_articles(
        api_keys["currents_api_key"],
        from_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        to_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    put_json(RAW_BUCKET, f"currents/{timestamp}.json", currents_articles)
    summary.append(f"{len(currents_articles)} Currents articles")

    return {
        "statusCode": 200,
        "body": f"Ingested: {', '.join(summary)}",
    }