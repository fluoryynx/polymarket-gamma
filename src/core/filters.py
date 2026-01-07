from src.core.parse import hours_to_close, parse_yes_no


def is_candidate(market):
    """Filter markets for 48h active YES/NO with order book"""
    if not market.get("enableOrderBook", False):
        return False
    if not market.get("active", False) or market.get("closed", False):
        return False
    hours = hours_to_close(market.get("endDate"))
    if hours is None or not (0 < hours <= 48):
        return False
    yes_price, no_price, yes_token, no_token, invalid = parse_yes_no(market)
    if not yes_token or not no_token:
        return False
    return True
