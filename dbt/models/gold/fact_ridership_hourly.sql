{{
  config(
    materialized='table',
    schema='gold',
    cluster_by=['date_key', 'station_id']
  )
}}

-- Hourly ridership at station × hour grain.
-- "ridership" is approximated as TAP_ON counts (every passenger taps on);
-- TAP_OFF is also counted as it's required for proof-of-payment audits and
-- some lines.

WITH taps AS (
    SELECT *
    FROM {{ ref('silver__afc_taps') }}
),

agg AS (
    SELECT
        date_key,
        tap_hour_utc,
        station_id,
        line_id,
        zone,
        SUM(CASE WHEN tap_type = 'TAP_ON' THEN 1 ELSE 0 END) AS tap_on_count,
        SUM(CASE WHEN tap_type = 'TAP_OFF' THEN 1 ELSE 0 END) AS tap_off_count,
        COUNT(*) AS total_taps,
        COUNT(DISTINCT card_token) AS unique_riders,
        SUM(fare_amount_cad) AS total_fare_cad
    FROM taps
    GROUP BY date_key, tap_hour_utc, station_id, line_id, zone
)

SELECT
    date_key,
    tap_hour_utc,
    station_id,
    line_id,
    zone,
    tap_on_count,
    tap_off_count,
    total_taps,
    unique_riders,
    total_fare_cad,
    CASE
        WHEN unique_riders = 0 THEN 0
        ELSE CAST(total_taps AS DOUBLE PRECISION) / unique_riders
    END AS taps_per_rider
FROM agg
