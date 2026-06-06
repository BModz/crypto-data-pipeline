import streamlit as st
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT = "crypto-pipeline-dev"
TABLE = f"`{PROJECT}.crypto_transformed.mart_coin_daily`"

st.set_page_config(
    page_title="Crypto Market Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Crypto Market Dashboard")
st.caption("Data refreshed daily from CoinGecko via automated pipeline.")


@st.cache_resource
def get_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT)


@st.cache_data(ttl=3600)
def load_latest():
    client = get_client()
    query = f"""
        SELECT *
        FROM {TABLE}
        WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM {TABLE})
        ORDER BY market_cap_rank
    """
    return client.query(query).to_dataframe()


@st.cache_data(ttl=3600)
def load_history():
    client = get_client()
    query = f"""
        SELECT snapshot_date, name, current_price_usd, market_cap_rank
        FROM {TABLE}
        ORDER BY snapshot_date, market_cap_rank
    """
    return client.query(query).to_dataframe()


latest = load_latest()
history = load_history()
snapshot_date = latest["snapshot_date"].iloc[0]

st.markdown(f"**Latest snapshot:** {snapshot_date}")

tab1, tab2, tab3 = st.tabs(["🏆 Top Coins", "📉 Price Trends", "🚀 Biggest Movers"])

# ── Tab 1: Leaderboard ───────────────────────────────────────────────────────
with tab1:
    st.subheader("Top 100 coins by market cap")

    import pandas as pd

    display = latest[[
        "market_cap_rank", "name", "symbol",
        "current_price_usd", "price_change_pct_24h",
        "market_cap_usd", "total_volume_usd",
    ]].copy()

    def fmt_price(x):
        if pd.isna(x):
            return "—"
        x = float(x)
        if x >= 1:
            return f"${x:,.2f}"
        elif x >= 0.0001:
            return f"${x:,.4f}"
        else:
            return f"${x:,.8f}"

    display["current_price_usd"] = display["current_price_usd"].apply(fmt_price)
    display["price_change_pct_24h"] = display["price_change_pct_24h"].apply(
        lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
    )
    display["market_cap_usd"] = display["market_cap_usd"].apply(
        lambda x: f"${x:,.0f}" if pd.notna(x) else "—"
    )
    display["total_volume_usd"] = display["total_volume_usd"].apply(
        lambda x: f"${x:,.0f}" if pd.notna(x) else "—"
    )

    display.columns = ["Rank", "Name", "Symbol", "Price (USD)", "24h Change %", "Market Cap (USD)", "Volume (USD)"]

    st.dataframe(display, width="stretch", hide_index=True)

# ── Tab 2: Price Trends ──────────────────────────────────────────────────────
with tab2:
    st.subheader("Price history by coin")

    top10 = latest.nsmallest(10, "market_cap_rank")["name"].tolist()
    selected = st.multiselect(
        "Select coins to compare",
        options=sorted(history["name"].unique()),
        default=top10[:5],
    )

    if selected:
        filtered = history[history["name"].isin(selected)]
        fig = px.line(
            filtered,
            x="snapshot_date",
            y="current_price_usd",
            color="name",
            labels={"current_price_usd": "Price (USD)", "snapshot_date": "Date", "name": "Coin"},
        )
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Select at least one coin above.")

# ── Tab 3: Biggest Movers ────────────────────────────────────────────────────
with tab3:
    st.subheader(f"Biggest movers — {snapshot_date}")

    movers = latest.dropna(subset=["price_change_pct_24h"]).copy()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 10 Gainers**")
        gainers = movers.nlargest(10, "price_change_pct_24h")[["name", "price_change_pct_24h"]]
        fig = px.bar(
            gainers,
            x="price_change_pct_24h",
            y="name",
            orientation="h",
            color_discrete_sequence=["#00c48c"],
            labels={"price_change_pct_24h": "24h Change %", "name": ""},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("**Top 10 Losers**")
        losers = movers.nsmallest(10, "price_change_pct_24h")[["name", "price_change_pct_24h"]]
        fig = px.bar(
            losers,
            x="price_change_pct_24h",
            y="name",
            orientation="h",
            color_discrete_sequence=["#ff4b4b"],
            labels={"price_change_pct_24h": "24h Change %", "name": ""},
        )
        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, width="stretch")
