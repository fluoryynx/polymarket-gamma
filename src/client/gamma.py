import requests

BASE_URL = "https://gamma-api.polymarket.com"

def fetch_markets(limit=100, max_pages=5):
    all_markets = []
    offset = 0

    for _ in range(max_pages):
        resp = requests.get(
            f"{BASE_URL}/markets",
            params={"limit": limit, "offset": offset},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        if not data:
            break

        all_markets.extend(data)
        offset += limit

    return all_markets
