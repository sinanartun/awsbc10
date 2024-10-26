WITH PriceAggregates AS (
  SELECT
    min(ID) as min_id,
    max(ID) as max_id,
    DATE_TRUNC('minute', to_timestamp(trade_time, 'YYYY-MM-DD HH24:MI:SS', TRUE)) as trade_time,
    AVG(price) as avg_price,
    max(price) as max_price,
    min(price) as min_price
  FROM 
    btcusdt
  GROUP BY
    DATE_TRUNC('minute', to_timestamp(trade_time, 'YYYY-MM-DD HH24:MI:SS', TRUE))
),
OpenPrices AS (
  SELECT 
    price as open_price,
    min_id
  FROM 
    btcusdt
    JOIN PriceAggregates ON btcusdt.ID = PriceAggregates.min_id
),
ClosePrices AS (
  SELECT 
    price as close_price,
    max_id
  FROM 
    btcusdt
    JOIN PriceAggregates ON btcusdt.ID = PriceAggregates.max_id
)
SELECT
  A.avg_price,
  A.max_price,
  A.min_price,
  A.min_id,
  A.max_id,
  A.trade_time,
  B.open_price,
  C.close_price
FROM
  PriceAggregates A
  JOIN OpenPrices B ON A.min_id = B.min_id
  JOIN ClosePrices C ON A.max_id = C.max_id
ORDER BY
  A.trade_time;