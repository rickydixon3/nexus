from datetime import datetime, timezone

import psycopg2
from pgvector import Vector
from pgvector.psycopg2 import register_vector
import openai

from common.secrets import get_secret
from common.chunking import chunk_article, chunk_summary

SIMILARITY_THRESHOLD = 0.65
EMBEDDING_MODEL = "text-embedding-3-small"


def _get_db_connection():
    creds = get_secret("nexus/db-credentials")
    conn = psycopg2.connect(
        host="nexus-db.cez2segysfth.us-east-1.rds.amazonaws.com",
        dbname="postgres",
        user=creds["username"],
        password=creds["password"],
        sslmode="require",
    )
    register_vector(conn)
    return conn


def _get_unembedded_articles(cursor):
    cursor.execute(
        """
        SELECT id, body, source, content_type
        FROM articles
        WHERE is_embedded = FALSE
        """
    )
    return cursor.fetchall()


def _chunk_body(body, source, content_type):
    if source == "guardian":
        return chunk_article(content_type, body)
    return chunk_summary(body)


def _embed_chunks(client, chunk_texts):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=chunk_texts,
    )
    return [item.embedding for item in response.data]


def _find_cluster(cursor, representative_embedding):
    vec = Vector(representative_embedding)
    cursor.execute(
        """
        SELECT id, story_cluster_id, 1 - (embedding <=> %s::vector) AS similarity
        FROM articles
        WHERE published_at > now() - interval '3 days'
          AND embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 1
        """,
        (vec, vec),
    )
    result = cursor.fetchone()

    if not result:
        return None

    matched_id, matched_cluster_id, similarity = result
    if similarity >= SIMILARITY_THRESHOLD:
        return matched_cluster_id if matched_cluster_id else matched_id

    return None


def _insert_chunks(cursor, article_id, chunk_texts, chunk_embeddings):
    for index, (text, embedding) in enumerate(zip(chunk_texts, chunk_embeddings)):
        cursor.execute(
            """
            INSERT INTO chunks (article_id, chunk_index, chunk_text, embedding, embedding_model)
            VALUES (%s, %s, %s, %s::vector, %s)
            """,
            (article_id, index, text, Vector(embedding), EMBEDDING_MODEL),
        )


def _update_article(cursor, article_id, representative_embedding, story_cluster_id):
    cursor.execute(
        """
        UPDATE articles
        SET embedding = %s::vector,
            embedding_model = %s,
            story_cluster_id = %s,
            is_embedded = TRUE
        WHERE id = %s
        """,
        (Vector(representative_embedding), EMBEDDING_MODEL, story_cluster_id, article_id),
    )


def embed(event, context):
    api_keys = get_secret("nexus/api-keys")
    client = openai.OpenAI(api_key=api_keys["openai_api_key"])

    conn = _get_db_connection()
    cursor = conn.cursor()

    counts = {"processed": 0, "skipped_no_content": 0, "failed": 0, "clustered": 0}

    articles = _get_unembedded_articles(cursor)

    for article_id, body, source, content_type in articles:
        try:
            chunk_texts = _chunk_body(body, source, content_type)

            if not chunk_texts:
                counts["skipped_no_content"] += 1
                cursor.execute(
                    "UPDATE articles SET is_embedded = TRUE WHERE id = %s",
                    (article_id,),
                )
                conn.commit()
                continue

            chunk_embeddings = _embed_chunks(client, chunk_texts)
            representative_embedding = chunk_embeddings[0]

            story_cluster_id = _find_cluster(cursor, representative_embedding)
            if story_cluster_id:
                counts["clustered"] += 1

            _insert_chunks(cursor, article_id, chunk_texts, chunk_embeddings)
            _update_article(cursor, article_id, representative_embedding, story_cluster_id)

            conn.commit()
            counts["processed"] += 1

        except Exception as e:
            conn.rollback()
            counts["failed"] += 1
            print(f"Failed on article {article_id}: {e}")

    cursor.close()
    conn.close()

    return {
        "statusCode": 200,
        "body": counts,
    }