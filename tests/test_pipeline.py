"""
Tests for pipeline.py.

We mock the CoinGecko API so these tests run fast and offline —
no network calls, no BigQuery credentials needed.
"""
from unittest.mock import Mock, patch
from pipeline import coin_markets, COINS_PER_PAGE

# A minimal fake coin that looks like a real CoinGecko response
FAKE_COIN = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 60000.0,
    "market_cap": 1_200_000_000_000,
    "market_cap_rank": 1,
    "total_volume": 30_000_000_000,
    "price_change_percentage_24h": 2.5,
    "high_24h": 61000.0,
    "low_24h": 59000.0,
    "circulating_supply": 19_000_000.0,
    "total_supply": 21_000_000.0,
    "max_supply": 21_000_000.0,
    "ath": 69000.0,
    "ath_change_percentage": -13.0,
    "atl": 67.81,
    "atl_change_percentage": 88000.0,
    "roi": None,
}


def make_mock_response(coins):
    """Return a mock requests.Response that returns the given coins as JSON."""
    mock_response = Mock()
    mock_response.json.return_value = coins
    mock_response.raise_for_status.return_value = None
    return mock_response


@patch("pipeline.requests.get")
def test_yields_correct_number_of_coins(mock_get):
    """Pipeline should yield exactly COINS_PER_PAGE coins."""
    fake_coins = [dict(FAKE_COIN, id=f"coin_{i}", market_cap_rank=i + 1)
                  for i in range(COINS_PER_PAGE)]
    mock_get.return_value = make_mock_response(fake_coins)

    results = list(coin_markets())
    assert len(results) == COINS_PER_PAGE


@patch("pipeline.requests.get")
def test_loaded_at_added_to_every_coin(mock_get):
    """Every coin must have a loaded_at field — it's how we track snapshots."""
    fake_coins = [dict(FAKE_COIN, id=f"coin_{i}") for i in range(5)]
    mock_get.return_value = make_mock_response(fake_coins)

    for coin in coin_markets():
        assert "loaded_at" in coin, f"loaded_at missing from coin: {coin['id']}"


@patch("pipeline.requests.get")
def test_loaded_at_is_iso_string(mock_get):
    """loaded_at must be an ISO 8601 string so dlt writes it as a timestamp."""
    mock_get.return_value = make_mock_response([FAKE_COIN])

    coin = next(iter(coin_markets()))
    assert isinstance(coin["loaded_at"], str)
    assert "T" in coin["loaded_at"]  # ISO 8601 format: 2026-06-06T14:00:00+00:00


@patch("pipeline.requests.get")
def test_all_coins_share_same_loaded_at(mock_get):
    """All coins in a single run must have the same loaded_at — one snapshot."""
    fake_coins = [dict(FAKE_COIN, id=f"coin_{i}") for i in range(10)]
    mock_get.return_value = make_mock_response(fake_coins)

    timestamps = [coin["loaded_at"] for coin in coin_markets()]
    assert len(set(timestamps)) == 1, "All coins in one run must share a loaded_at"


@patch("pipeline.requests.get")
def test_required_fields_present(mock_get):
    """Key fields used by dbt models must be present in every coin."""
    required = {"id", "symbol", "name", "current_price", "market_cap",
                "market_cap_rank", "total_volume", "price_change_percentage_24h"}
    mock_get.return_value = make_mock_response([FAKE_COIN])

    coin = next(iter(coin_markets()))
    missing = required - coin.keys()
    assert not missing, f"Missing fields: {missing}"
