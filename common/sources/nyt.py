import time
import requests

BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
REQUEST_DELAY_SECONDS = 20 # stay under NYT's ~5 requests/minute limit


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

        response = requests.get(BASE_URL, params=params)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", REQUEST_DELAY_SECONDS))
            time.sleep(retry_after)
            response = requests.get(BASE_URL, params=params)

        response.raise_for_status()
        payload = response.json()["response"]

        all_results.extend(payload["docs"])

        hits = payload["metadata"]["hits"]
        if (page + 1) * 10 >= hits or page >= 99:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_results