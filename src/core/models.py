from dataclasses import dataclass
from typing import Optional, List

@dataclass
class MarketRecord:
    id: str
    slug: Optional[str]
    question: Optional[str]
    category: Optional[str]
    endDate: Optional[str]
    hours_to_close: Optional[float]
    enableOrderBook: bool
    active: bool
    closed: bool
    yes_token_id: Optional[str]
    no_token_id: Optional[str]
    yes_price: Optional[float]
    no_price: Optional[float]
    invalid_reason: Optional[str]
    clob_token_ids: Optional[List[str]] = None
