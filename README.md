# Crypto Market Data Pipeline

An end-to-end data engineering portfolio project. A fully automated pipeline ingests daily crypto market data from the CoinGecko API, loads it into BigQuery, transforms it with dbt, and serves it via a live Streamlit dashboard — all running on free-tier cloud infrastructure.

**[View live dashboard →](https://crypto-data-pipeline-4kerebjgrstjaydbpzt6s7.streamlit.app/)**

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  CoinGecko API  │────▶│  dlt (Python)   │────▶│  BigQuery            │
│  /coins/markets │     │  pipeline.py     │     │  crypto_raw          │
│  top 100 coins  │     │  daily snapshot  │     │  coin_markets        │
└─────────────────┘     └─────────────────┘     └──────────┬───────────┘
                                                             │
                                                             ▼
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  Streamlit      │◀────│  BigQuery        │◀────│  dbt Core            │
│  Community Cloud│     │  crypto_         │     │  staging + marts     │
│  live dashboard │     │  transformed     │     │  transform/          │
└─────────────────┘     └─────────────────┘     └──────────────────────┘

                    Orchestration: GitHub Actions (daily @ 6am UTC)
                    CI: GitHub Actions (runs on every pull request)
```

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | [dlt](https://dlthub.com/) |
| Warehouse | [Google BigQuery](https://cloud.google.com/bigquery) (free tier) |
| Transformation | [dbt Core](https://www.getdbt.com/) |
| Orchestration | [GitHub Actions](https://github.com/features/actions) |
| Dashboard | [Streamlit Community Cloud](https://streamlit.io/cloud) (free tier) |
| Language | Python 3.13 |
| Package manager | [uv](https://github.com/astral-sh/uv) |

## Dashboard

Three views updated daily:

- **Top Coins** — leaderboard of the top 100 coins by market cap with price, 24h change, and volume
- **Price Trends** — interactive line chart comparing price history across any selected coins
- **Biggest Movers** — top 10 gainers and losers by 24h percentage change

## Data Flow

1. **Ingest** — `pipeline.py` calls CoinGecko's `/coins/markets` endpoint and loads 100 coins into BigQuery using dlt. Each run appends a new timestamped snapshot, building historical data over time.

2. **Transform** — dbt reads from `crypto_raw.coin_markets`, deduplicates to one row per coin per day, casts all numeric types correctly, and writes clean tables to `crypto_transformed`.

3. **Serve** — Streamlit reads from `crypto_transformed.mart_coin_daily` and renders the dashboard.

4. **Orchestrate** — A GitHub Actions workflow runs steps 1–3 every day at 6am UTC. A separate CI workflow runs all tests on every pull request.

## Project Structure

```
crypto-data-pipeline/
├── pipeline.py              # dlt ingestion pipeline
├── app.py                   # Streamlit dashboard
├── explore.py               # one-off API exploration script
├── transform/               # dbt project
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/         # cleans and deduplicates raw data
│       └── marts/           # final tables for the dashboard
├── tests/                   # pytest tests for the pipeline
├── scripts/
│   └── write_secrets.py     # CI helper: writes dlt secrets from env var
└── .github/workflows/
    ├── daily_pipeline.yml   # scheduled daily run
    └── ci.yml               # tests on every pull request
```

## Local Setup

**Prerequisites:** Python 3.13+, [uv](https://github.com/astral-sh/uv), a Google Cloud project with BigQuery enabled.

```bash
git clone https://github.com/BModz/crypto-data-pipeline.git
cd crypto-data-pipeline
uv sync
```

Create `.dlt/secrets.toml` with your BigQuery service account credentials:

```toml
[destination.bigquery.credentials]
project_id = "your-gcp-project"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "your-sa@your-project.iam.gserviceaccount.com"
```

Run the pipeline:

```bash
uv run python pipeline.py
```

Run dbt transformations:

```bash
cd transform && uv run dbt run
```

Run the dashboard locally:

```bash
uv run streamlit run app.py
```

Run tests:

```bash
uv run pytest tests/ -v
cd transform && uv run dbt test
```

## CI/CD

- **Daily pipeline** — runs at 6am UTC via GitHub Actions, requires `GCP_SERVICE_ACCOUNT_KEY` secret
- **CI on PRs** — runs pytest + dbt test on every pull request to main
