import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.oauth2 import service_account
from google.cloud import bigquery

PROJECT = "crypto-pipeline-dev"
TABLE   = f"`{PROJECT}.crypto_transformed.mart_coin_daily`"

st.set_page_config(page_title="Crypto Market Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    [data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
    }
    [data-testid="stMetricLabel"] { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    [data-testid="stMetricValue"] { font-size: 1.3rem; font-weight: 700; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #64748b; font-weight: 500; padding: 0.5rem 1.2rem; border-radius: 4px 4px 0 0; }
    .stTabs [aria-selected="true"] { background: #1e293b; color: #f1f5f9; border-bottom: 2px solid #2563eb; }

    .coin-table { width:100%; border-collapse:collapse; font-size:14px; }
    .coin-table th { padding:10px 14px; text-align:right; font-size:11px; color:#64748b; font-weight:500; text-transform:uppercase; letter-spacing:0.06em; border-bottom:1px solid #1e293b; }
    .coin-table th:nth-child(1) { text-align:center; }
    .coin-table th:nth-child(2) { text-align:left; }
    .coin-table td { padding:13px 14px; border-bottom:1px solid #0f172a; vertical-align:middle; }
    .coin-table tr:hover td { background-color:#1e293b; }

    .tv-header { display:flex; align-items:baseline; gap:12px; margin-bottom:1.2rem; }
    .tv-price  { font-size:2.2rem; font-weight:700; color:#f1f5f9; letter-spacing:-0.5px; }
    .tv-change { font-size:1rem; font-weight:600; }
    .tv-label  { font-size:0.8rem; color:#64748b; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_price(x):
    if pd.isna(x): return "—"
    x = float(x)
    if x >= 1:       return f"${x:,.2f}"
    if x >= 0.0001:  return f"${x:,.4f}"
    return f"${x:,.8f}"

def fmt_large(x):
    if pd.isna(x): return "—"
    x = float(x)
    if x >= 1e12: return f"${x/1e12:.2f}T"
    if x >= 1e9:  return f"${x/1e9:.2f}B"
    if x >= 1e6:  return f"${x/1e6:.2f}M"
    return f"${x:,.0f}"

CHART_BASE = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=12),
)

# ── Data ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    return bigquery.Client(credentials=creds, project=PROJECT)

@st.cache_data(ttl=3600)
def load_latest():
    q = f"SELECT * FROM {TABLE} WHERE snapshot_date=(SELECT MAX(snapshot_date) FROM {TABLE}) ORDER BY market_cap_rank"
    return get_client().query(q).to_dataframe()

@st.cache_data(ttl=3600)
def load_history():
    q = f"""SELECT snapshot_date, name, symbol, current_price_usd,
                   total_volume_usd, market_cap_usd, market_cap_rank,
                   high_24h_usd, low_24h_usd, price_change_pct_24h
            FROM {TABLE} ORDER BY snapshot_date, market_cap_rank"""
    return get_client().query(q).to_dataframe()

latest        = load_latest()
history       = load_history()
snapshot_date = latest["snapshot_date"].iloc[0]
num_days      = history["snapshot_date"].nunique()

# ── Global header ─────────────────────────────────────────────────────────────
st.title("Crypto Market Dashboard")
st.caption(f"Top 100 coins · {snapshot_date} · {num_days} day(s) of history")

total_mcap = float(latest["market_cap_usd"].sum())
btc        = latest[latest["id"] == "bitcoin"].iloc[0]
gainers    = int((latest["price_change_pct_24h"] > 0).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Market Cap",  fmt_large(total_mcap))
c2.metric("Bitcoin",           fmt_price(float(btc["current_price_usd"])))
c3.metric("BTC Dominance",     f"{float(btc['market_cap_usd'])/total_mcap*100:.1f}%")
c4.metric("Gainers / Losers",  f"{gainers} / {100-gainers}")

st.divider()
tab1, tab2, tab3 = st.tabs(["Top Coins", "Price Trends", "Biggest Movers"])

# ── Tab 1: leaderboard ────────────────────────────────────────────────────────
with tab1:
    def build_table(df):
        rows = ""
        for _, r in df.iterrows():
            chg = r["price_change_pct_24h"]
            if pd.isna(chg):
                chg_html = '<span style="color:#64748b">—</span>'
            elif float(chg) >= 0:
                chg_html = f'<span style="color:#10b981;font-weight:600">{float(chg):+.2f}%</span>'
            else:
                chg_html = f'<span style="color:#ef4444;font-weight:600">{float(chg):+.2f}%</span>'
            rows += f"""<tr>
                <td style="color:#64748b;text-align:center;width:44px">{int(r['market_cap_rank'])}</td>
                <td><span style="font-weight:600;font-size:15px">{r['name']}</span>
                    <span style="color:#475569;font-size:12px;margin-left:6px">{r['symbol'].upper()}</span></td>
                <td style="text-align:right;font-weight:600">{fmt_price(r['current_price_usd'])}</td>
                <td style="text-align:right">{chg_html}</td>
                <td style="text-align:right;color:#94a3b8">{fmt_large(r['market_cap_usd'])}</td>
                <td style="text-align:right;color:#94a3b8">{fmt_large(r['total_volume_usd'])}</td>
            </tr>"""
        return f"""<table class="coin-table">
            <thead><tr>
                <th>#</th><th style="text-align:left">Name</th>
                <th>Price</th><th>24h %</th><th>Market Cap</th><th>Volume (24h)</th>
            </tr></thead><tbody>{rows}</tbody></table>"""

    st.markdown(build_table(latest), unsafe_allow_html=True)

# ── Tab 2: Multi-coin comparison chart ───────────────────────────────────────
with tab2:
    coin_options = latest.sort_values("market_cap_rank")["name"].tolist()
    top5         = latest.nsmallest(5, "market_cap_rank")["name"].tolist()
    palette      = ["#2196f3","#ff9800","#e91e63","#00bcd4","#9c27b0","#4caf50","#ff5722","#f06292"]

    left, right = st.columns([3, 1])
    with left:
        compare = st.multiselect("Select coins to compare", options=coin_options, default=top5)
    with right:
        normalize = st.toggle("Normalize to % return", value=(num_days >= 2))

    if not compare:
        st.info("Select at least one coin above.")
    else:
        filt = history[history["name"].isin(compare)].copy()
        filt["current_price_usd"] = pd.to_numeric(filt["current_price_usd"], errors="coerce")

        if num_days < 2:
            st.caption(f"Trend data will appear once the pipeline has run on 2+ days. Currently {num_days} day.")

        fig = go.Figure()
        for i, coin in enumerate(compare):
            d     = filt[filt["name"] == coin].sort_values("snapshot_date").copy()
            color = palette[i % len(palette)]

            if normalize and num_days >= 2:
                base   = d["current_price_usd"].iloc[0]
                y_vals = (d["current_price_usd"] / base - 1) * 100
                hover  = f"<b>{coin}</b>: %{{y:+.2f}}%<extra></extra>"
            else:
                y_vals = d["current_price_usd"]
                hover  = f"<b>{coin}</b>: $%{{y:,.4f}}<extra></extra>"

            fig.add_trace(go.Scatter(
                x=d["snapshot_date"],
                y=y_vals,
                name=coin,
                mode="lines+markers",
                line=dict(width=2.5, color=color),
                marker=dict(size=7, color=color, line=dict(width=1.5, color="#0f172a")),
                hovertemplate=hover,
            ))

        if normalize and num_days >= 2:
            fig.add_hline(y=0, line_dash="dot", line_color="#334155", line_width=1)

        fig.update_layout(
            **CHART_BASE,
            height=500,
            hovermode="x unified",
            yaxis=dict(
                gridcolor="#1e293b", color="#64748b", side="right",
                ticksuffix="%" if (normalize and num_days >= 2) else "",
                zeroline=False,
            ),
            xaxis=dict(showgrid=False, color="#64748b", zeroline=False),
            legend=dict(
                orientation="h", y=1.06, x=0,
                bgcolor="rgba(0,0,0,0)", font=dict(size=12),
            ),
            margin=dict(l=0, r=60, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: movers ────────────────────────────────────────────────────────────
with tab3:
    movers = latest.dropna(subset=["price_change_pct_24h"]).copy()
    movers["price_change_pct_24h"] = movers["price_change_pct_24h"].astype(float)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Gainers")
        g = movers.nlargest(10, "price_change_pct_24h")[["name","price_change_pct_24h"]]
        fig = px.bar(g, x="price_change_pct_24h", y="name", orientation="h",
                     color_discrete_sequence=["#26a69a"],
                     labels={"price_change_pct_24h":"24h %","name":""},
                     text=g["price_change_pct_24h"].apply(lambda x: f"{x:+.2f}%"))
        fig.update_layout(**CHART_BASE, margin=dict(l=0,r=20,t=10,b=0))
        fig.update_yaxes(categoryorder="total ascending", showgrid=False, color="#94a3b8")
        fig.update_xaxes(showgrid=False, color="#64748b")
        fig.update_traces(textposition="outside", textfont_color="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 Losers")
        l = movers.nsmallest(10, "price_change_pct_24h")[["name","price_change_pct_24h"]]
        fig = px.bar(l, x="price_change_pct_24h", y="name", orientation="h",
                     color_discrete_sequence=["#ef5350"],
                     labels={"price_change_pct_24h":"24h %","name":""},
                     text=l["price_change_pct_24h"].apply(lambda x: f"{x:+.2f}%"))
        fig.update_layout(**CHART_BASE, margin=dict(l=0,r=20,t=10,b=0))
        fig.update_yaxes(categoryorder="total descending", showgrid=False, color="#94a3b8")
        fig.update_xaxes(showgrid=False, color="#64748b")
        fig.update_traces(textposition="outside", textfont_color="#f1f5f9")
        st.plotly_chart(fig, use_container_width=True)
