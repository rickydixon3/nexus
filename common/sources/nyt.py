import time
import requests

BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
REQUEST_DELAY_SECONDS = 20
MAX_RETRIES = 3


def fetch_articles(api_key, from_date, to_date):
    """
    Fetch all NYT articles published between from_date and to_date
    (YYYYMMDD strings), handling pagination.
    NYT returns max 10 results per page, up to 100 pages (1000 results) per query.
    Rate-limited to ~5 requests/minute, so requests are paced with a delay.
    """
    all_results = []
    page = 0

    while True:
        params = {
            "api-key": api_key,
            "begin_date": from_date,
            "end_date": to_date,
            "sort": "newest",
            "page": page,
        }

        print(f"NYT requesting page {page}")
        response = _get_with_retry(params)

        payload = response.json()["response"]
        all_results.extend(payload["docs"])
        print(f"NYT page {page} done, total so far {len(all_results)}")

        hits = payload["metadata"]["hits"]
        if (page + 1) * 10 >= hits or page >= 99:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_results


def _get_with_retry(params):
    last_response = None
    for attempt in range(MAX_RETRIES):
        response = requests.get(BASE_URL, params=params)
        last_response = response

        if response.status_code != 429:
            response.raise_for_status()
            return response

        wait = int(response.headers.get("Retry-After", REQUEST_DELAY_SECONDS * (attempt + 1)))
        print(f"NYT 429 on page {params['page']}, attempt {attempt + 1}/{MAX_RETRIES}, waiting {wait}s")
        time.sleep(wait)

    print(f"NYT still rate-limited after {MAX_RETRIES} attempts, giving up on page {params['page']}")
    last_response.raise_for_status()
    return last_response