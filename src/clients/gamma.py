import requests

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"

def fetch_markets(limit=None, offset=None):
    """Fetch markets with optional pagination."""
    params = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    
    resp = requests.get(GAMMA_MARKETS_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return []
