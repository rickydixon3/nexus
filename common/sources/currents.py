import requests

BASE_URL = "https://api.currentsapi.services/v2/search"
MAX_FREE_TIER_RESULTS = 100
PAGE_SIZE = 20


def fetch_articles(api_key, from_date, to_date):
    """
    Fetch Currents articles published between from_date and to_date
    (RFC 3339 timestamp strings), handling cursor-based pagination.
    Free tier caps page_size at 20 and total retrievable results at 100.
    """
    all_results = []
    cursor = None

    while True:
        params = {
            "apiKey": api_key,
            "language": "en",
            "start_date": from_date,
            "end_date": to_date,
            "page_size": PAGE_SIZE,
        }
        if cursor:
            params["cursor"] = cursor

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()

        all_results.extend(payload["news"])

        if len(all_results) >= MAX_FREE_TIER_RESULTS:
            break

        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) <= 0:
            break

        cursor = payload.get("next_cursor")
        if not cursor:
            break

    return all_results