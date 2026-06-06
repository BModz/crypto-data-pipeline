with source as (
    select * from {{ source('crypto_raw', 'coin_markets') }}
),

-- Keep only the most recent load per coin per day.
-- We may run the pipeline multiple times in one day (e.g. manual runs),
-- so we deduplicate to one clean snapshot per coin per calendar date.
deduped as (
    select
        *,
        row_number() over (
            partition by id, date(loaded_at)
            order by loaded_at desc
        ) as row_num
    from source
)

select
    id,
    symbol,
    name,
    cast(current_price        as float64) as current_price_usd,
    cast(market_cap           as float64) as market_cap_usd,
    cast(market_cap_rank      as int64)   as market_cap_rank,
    cast(total_volume         as float64) as total_volume_usd,
    cast(price_change_percentage_24h as float64) as price_change_pct_24h,
    cast(high_24h             as float64) as high_24h_usd,
    cast(low_24h              as float64) as low_24h_usd,
    cast(circulating_supply   as float64) as circulating_supply,
    cast(ath                  as float64) as ath_usd,
    cast(ath_change_percentage as float64) as ath_change_pct,
    timestamp(loaded_at)                  as loaded_at,
    date(loaded_at)                       as snapshot_date
from deduped
where row_num = 1
