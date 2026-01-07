def pick_focus(markets):
    crypto = None
    sports = None

    for m in markets:
        cat = (m.category or "").lower()
        if not crypto and "crypto" in cat:
            crypto = m
        elif not sports and "sport" in cat:
            sports = m

    return [m for m in (crypto, sports) if m]
