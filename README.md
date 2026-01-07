# polymarket-gamma
用 Python 拉取 Polymarket 市场数据，并做一个最小可用的网页（可交互），用于展示市场列表、YES/NO 价格、以及一键过滤

## Installation and Running

### Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the Web Dashboard

```bash
streamlit run app.py
```

### Run the API Server (Optional)

To use the CLOB API endpoints separately:

```bash
python run_api.py
```

This starts a Flask API server on port 5001 with CLOB endpoints available.

## Core Implementation Details

### Market Data Parsing Robustness
- **JSON String Handling**: All market fields (outcomes, outcomePrices, clobTokenIds) are parsed robustly to handle both JSON strings and arrays
- **Binary YES/NO Validation**: Markets are validated to ensure they are binary (exactly 2 outcomes) and contain "Yes"/"No" outcomes
- **Price Mapping**: yes_price and no_price are correctly mapped based on outcome positions, not fixed left/right assumptions
- **Invalid Reason Tracking**: Markets that fail validation are marked with specific invalid_reason for debugging/filtering

### Filtering Implementation
- **Candidate Filter Rules**:
  1. `enableOrderBook == true` (markets with order book functionality)
  2. `active == true` and `closed == false` (currently active, not closed markets)
  3. `0 < time_to_end <= 48 hours` (markets closing within next 48 hours)
  4. Valid YES/NO token IDs (clobTokenIds can be parsed to length 2 list)

- **Price Filtering UI**:
  - **"一键过滤按钮 (Remove Invalid Prices)": Toggles to filter out rows where yes_price or no_price are null, non-numeric, or parse failures
  - **Toggle Behavior**: First click applies filter, second click restores original view
  - **"Show All Data" Reset**: Available to reset all filters and show complete data

### API Endpoints Implementation

#### CLOB API Endpoints:
- **GET /book?token_id=...**: Reads order book summary (bids/asks) for a specific token
  - Parameter: `token_id` as query parameter
  - Response: Order book data with bid/ask orders
  - Frontend: Called via `api_client.get_order_book(token_id)`

- **POST /prices**: Batch get best bid/ask for multiple tokens (BUY/SELL)
  - Request body: `{"requests": [{"token_id": "token1", "side": "BUY"}, {"token_id": "token2", "side": "SELL"}]}"
  - Response: `{"results": [{"token_id": "token1", "side": "BUY", "price": 0.5}]}"
  - Frontend: Called via `api_client.get_best_bid_ask_batch(requests_data)`
  - Handles both BUY (ask price) and SELL (bid price) sides

- **Additional Endpoints**:
  - **GET /price?token_id=...&side=BUY/SELL**: Single token price lookup
  - **GET /midpoint?token_id=...**: Midpoint price calculation
  - **GET /best_bid_ask?token_id=...**: Both bid and ask for a token
  - **POST /books**: Batch order book requests for multiple tokens

#### Frontend API Integration:
- **API Client Class**: `ClobAPI` in app.py handles HTTP requests to endpoints
- **Fallback System**: When API server is not running, falls back to direct CLOB client
- **Error Handling**: Comprehensive error handling for connection failures

### Focus Market Selection (Focus = 2 Markets)
- **Selection Strategy**: 1 Crypto market + 1 Sports market from candidates
- **Crypto Keywords**: "crypto", "bitcoin", "ethereum", "btc", "eth", "cryptocurrency" (case-insensitive)
- **Sports Keywords**: "sport", "football", "basketball", "soccer", "tennis", "baseball", "hockey", "nfl" (case-insensitive)
- **Search Logic**: Checks both category and question fields for keyword matches
- **Priority**: Selects first match of each type from candidate list

### UI Components
- **Three Main Views**:
  1. **All Markets**: Complete dataset without filters
  2. **Candidate Markets**: Filtered to 48h/active/orderbook markets
  3. **Filtered Markets**: Candidate markets with invalid prices removed
- **Interactive Controls**: Buttons to switch between views with session state management
- **Order Book Details**: Interactive selector for viewing token-specific order book information
- **CLOB API Demo**: Direct API endpoint testing interface

## APIs Used

- **Gamma API**: Used to fetch market data from `https://gamma-api.polymarket.com/markets`
- **CLOB API**: Used to fetch order book data from `https://clob.polymarket.com`

## Category Classification Strategy for "Crypto / Sports" and "Focus 2 Markets" Selection

### Strategy for Focus=2 Selection (1 Crypto + 1 Sports):

- **Crypto markets**: Markets with "crypto", "bitcoin", "ethereum", "btc", "eth", or "cryptocurrency" (case-insensitive) in the category or question
- **Sports markets**: Markets with "sport", "football", "basketball", "soccer", "tennis", "baseball", "hockey", or "nfl" (case-insensitive) in the category or question

The system selects exactly 1 crypto market and 1 sports market from the filtered candidate list, prioritizing markets that match these criteria.

## Filtering Rules Explanation

### 48h Close Rule:
- Markets are filtered to only include those that will close within 48 hours (0 < hours_to_close <= 48)
- This is calculated by comparing the market's endDate with the current time

### Missing Price Definition:
- Markets with missing prices are identified as those where either YES or NO token prices are null/None
- This can occur due to invalid price conversion or missing outcome prices
- These markets are filtered out during the "Remove rows with missing YES/NO prices" filtering step

### Additional Filters:
- **Order Book Enabled**: Markets must have `fpmmLive` set to true to have order book functionality
- **Active Status**: Markets must be active (`active` = true)
- **Not Closed**: Markets must not be closed (`closed` = false)

