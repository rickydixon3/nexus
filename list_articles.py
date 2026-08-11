import json

import psycopg2

from common.secrets import get_secret

DEFAULT_LIMIT = 20
MAX_LIMIT = 50


def _get_db_connection():
    creds = get_secret("nexus/db-credentials")
    return psycopg2.connect(
        host="nexus-db.cez2segysfth.us-east-1.rds.amazonaws.com",
        dbname="postgres",
        user=creds["username"],
        password=creds["password"],
        sslmode="require",
    )


def _get_articles(cursor, source, category, limit, offset):
    conditions = []
    params = []

    if source:
        conditions.append("source = %s")
        params.append(source)

    if category:
        conditions.append("category = %s")
        params.append(category)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT id, title, source, url, published_at, category, image_url
        FROM articles
        {where_clause}
        ORDER BY published_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    return cursor.fetchall()

def _get_distinct_categories(cursor):
    cursor.execute(
        """
        SELECT category
        FROM articles
        WHERE category IS NOT NULL
        GROUP BY category
        HAVING COUNT(*) >= 5
        ORDER BY COUNT(*) DESC
        LIMIT 15
        """
    )
    return [row[0] for row in cursor.fetchall()]


def list_articles(event, context):
    params = event.get("queryStringParameters") or {}

    source = params.get("source")
    category = params.get("category")

    if params.get("meta") == "categories":
        try:
            conn = _get_db_connection()
            cursor = conn.cursor()
            categories = _get_distinct_categories(cursor)
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"listArticles categories query failed: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to fetch categories"}),
            }
        return {
            "statusCode": 200,
            "body": json.dumps({"categories": categories}),
        }

    try:
        limit = min(int(params.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)
        offset = max(int(params.get("offset", 0)), 0)
    except ValueError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "limit and offset must be integers"}),
        }

    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        rows = _get_articles(cursor, source, category, limit, offset)
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"listArticles query failed: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch articles"}),
        }

    articles = [
        {
            "id": str(row[0]),
            "title": row[1],
            "source": row[2],
            "url": row[3],
            "published_at": row[4].isoformat(),
            "category": row[5],
            "image_url": row[6],
        }
        for row in rows
    ]

    return {
        "statusCode": 200,
        "body": json.dumps({"articles": articles, "limit": limit, "offset": offset}),
    }