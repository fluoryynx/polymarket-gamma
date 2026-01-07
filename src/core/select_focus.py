def pick_focus(candidates):
    """Select 1 crypto and 1 sports market from candidates."""
    crypto_keywords = ["crypto", "bitcoin", "ethereum", "btc", "eth", "cryptocurrency"]
    sports_keywords = ["sport", "football", "basketball", "soccer", "tennis", "baseball", "hockey", "nfl"]
    
    crypto = None
    sports = None
    
    for market in candidates:
        category_lower = (market.category or "").lower()
        question_lower = (market.question or "").lower()
        
        # Check if it's a crypto market
        if crypto is None:
            for keyword in crypto_keywords:
                if keyword in category_lower or keyword in question_lower:
                    crypto = market
                    break
        
        # Check if it's a sports market
        if sports is None:
            for keyword in sports_keywords:
                if keyword in category_lower or keyword in question_lower:
                    sports = market
                    break
        
        # If we found both, we can stop searching
        if crypto and sports:
            break
    
    result = []
    if crypto:
        result.append(crypto)
    if sports:
        result.append(sports)
    return result
