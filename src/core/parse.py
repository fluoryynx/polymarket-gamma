import json
from datetime import datetime, timezone
from dateutil.parser import isoparse

def _ensure_list(x):
    if x is None:
        return None
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return None
    return None

def parse_yes_no(market: dict):
    outcomes = _ensure_list(market.get("outcomes"))
    prices = _ensure_list(market.get("outcomePrices"))
    token_ids = _ensure_list(market.get("clobTokenIds"))

    if not outcomes or len(outcomes) != 2:
        return None, None, None, None, "Not binary outcomes"

    mapping = {}
    for i, o in enumerate(outcomes):
        key = o.lower()
        mapping[key] = i

    if "yes" not in mapping or "no" not in mapping:
        return None, None, None, None, "Cannot identify Yes/No"

    try:
        yes_price = float(prices[mapping["yes"]]) if prices else None
        no_price = float(prices[mapping["no"]]) if prices else None
    except Exception:
        yes_price, no_price = None, None

    try:
        yes_token = token_ids[mapping["yes"]] if token_ids else None
        no_token = token_ids[mapping["no"]] if token_ids else None
    except Exception:
        yes_token, no_token = None, None

    return yes_price, no_price, yes_token, no_token, None

def hours_to_close(end_date: str):
    try:
        end = isoparse(end_date)
        now = datetime.now(timezone.utc)
        return round((end - now).total_seconds() / 3600, 2)
    except Exception:
        return None
