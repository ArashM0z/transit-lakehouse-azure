{{
  config(
    materialized='table',
    schema='gold',
    cluster_by=['date_key', 'line_id']
  )
}}

-- Fare revenue at station × hour × fare_class grain. Used as the basis for
-- revenue forecasting and Power BI revenue dashboards.

WITH taps AS (
    SELECT *
    FROM {{ ref('silver__afc_taps') }}
    WHERE tap_type = 'TAP_ON'  -- revenue is recognised on tap-on
)

SELECT
    date_key,
    tap_hour_utc,
    station_id,
    line_id,
    zone,
    fare_class,
    SUM(fare_amount_cad)                                                     AS gross_fare_revenue_cad,
    COUNT(*)                                                                  AS paid_tap_count,
    COUNT(DISTINCT card_token)                                                AS paying_riders,
    SUM(fare_amount_cad) / NULLIF(COUNT(*), 0)                                AS avg_fare_per_tap_cad,
    SUM(fare_amount_cad) / NULLIF(COUNT(DISTINCT card_token), 0)              AS revenue_per_rider_cad
FROM taps
GROUP BY date_key, tap_hour_utc, station_id, line_id, zone, fare_class
