import requests
from typing import List, Dict, Any, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams


class ClobAPIClient:
    """Client for interacting with Polymarket CLOB API"""
    
    def __init__(self, base_url: str = "https://clob.polymarket.com"):
        self.client = ClobClient(base_url)
    
    def get_order_book(self, token_id: str) -> Dict[str, Any]:
        """
        Get order book for a specific token
        
        Args:
            token_id: The token ID to fetch order book for
            
        Returns:
            Dict containing order book data with bids and asks
        """
        return self.client.get_order_book(token_id)
    
    def get_order_books(self, token_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get order books for multiple tokens
        
        Args:
            token_ids: List of token IDs to fetch order books for
            
        Returns:
            List of order book data
        """
        book_params = [BookParams(token_id=token_id) for token_id in token_ids]
        return self.client.get_order_books(book_params)
    
    def get_midpoint(self, token_id: str) -> Optional[float]:
        """
        Get midpoint price for a token
        
        Args:
            token_id: The token ID to get midpoint for
            
        Returns:
            Midpoint price or None if error
        """
        try:
            return self.client.get_midpoint(token_id)
        except:
            return None
    
    def get_price(self, token_id: str, side: str) -> Optional[float]:
        """
        Get price for a token on a specific side (BUY/SELL)
        
        Args:
            token_id: The token ID to get price for
            side: "BUY" or "SELL"
            
        Returns:
            Price or None if error
        """
        try:
            return self.client.get_price(token_id, side=side)
        except:
            return None
    
    def get_best_bid_ask(self, token_id: str) -> Dict[str, Optional[float]]:
        """
        Get both best bid and ask prices for a token
        
        Args:
            token_id: The token ID to get bid/ask for
            
        Returns:
            Dict with 'bid' and 'ask' prices
        """
        bid_price = self.get_price(token_id, side="BUY")  # BUY is for getting price to sell at (bid)
        ask_price = self.get_price(token_id, side="SELL")  # SELL is for getting price to buy at (ask)
        
        return {
            "bid": bid_price,
            "ask": ask_price
        }
