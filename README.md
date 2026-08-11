# Nexus

A serverless RAG news platform on AWS that ingests, embeds, and clusters articles from multiple sources with pgvector, answering questions with cited, grounded responses.

**Live:** [nexusnews.dev](https://nexusnews.dev)

---

## Overview

Nexus runs two things: a fully autonomous ingestion pipeline that pulls, normalizes, and embeds articles from three news APIs on a schedule, and a query layer that answers questions using retrieval-augmented generation over that data. And a React frontend provides a chat interface for asking questions and a filterable feed for browsing the raw article corpus.

---

## Architecture

### Ingestion & processing pipeline

<!---![Ingestion pipeline architecture](docs/architecture-ingestion.png)--->

EventBridge triggers a Lambda that pulls new articles from three APIs into S3. A second Lambda normalizes and deduplicates them into RDS. A third chunks and embeds the content via OpenAI, then clusters near-duplicate coverage of the same event using pgvector cosine similarity. The three functions are chained via direct Lambda invocation, so the pipeline runs end-to-end from one scheduled trigger, with no manual steps.

### Live deployment & query path

<!---![Deployment and query path architecture](docs/architecture-deployment.png)--->

The frontend is built and deployed as static files to S3, served through CloudFront with a custom domain and TLS certificate. The app calls API Gateway, which routes to two Lambdas — one for retrieval-augmented question answering, one for the article feed. Both query RDS directly; the query-answering Lambda calls OpenAI twice per request, once to embed the question and once to generate the answer.

---

## Features

**Ask — retrieval-augmented Q&A**
- Multi-turn chat interface
- Retrieval adapts to query shape: broad questions collapse redundant coverage of one story down to a single representative source; narrow questions about a specific event surface multiple outlets' takes on it
- A dedicated LLM classifier detects "what's happening lately" queries and routes them to a recency-ordered retrieval path instead of similarity search
- Answers are grounded in and cited from real retrieved articles; the model explicitly says so when the corpus doesn't have enough information, rather than answering from general knowledge

**Browse — live filterable feed**
- Dense list view with source and category filters
- Infinite scroll with cursor-based pagination
- Detects and discards reused generic publisher logos (common with aggregator sources), falling back to a source-colored indicator instead

**Fully autonomous pipeline**
- Ingests from three production news APIs on a schedule, no manual intervention
- Deduplicates near-identical coverage across outlets via vector similarity clustering, with a threshold tuned empirically against real article pairs rather than borrowed from general literature

---

## Tech stack

**Backend**
- Python
- AWS Lambda — 5 functions (ingest, normalize, embed, ragHandler, listArticles)
- Amazon EventBridge — scheduled pipeline trigger
- Amazon S3 — raw article storage
- Amazon RDS (PostgreSQL) with pgvector — article/chunk storage and vector search
- AWS Secrets Manager — API keys and DB credentials
- Amazon API Gateway — REST endpoints
- Serverless Framework — infrastructure as code

**AI / retrieval**
- OpenAI Embeddings API (`text-embedding-3-small`)
- OpenAI Chat Completions API — answer generation and query classification

**Frontend**
- React + TypeScript, Vite

**Deployment**
- Amazon S3 — static hosting
- Amazon CloudFront — CDN and TLS termination
- AWS Certificate Manager — TLS certificate
- Cloudflare — domain registration and DNS

---

## File structure

```
nexus/
├── ingest.py                  # Pulls new articles from Guardian, NYT, Currents
├── normalize.py                # Maps fields, dedupes, writes to RDS
├── embed.py                    # Chunks, embeds, and clusters articles
├── rag_handler.py               # Retrieval-augmented Q&A endpoint
├── list_articles.py             # Filterable article feed endpoint
├── common/
│   ├── secrets.py               # Secrets Manager helper
│   ├── s3_utils.py              # S3 read/write helpers
│   ├── chunking.py              # Content-aware chunking logic
│   └── sources/
│       ├── guardian.py
│       ├── nyt.py
│       └── currents.py
├── serverless.yml               # Infrastructure as code (Lambda, API Gateway, EventBridge)
├── requirements.txt
└── nexus-frontend/
    ├── src/
    │   ├── api/                 # Typed fetch wrappers for the backend
    │   ├── components/          # ChatThread, ArticleFeed, FilterBar, etc.
    │   ├── hooks/                # Shared React hooks
    │   ├── types/                # Shared TypeScript types
    │   ├── App.tsx
    │   └── index.css
    └── package.json
```

---

## Key technical decisions

**Story clustering threshold**. Standard guidance points to around 0.85 to 0.90 cosine similarity for catching duplicate content, but that didn't hold up against real article pairs. Actual same-event coverage from different outlets scored closer to 0.65 to 0.70, since full articles naturally score lower than the short snippets those published thresholds were validated on. The threshold got set to 0.65 based on that. The tradeoff is that whole-article similarity is a fairly blunt way to detect "same specific event," so it can miss loose duplicates or occasionally merge stories that are related but genuinely distinct.

**Retrieval branches on how concentrated the results are.** Instead of deciding upfront whether a question is broad or specific, retrieval pulls a wide set of candidates first, then checks how many cluster around the same story. If most of them do, the question is probably about that one event, so the response pulls in different outlets covering it. If they're spread across many stories, the question is broad, so each story only contributes its single best match, keeping the results from being crowded out by repeat coverage of one thing.

**A dedicated LLM classifier for recency intent.** Similarity search doesn't work for questions like "what's happened recently," since there's no specific topic to match against. A quick classification call catches these and sends them down a separate path that just orders by date instead, chosen over keyword matching so it still catches oddly phrased or misspelled versions of the same question.

**Chunking follows content shape, not just by source.** Standard articles are chunked by grouping paragraphs together, splitting at sentence boundaries when one gets too long. Guardian's liveblogs split differently, by timestamped update, since each update stands on its own. NYT and Currents only give short abstracts, so those stay as a single chunk. Anything marked interactive gets dropped entirely at ingestion, since the API only returns a placeholder for that content, not real text.

---

## Known limitations

- **Retrieval is recency-blind outside the dedicated recency path.** Similarity search has no concept of "newer is better" a highly relevant older article can outrank a slightly less relevant recent one for a standard topical query.
- **Story clustering is blunt** Clear matches and clear non-matches separate well; closely related but genuinely distinct stories within the same broader event aren't always separated reliably.
- **Currents API data quality varies.** As an aggregator of many third-party publishers, a meaningful share of its content is templated financial alerts or reused generic publisher branding rather than original editorial content or real per-article images.
- **Category values are unstandardized across sources.** Each source's own taxonomy is stored as-is ("Sport", "sport", and "Football" all exist as distinct values). The Browse filter caps the list to the most frequent values to stay usable, but doesn't merge near-duplicates.
- **No conversation memory in the query layer.** The chat interface shows a multi-turn thread, but each question is currently answered independently. A follow-up doesn't carry prior context into retrieval or generation.

---

## Local setup

**Backend**
```bash
git clone https://github.com/rickydixon3/nexus.git
cd nexus
pip install -r requirements.txt --break-system-packages
serverless deploy
```
Requires AWS credentials configured locally, and API keys for Guardian, NYT, Currents, and OpenAI stored in Secrets Manager under `nexus/api-keys` and `nexus/db-credentials`.

**Frontend**
```bash
cd nexus-frontend
npm install
echo "VITE_API_URL=<your-api-gateway-url>" > .env
npm run dev
```

---
