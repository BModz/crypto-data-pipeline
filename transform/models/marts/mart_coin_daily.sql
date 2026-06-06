with staging as (
    select * from {{ ref('stg_coin_markets') }}
)

select
    snapshot_date,
    market_cap_rank,
    id,
    symbol,
    name,
    current_price_usd,
    market_cap_usd,
    total_volume_usd,
    price_change_pct_24h,
    high_24h_usd,
    low_24h_usd,
    circulating_supply,
    ath_usd,
    ath_change_pct,
    loaded_at
from staging
order by snapshot_date desc, market_cap_rank asc
