import streamlit as st
import pandas as pd

from src.clients import fetch_markets

from src.core import (
    MarketRecord,
    parse_yes_no,
    hours_to_close,
    is_candidate,
    pick_focus,
)
st.set_page_config(layout="wide")
st.title("Polymarket – Dual Market Dashboard")

@st.cache_data
def load_data():
    raw = fetch_markets()
    records = []

  # filter candidate
    for m in raw:
        yes_p, no_p, yes_t, no_t, invalid = parse_yes_no(m)

        rec = MarketRecord(
            id=m.get("id"),
            slug=m.get("slug"),
            question=m.get("question"),
            category=m.get("category"),
            endDate=m.get("endDate"),
            hours_to_close=hours_to_close(m.get("endDate")),
            enableOrderBook=bool(m.get("enableOrderBook")),
            active=bool(m.get("active")),
            closed=bool(m.get("closed")),
            yes_token_id=yes_t,
            no_token_id=no_t,
            yes_price=yes_p,
            no_price=no_p,
            invalid_reason=invalid,
        )
        records.append(rec)

    return records

records = load_data()
df = pd.DataFrame([r.dict() for r in records])

candidates = [r for r in records if is_candidate(r)]
df_candidates = pd.DataFrame([r.dict() for r in candidates])

st.subheader("Candidate Markets (≤ 48h)")
filter_price = st.toggle("Filter invalid YES/NO price")

if filter_price:
    df_candidates = df_candidates[
        df_candidates["yes_price"].notna() &
        df_candidates["no_price"].notna()
    ]

st.dataframe(
    df_candidates[
        ["category", "question", "endDate", "hours_to_close",
         "yes_price", "no_price", "slug"]
    ],
    use_container_width=True
)

# Focus = 2 
st.subheader("🎯 Focus Markets")
focus = pick_focus(candidates)

for m in focus:
    st.markdown(f"""
**{m.category}**  
**{m.question}**  
⏳ {m.hours_to_close} hours  
YES: `{m.yes_price}` | NO: `{m.no_price}`  
ID: `{m.slug or m.id}`
""")
