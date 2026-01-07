import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import json
import requests

from src.clients.gamma import fetch_markets
from src.clients.clob import ClobAPIClient
from src.core.parse import parse_yes_no, hours_to_close, hours_to_close


# API client for CLOB endpoints
class ClobAPI:
    """API client for CLOB endpoints that can be used within the Streamlit app"""
    
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
    
    def get_order_book(self, token_id: str):
        """GET /book?token_id=... - Read order book summary for a token"""
        try:
            response = requests.get(f"{self.base_url}/book", params={"token_id": token_id})
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def get_best_bid_ask_batch(self, requests_data: list):
        """POST /prices - Batch get best bid/ask for multiple tokens"""
        try:
            response = requests.post(f"{self.base_url}/prices", json={"requests": requests_data})
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    def get_best_bid_ask(self, token_id: str):
        """Get both best bid and ask for a single token using the batch endpoint"""
        result = self.get_best_bid_ask_batch([{"token_id": token_id, "side": "BUY"}, {"token_id": token_id, "side": "SELL"}])
        if "error" not in result:
            bid = None
            ask = None
            for res in result.get("results", []):
                if res.get("token_id") == token_id and res.get("side") == "BUY":
                    bid = res.get("price")
                elif res.get("token_id") == token_id and res.get("side") == "SELL":
                    ask = res.get("price")
            return {"bid": bid, "ask": ask}
        return result

st.set_page_config(page_title="Polymarket Dashboard", layout="wide")
st.title("Polymarket Market Dashboard")

@st.cache_data
def load_data(limit=None, offset=None):
    raw_markets = fetch_markets(limit=limit, offset=offset)  # markets with optional pagination
    clob_client = ClobAPIClient()  
    records = []

    for m in raw_markets:
        yes_price, no_price, yes_token, no_token, invalid_reason = parse_yes_no(m)
        hours = hours_to_close(m.get("endDate"))

        # Extract CLOB token IDs from the market data
        clob_token_ids_str = m.get("clobTokenIds", "[]")
        import ast
        try:
            clob_token_ids = ast.literal_eval(clob_token_ids_str) if isinstance(clob_token_ids_str, str) else clob_token_ids_str
        except:
            clob_token_ids = []

        records.append({
            "id": m.get("id"),
            "slug": m.get("slug"),
            "question": m.get("question"),
            "category": m.get("category"),
            "endDate": m.get("endDate"),
            "hours_to_close": hours,
            "enableOrderBook": m.get("fpmmLive", False),
            "active": m.get("active", False),
            "closed": m.get("closed", False),
            "yes_token_id": yes_token,
            "no_token_id": no_token,
            "yes_price": yes_price,
            "no_price": no_price,
            "invalid_reason": invalid_reason,
            "clob_token_ids": clob_token_ids
        })
    return records

# Add pagination controls
st.sidebar.header("Pagination Settings")
use_pagination = st.sidebar.checkbox("Use Pagination", value=False)
limit = None
offset = None

if use_pagination:
    limit = st.sidebar.number_input("Limit (items per page)", value=50, min_value=1, max_value=1000)
    offset = st.sidebar.number_input("Offset (starting position)", value=0, min_value=0)

# Load data
records = load_data(limit=limit, offset=offset)
df = pd.DataFrame(records)

st.sidebar.write(f"Loaded {len(records)} markets{' (with pagination)' if use_pagination else ''}")

# Store original unfiltered dataframe for "Show All Data" functionality
df_all = df.copy()

# Candidate filter - Updated to match option 3 requirements
def is_candidate(row):
    # Rule 1: enableOrderBook == true
    if not row.enableOrderBook:
        return False
    # Rule 2: active == true and closed == false
    if not row.active or row.closed:
        return False
    # Rule 3: 0 < time_to_end <= 48 hours (endDate must be in future and close within 48h)
    if row.hours_to_close is None or not (0 < row.hours_to_close <= 48):
        return False
    # Rule 4: Has valid YES/NO token id (clob_token_ids can be parsed to length 2 list)
    clob_token_ids = row.clob_token_ids
    if not clob_token_ids or not isinstance(clob_token_ids, list) or len(clob_token_ids) != 2:
        return False
    # Additional check: both YES and NO token IDs should exist
    if not row.yes_token_id or not row.no_token_id:
        return False
    return True


df["is_candidate"] = df.apply(is_candidate, axis=1)
df_candidates = df[df["is_candidate"]]

# Initialize session state for filter status
if 'display_mode' not in st.session_state:
    st.session_state.display_mode = 'candidates'  # 'all', 'candidates', or 'filtered'
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = df_candidates
if 'is_filtered' not in st.session_state:
    st.session_state.is_filtered = False
if 'filtered_candidates' not in st.session_state:
    st.session_state.filtered_candidates = df_candidates

st.subheader("Candidate Markets (48h / YES/NO / OrderBook)")



# Determine which dataframe to display based on mode
if st.session_state.display_mode == 'all':
    # Show all original data (before any filtering)
    display_df = df_all
elif st.session_state.display_mode == 'filtered':
    # Show data with missing prices removed
    display_df = st.session_state.filtered_data
else:  # candidates
    # Show candidate data (with 48h/active, etc. filters)
    display_df = df_candidates

st.dataframe(display_df[
    ["category", "question", "endDate", "hours_to_close", "yes_price", "no_price", "slug"]
])

# Three option buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Show All Data"):
        st.session_state.display_mode = 'all'
        st.rerun()

with col2:
    if st.button("一键过滤按钮 (Remove Invalid Prices)"):
        # Check if currently in filtered state to determine action
        if st.session_state.display_mode == 'filtered':
            # If already filtered, reset to the appropriate non-filtered view
            if st.session_state.is_filtered:
                # Was filtered candidates, go back to normal candidates
                st.session_state.display_mode = 'candidates'
                st.session_state.is_filtered = False
            else:
                # Was filtered all data, go back to all data
                st.session_state.display_mode = 'all'
        else:
            # Apply filtering to current view
            current_display = df_all if st.session_state.display_mode == 'all' else df_candidates
            filtered_df = current_display[
                current_display["yes_price"].notna() & 
                current_display["no_price"].notna() &
                pd.to_numeric(current_display["yes_price"], errors='coerce').notna() &
                pd.to_numeric(current_display["no_price"], errors='coerce').notna()
            ].copy()
            
            # Update session state based on current display mode
            if st.session_state.display_mode == 'all':
                st.session_state.filtered_data = filtered_df
                st.session_state.display_mode = 'filtered'
                st.session_state.is_filtered = False
            elif st.session_state.display_mode == 'candidates':
                st.session_state.filtered_candidates = filtered_df
                st.session_state.display_mode = 'filtered'
                st.session_state.is_filtered = True
        
        st.rerun()

with col3:
    if st.button("Filter Candidates"):
        st.session_state.display_mode = 'candidates'
        st.session_state.is_filtered = False
        st.rerun()

# Show status
if st.session_state.display_mode == 'all':
    st.info(f"Showing all {len(df_all)} markets (no filters applied)")
elif st.session_state.display_mode == 'filtered':
    if st.session_state.is_filtered:
        filtered_count = len(st.session_state.filtered_candidates)
        st.info(f"Showing {filtered_count} candidate markets (with 48h/active filters, invalid prices removed)")
    else:
        filtered_count = len(st.session_state.filtered_data)
        st.info(f"Showing {filtered_count} markets (invalid prices removed from all data)")
else:  # candidates
    st.info(f"Showing {len(df_candidates)} candidate markets (with 48h/active filters)")

# Focus = 2 (crypto + sports)
from src.core.select_focus import pick_focus
from src.core.models import MarketRecord

def select_focus_df(df):
    # Convert dataframe rows to MarketRecord objects
    market_records = []
    for _, row in df.iterrows():
        record = MarketRecord(
            id=row["id"],
            slug=row["slug"],
            question=row["question"],
            category=row["category"],
            endDate=row["endDate"],
            hours_to_close=row["hours_to_close"],
            enableOrderBook=row["enableOrderBook"],
            active=row["active"],
            closed=row["closed"],
            yes_token_id=row["yes_token_id"],
            no_token_id=row["no_token_id"],
            yes_price=row["yes_price"],
            no_price=row["no_price"],
            invalid_reason=row["invalid_reason"],
            clob_token_ids=row["clob_token_ids"]
        )
        market_records.append(record)
    
    selected_records = pick_focus(market_records)
    if selected_records:
        # Convert back to dataframe
        selected_data = []
        for record in selected_records:
            selected_data.append({
                "question": record.question,
                "hours_to_close": record.hours_to_close,
                "yes_price": record.yes_price,
                "no_price": record.no_price,
                "slug": record.slug,
                "category": record.category
            })
        return pd.DataFrame(selected_data)
    else:
        return pd.DataFrame()

# Use the filtered dataframe if filter is applied, otherwise use original

# Focus selection should always be based on markets that fulfill the 48-hour close condition
# Since the pick_focus algorithm expects markets with specific characteristics
if st.session_state.display_mode == 'filtered':
    # Use filtered data for focus selection, but ensure it has 48h condition
    focus_df = st.session_state.filtered_candidates
elif st.session_state.display_mode == 'all':
    # For all data, filter to only include markets with 48h condition for focus selection
    focus_df = df_all[
        (df_all["hours_to_close"] > 0) & 
        (df_all["hours_to_close"] <= 48)
    ]
else:
    # Default: use candidate data for focus selection (already has 48h condition)
    focus_df = df_candidates

df_focus = select_focus_df(focus_df)
st.subheader("Focus = 2 Markets (1 Crypto + 1 Sports)")
if not df_focus.empty:
    # Show category along with other fields for clarity
    st.dataframe(df_focus[
        ["category", "question", "hours_to_close", "yes_price", "no_price", "slug"]
    ])
else:
    st.write("No focus markets available.")

# Add CLOB Order Book Information
st.subheader("CLOB Order Book Information")

# Determine which dataframe to use for order book selection based on current display mode
if st.session_state.display_mode == 'filtered':
    if st.session_state.is_filtered:
        order_book_df = st.session_state.filtered_candidates
    else:
        order_book_df = st.session_state.filtered_data
elif st.session_state.display_mode == 'all':
    order_book_df = df_all
else:  # candidates
    order_book_df = df_candidates

if not order_book_df.empty:
    # Allow user to select a market to view order book details:
    selected_market = st.selectbox(
        "Select a market to view order book details:",
        options=order_book_df.index,
        format_func=lambda x: order_book_df.loc[x, "question"][:50] + "..." if len(order_book_df.loc[x, "question"]) > 50 else order_book_df.loc[x, "question"]
    )
    
    if selected_market is not None:
        market_row = order_book_df.loc[selected_market]
        clob_token_ids = market_row["clob_token_ids"]
        
        if clob_token_ids and len(clob_token_ids) > 0:
            clob_client = ClobAPIClient()
            api_client = ClobAPI()  # API client for the endpoints
            
            # Display order book info for each token ID
            for i, token_id in enumerate(clob_token_ids):
                st.write(f"**Token {i+1}:** {token_id}")
                
                # Get best bid/ask using both direct client and API endpoint
                bid_ask = clob_client.get_best_bid_ask(token_id)
                
                # Note: In ClobAPIClient implementation:
                # - get_price with side="BUY" returns the ask price (what you pay to buy)
                # - get_price with side="SELL" returns the bid price (what you get for selling)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="Best Bid", value=f"{bid_ask['bid']:.4f}" if bid_ask['bid'] else "N/A")
                with col2:
                    st.metric(label="Best Ask", value=f"{bid_ask['ask']:.4f}" if bid_ask['ask'] else "N/A")
                
                # Get midpoint
                midpoint = clob_client.get_midpoint(token_id)
                if midpoint:
                    st.metric(label="Midpoint Price", value=f"{midpoint:.4f}")
                
                # Test the API endpoints
                st.write("**API Endpoints Test:**")
                col3, col4 = st.columns(2)
                with col3:
                    if st.button(f"Test GET /book for Token {i+1}", key=f"api_book_{token_id}"):
                        book_data = api_client.get_order_book(token_id)
                        if "error" in book_data and "Connection refused" in str(book_data["error"]):
                            st.warning("API server not running. Use: python run_api.py to start it.")
                            # Fallback to direct client
                            try:
                                book = clob_client.get_order_book(token_id)
                                st.json({"fallback_direct_client": True, "data": book})
                            except Exception as e:
                                st.error(f"Direct client also failed: {str(e)}")
                        else:
                            st.json(book_data)
                with col4:
                    if st.button(f"Test GET best_bid_ask for Token {i+1}", key=f"api_best_{token_id}"):
                        best_bid_ask = api_client.get_best_bid_ask(token_id)
                        if "error" in best_bid_ask and "Connection refused" in str(best_bid_ask["error"]):
                            st.warning("API server not running. Use: python run_api.py to start it.")
                            # Fallback to direct client
                            try:
                                bid_ask_direct = clob_client.get_best_bid_ask(token_id)
                                st.json({"fallback_direct_client": True, "data": bid_ask_direct})
                            except Exception as e:
                                st.error(f"Direct client also failed: {str(e)}")
                        else:
                            st.json(best_bid_ask)
                
                # Option to view full order book
                if st.button(f"View Full Order Book for Token {i+1}", key=f"book_{token_id}"):
                    try:
                        book = clob_client.get_order_book(token_id)
                        st.json(book)
                    except Exception as e:
                        st.error(f"Error fetching order book: {str(e)}")
                
                st.divider()
        else:
            st.write("No CLOB token IDs available for this market.")
else:
    st.write("No markets available to show order book information.")

# New section: CLOB API Endpoints Demo
st.subheader("CLOB API Endpoints Demo")

# Create API client instance
api_client = ClobAPI()
clob_client = ClobAPIClient()  # Direct client as fallback

# Single token order book
st.write("### Get Order Book Summary for a Token")
with st.form("get_book_form"):
    token_id_input = st.text_input("Enter Token ID:", key="token_id_book")
    use_direct_client = st.checkbox("Use direct CLOB client (if API server not running)", value=True)
    submitted = st.form_submit_button("Get Order Book")
    if submitted and token_id_input:
        if use_direct_client:
            # Use direct CLOB client
            try:
                book = clob_client.get_order_book(token_id_input)
                st.json(book)
            except Exception as e:
                st.error(f"Error with direct client: {str(e)}")
                st.write("Make sure you have internet connection and the token ID is valid.")
        else:
            # Use API endpoint
            result = api_client.get_order_book(token_id_input)
            st.json(result)

# Batch prices request
st.write("### Batch Get Best Bid/Ask Prices")
with st.form("batch_prices_form"):
    st.write("Enter multiple token requests (one per line, format: token_id,side)")
    batch_input = st.text_area("Token requests (format: token_id,side per line):\nexample_token_id,BUY\nexample_token_id,SELL")
    use_direct_batch = st.checkbox("Use direct CLOB client for batch", value=True, key="direct_batch")
    batch_submitted = st.form_submit_button("Get Batch Prices")
    if batch_submitted and batch_input:
        # Parse the input
        requests_list = []
        for line in batch_input.strip().split('\n'):
            if ',' in line:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    token_id, side = parts
                    requests_list.append({
                        "token_id": token_id.strip(),
                        "side": side.strip().upper()
                    })
        
        if requests_list:
            if use_direct_batch:
                # Use direct client for batch requests
                results = []
                for req in requests_list:
                    token_id = req["token_id"]
                    side = req["side"]
                    try:
                        # For the ClobAPIClient, side="BUY" gets the ask price (what you'd pay to buy)
                        # and side="SELL" gets the bid price (what you'd get for selling)
                        price = clob_client.get_price(token_id, side=side)
                        results.append({
                            "token_id": token_id,
                            "side": side,
                            "price": price
                        })
                    except Exception as e:
                        results.append({
                            "token_id": token_id,
                            "side": side,
                            "error": str(e)
                        })
                st.json({"results": results})
            else:
                result = api_client.get_best_bid_ask_batch(requests_list)
                st.json(result)

st.info("Note: Check 'Use direct CLOB client' to bypass the API server and use the CLOB client directly. Otherwise, make sure to run the API server with 'python run_api.py' for API endpoint functionality.")

