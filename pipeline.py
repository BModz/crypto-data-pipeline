"""
Ingestion pipeline: CoinGecko → BigQuery via dlt.

Pulls the top 100 coins by market cap and appends them into
BigQuery dataset `crypto_raw`, table `coin_markets`.

Each run adds a new daily snapshot — rows are never deleted.
Use `loaded_at` to filter to a specific day's data.
"""
import dlt
import requests
from datetime import datetime, timezone

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINS_PER_PAGE = 100


@dlt.resource(
    write_disposition="append",
    columns={
        "loaded_at":                    {"data_type": "timestamp"},
        "current_price":                {"data_type": "double"},
        "market_cap":                   {"data_type": "double"},
        "market_cap_rank":              {"data_type": "bigint"},
        "total_volume":                 {"data_type": "double"},
        "high_24h":                     {"data_type": "double"},
        "low_24h":                      {"data_type": "double"},
        "price_change_24h":             {"data_type": "double"},
        "price_change_percentage_24h":  {"data_type": "double"},
        "circulating_supply":           {"data_type": "double"},
        "total_supply":                 {"data_type": "double"},
        "max_supply":                   {"data_type": "double"},
        "ath":                          {"data_type": "double"},
        "ath_change_percentage":        {"data_type": "double"},
        "atl":                          {"data_type": "double"},
        "atl_change_percentage":        {"data_type": "double"},
    },
)
def coin_markets():
    """Yield one dict per coin from CoinGecko /coins/markets."""
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": COINS_PER_PAGE,
        "page": 1,
    }
    response = requests.get(COINGECKO_URL, params=params, timeout=30)
    response.raise_for_status()

    loaded_at = datetime.now(timezone.utc).isoformat()
    for coin in response.json():
        coin["loaded_at"] = loaded_at
        yield coin


def run():
    pipeline = dlt.pipeline(
        pipeline_name="crypto_pipeline",
        destination="bigquery",
        dataset_name="crypto_raw",
    )

    load_info = pipeline.run(coin_markets())
    print(load_info)


if __name__ == "__main__":
    run()
