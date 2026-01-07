from datetime import datetime, timezone
import json

def hours_to_close(end_date_str):
    if not end_date_str:
        return None
    try:
        end_dt = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = end_dt - now
        hours = delta.total_seconds() / 3600
        return round(hours, 2)
    except:
        return None

def parse_yes_no(market: dict):
    """Extract YES/NO prices and token IDs safely"""
    invalid_reason = None
    yes_price = no_price = None
    yes_token = no_token = None

    # Parse outcomes
    outcomes = market.get("outcomes")
    if outcomes is None:
        outcomes = []
        invalid_reason = "missing outcomes"
    elif isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except:
            outcomes = []
            invalid_reason = "invalid outcomes JSON"

    # Parse outcomePrices
    outcomePrices = market.get("outcomePrices")
    if outcomePrices is None:
        outcomePrices = []
        if not invalid_reason:  # Only set if not already set
            invalid_reason = "missing outcomePrices"
    elif isinstance(outcomePrices, str):
        try:
            outcomePrices = json.loads(outcomePrices)
        except:
            outcomePrices = []
            invalid_reason = "invalid outcomePrices JSON"

    # Parse token IDs - prioritize clobTokenIds, fallback to conditionId if needed
    token_ids = market.get("clobTokenIds")
    if token_ids is None:
        # Fallback to conditionId for gamma pricing (single ID, need to duplicate for YES/NO)
        condition_id = market.get("conditionId")
        if condition_id:
            token_ids = [condition_id, condition_id]  # Duplicate for YES/NO if needed
        else:
            token_ids = []
            if not invalid_reason:  # Only set if not already set
                invalid_reason = "missing clobTokenIds and conditionId"
    elif isinstance(token_ids, str):
        try:
            token_ids = json.loads(token_ids)
        except:
            token_ids = []
            invalid_reason = "invalid clobTokenIds JSON"

    # Check binary YES/NO
    if len(outcomes) != 2 or len(outcomePrices) != 2 or len(token_ids) != 2:
        invalid_reason = "not binary YES/NO"
    else:
        try:
            yes_idx = 0 if outcomes[0].lower() == "yes" else 1
            no_idx = 1 - yes_idx
            yes_token = token_ids[yes_idx]
            no_token = token_ids[no_idx]
            
            yes_price = float(outcomePrices[yes_idx])
            no_price = float(outcomePrices[no_idx])
        except (ValueError, TypeError):  # Only catch price conversion errors
            invalid_reason = f"invalid price: could not convert prices {outcomePrices}"
            yes_price = no_price = None
            yes_token = no_token = None  # Also reset tokens if prices are invalid
        except Exception as e:
            invalid_reason = f"invalid price: {str(e)}"
            yes_price = no_price = None
            yes_token = no_token = None  # Also reset tokens if there's an error

    return yes_price, no_price, yes_token, no_token, invalid_reason
