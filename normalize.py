import hashlib
import json
from datetime import datetime, timezone

import psycopg2

from common.secrets import get_secret
from common.s3_utils import get_json

import boto3

lambda_client = boto3.client("lambda")

RAW_BUCKET = "nexus-raw-articles-rickydixon3"


def _get_db_connection():
    creds = get_secret("nexus/db-credentials")
    return psycopg2.connect(
        host="nexus-db.cez2segysfth.us-east-1.rds.amazonaws.com",
        dbname="postgres",
        user=creds["username"],
        password=creds["password"],
    )


def _parse_currents_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %z")


def _normalize_guardian(raw):
    if raw.get("type") == "interactive":
        return None

    fields = raw.get("fields", {})
    return {
        "title": raw.get("webTitle"),
        "body": fields.get("body"),
        "source": "guardian",
        "author": fields.get("byline"),
        "url": raw.get("webUrl"),
        "category": raw.get("sectionName"),
        "published_at": datetime.fromisoformat(raw["webPublicationDate"].replace("Z", "+00:00")),
        "content_type": raw.get("type"),
        "image_url": fields.get("thumbnail"),
    }


def _normalize_nyt(raw):
    if raw.get("document_type") == "interactive":
        return None

    headline = raw.get("headline", {})
    byline = raw.get("byline", {})
    body_parts = [raw.get("abstract", ""), raw.get("lead_paragraph", "")]
    body = " ".join(p for p in body_parts if p).strip()

    multimedia = raw.get("multimedia") or {}
    image_url = multimedia.get("default", {}).get("url")

    return {
        "title": headline.get("main"),
        "body": body,
        "source": "nyt",
        "author": byline.get("original"),
        "url": raw.get("web_url"),
        "category": raw.get("section_name"),
        "published_at": datetime.fromisoformat(raw["pub_date"].replace("Z", "+00:00")),
        "content_type": raw.get("document_type"),
        "image_url": image_url,
    }


def _normalize_currents(raw):
    category_list = raw.get("category", [])
    category = category_list[0] if category_list else None

    image = raw.get("image")
    image_url = None if image in (None, "None") else image

    return {
        "title": raw.get("title"),
        "body": raw.get("description"),
        "source": "currents",
        "author": raw.get("author"),
        "url": raw.get("url"),
        "category": category,
        "published_at": _parse_currents_date(raw["published"]),
        "content_type": None,
        "image_url": image_url,
    }


NORMALIZERS = {
    "guardian": _normalize_guardian,
    "nyt": _normalize_nyt,
    "currents": _normalize_currents,
}


def _insert_article(cursor, article):
    try:
        cursor.execute(
            """
            INSERT INTO articles (title, body, source, author, url, category, published_at, content_type, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                article["title"],
                article["body"],
                article["source"],
                article["author"],
                article["url"],
                article["category"],
                article["published_at"],
                article["content_type"],
                article["image_url"],
            ),
        )
        return "processed"
    except psycopg2.errors.UniqueViolation:
        cursor.connection.rollback()
        return "skipped_duplicate"


def normalize(event, context):
    timestamp = event["timestamp"]
    normalizer = None
    summary = {}

    conn = _get_db_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    for source in ("guardian", "nyt", "currents"):
        counts = {"processed": 0, "skipped_duplicate": 0, "skipped_interactive": 0, "failed": 0}

        try:
            raw_articles = get_json(RAW_BUCKET, f"{source}/{timestamp}.json")
        except Exception:
            summary[source] = counts
            continue

        normalizer = NORMALIZERS[source]

        for raw in raw_articles:
            try:
                article = normalizer(raw)
            except Exception:
                counts["failed"] += 1
                continue

            if article is None:
                counts["skipped_interactive"] += 1
                continue

            result = _insert_article(cursor, article)
            counts[result] += 1
            if result == "processed":
                conn.commit()

        summary[source] = counts

    cursor.close()
    conn.close()

    total_processed = sum(s["processed"] for s in summary.values())

    lambda_client.invoke(
            FunctionName="nexus-dev-embed",
            InvocationType="Event",
            Payload=b"{}",
        )

    return {
        "statusCode": 200,
        "body": {**summary, "total_processed": total_processed},
    }
