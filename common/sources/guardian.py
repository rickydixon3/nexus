import requests

BASE_URL = "https://content.guardianapis.com/search"


def fetch_articles(api_key, from_date, to_date, page_size=200):
    """
    Fetch all Guardian articles published between from_date and to_date
    (ISO 8601 strings), handling pagination if results exceed one page.
    """
    all_results = []
    page = 1

    while True:
        params = {
            "api-key": api_key,
            "from-date": from_date,
            "to-date": to_date,
            "page-size": page_size,
            "page": page,
            "order-by": "newest",
            "show-fields": "body,byline,thumbnail",
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()["response"]

        all_results.extend(payload["results"])

        if page >= payload["pages"]:
            break
        page += 1

    return all_results