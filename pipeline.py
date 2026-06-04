"""
Ingestion pipeline: CoinGecko → BigQuery via dlt.

Pulls the top 100 coins by market cap and loads them into
BigQuery dataset `crypto_raw`, table `coin_markets`.

Write disposition is REPLACE for now (Week 1): every run
overwrites the table. Week 2 will switch to incremental append.
"""
import dlt
import requests

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
COINS_PER_PAGE = 100


@dlt.resource(write_disposition="replace")
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

    for coin in response.json():
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
