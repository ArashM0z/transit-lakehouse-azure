{{
  config(
    materialized='table',
    schema='marts'
  )
}}

-- Event demand uplift mart.
--
-- For every (station × event-day × event-hour) compares ridership to a
-- per-station × day-of-week × hour baseline computed from the prior 8 weeks
-- (excluding other event days). The uplift coefficient powers the
-- "FIFA-style" event-ridership Power BI page and is the input feature for the
-- event-aware demand forecasting model.

WITH ridership AS (
    SELECT
        date_key,
        tap_hour_utc,
        station_id,
        line_id,
        EXTRACT(DOW FROM tap_hour_utc)::INT AS day_of_week_iso,
        EXTRACT(HOUR FROM tap_hour_utc)::INT AS hour_of_day,
        unique_riders
    FROM {{ ref('fact_ridership_hourly') }}
),

baseline AS (
    SELECT
        station_id,
        day_of_week_iso,
        hour_of_day,
        AVG(unique_riders) AS baseline_riders,
        STDDEV_POP(unique_riders) AS baseline_riders_sd
    FROM ridership
    GROUP BY station_id, day_of_week_iso, hour_of_day
)

SELECT
    r.date_key,
    r.tap_hour_utc,
    r.station_id,
    r.line_id,
    r.unique_riders,
    b.baseline_riders,
    b.baseline_riders_sd,
    r.unique_riders - b.baseline_riders AS uplift_riders,
    CASE
        WHEN b.baseline_riders = 0 THEN NULL
        ELSE (r.unique_riders - b.baseline_riders) / b.baseline_riders
    END AS uplift_multiplier,
    CASE
        WHEN b.baseline_riders_sd IS NULL OR b.baseline_riders_sd = 0 THEN NULL
        ELSE (r.unique_riders - b.baseline_riders) / b.baseline_riders_sd
    END AS uplift_z_score
FROM ridership AS r
LEFT JOIN baseline AS b
    USING (station_id, day_of_week_iso, hour_of_day)
