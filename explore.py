"""
Explore the CoinGecko API.
Goal: understand the data structure before building the pipeline.
"""
import requests
import json

# CoinGecko's free public endpoint - top coins by market cap
URL = "https://api.coingecko.com/api/v3/coins/markets"

# What we're asking for: top 10 coins, priced in USD, sorted by market cap
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1,
}

# Make the API call
print("Calling CoinGecko API...")
response = requests.get(URL, params=params)
response.raise_for_status()  # crashes loudly if the request failed

data = response.json()
print(f"Got {len(data)} coins back\n")

# Print one full coin so you can see the data structure
print("=" * 60)
print("FULL DATA for the first coin (so you see all available fields):")
print("=" * 60)
print(json.dumps(data[0], indent=2))

# Print a clean summary of all 10
print("\n" + "=" * 60)
print("SUMMARY: top 10 coins by market cap")
print("=" * 60)
for coin in data:
    name = coin["name"]
    price = coin["current_price"]
    change_24h = coin["price_change_percentage_24h"]
    print(f"  {name:20} ${price:>12,.2f}   ({change_24h:+.2f}% 24h)")