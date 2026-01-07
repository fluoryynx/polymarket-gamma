def is_candidate(m):
    if not m.enableOrderBook:
        return False
    if not m.active or m.closed:
        return False
    if m.hours_to_close is None:
        return False
    if not (0 < m.hours_to_close <= 48):
        return False
    if not m.yes_token_id or not m.no_token_id:
        return False
    return True
