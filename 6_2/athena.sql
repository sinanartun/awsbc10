CREATE EXTERNAL TABLE `binance`(
  `id` bigint, 
  `symbol` string, 
  `price` decimal(7,2), 
  `quantity` decimal(7,5), 
  `time` timestamp, 
  `maker` boolean)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY '\t' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://awsbc10/2024'




  WITH PriceAggregates AS (
  SELECT
    MIN(id) AS min_id,
    MAX(id) AS max_id,
    DATE_TRUNC('minute', time) AS trade_minute,
    AVG(price) AS avg_price,
    MAX(price) AS max_price,
    MIN(price) AS min_price
  FROM 
    binance
  GROUP BY
    DATE_TRUNC('minute', time)
),
OpenPrices AS (
  SELECT 
    price AS open_price,
    min_id
  FROM 
    binance
  INNER JOIN PriceAggregates ON binance.id = PriceAggregates.min_id
),
ClosePrices AS (
  SELECT 
    price AS close_price,
    max_id
  FROM 
    binance
  INNER JOIN PriceAggregates ON binance.id = PriceAggregates.max_id
)
SELECT
  pa.avg_price,
  pa.max_price,
  pa.min_price,
  pa.min_id,
  pa.max_id,
  pa.trade_minute,
  op.open_price,
  cp.close_price
FROM
  PriceAggregates pa
  INNER JOIN OpenPrices op ON pa.min_id = op.min_id
  INNER JOIN ClosePrices cp ON pa.max_id = cp.max_id
ORDER BY
  pa.trade_minute;
