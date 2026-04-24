{{ config(materialized='table', schema='gold') }}

SELECT
    date_key,
    calendar_date::date AS calendar_date,
    year,
    quarter,
    month,
    month_name,
    day_of_month,
    day_of_week_iso,
    day_name,
    is_weekend,
    CASE WHEN is_weekend THEN 'WEEKEND' ELSE 'WEEKDAY' END AS day_type
FROM {{ source('bronze', 'date') }}
