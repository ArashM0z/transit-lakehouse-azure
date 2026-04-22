{{
  config(
    materialized='incremental',
    unique_key='tap_id',
    incremental_strategy='delete+insert',
    schema='silver',
    cluster_by=['date_key', 'station_id']
  )
}}

-- Silver: deduplicated, type-conformed, dimension-aware tap events.
--   - dedupes on tap_id keeping the latest ingest_timestamp
--   - back-fills line_id from the stations dimension (line in bronze is
--     descriptive, line_id is the conformed key)
--   - adds date_key for downstream joins to dim_date

WITH source AS (
    SELECT *
    FROM {{ ref('bronze__afc_taps') }}
    {% if is_incremental() %}
      WHERE ingest_timestamp_utc > (SELECT COALESCE(MAX(ingest_timestamp_utc), '1970-01-01'::timestamp) FROM {{ this }})
    {% endif %}
),

dedup AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY tap_id
            ORDER BY ingest_timestamp_utc DESC
        ) AS rn
    FROM source
),

with_dims AS (
    SELECT
        d.tap_id,
        d.card_token,
        d.station_id,
        s.line_id,
        d.zone,
        d.fare_class,
        d.fare_amount_cad,
        d.tap_type,
        d.tap_timestamp_utc,
        d.device_id,
        d.schema_version,
        CAST(TO_CHAR(d.tap_timestamp_utc, 'YYYYMMDD') AS INT) AS date_key,
        DATE_TRUNC('hour', d.tap_timestamp_utc) AS tap_hour_utc,
        d.ingest_timestamp_utc
    FROM dedup AS d
    INNER JOIN {{ source('bronze', 'stations') }} AS s
        ON d.station_id = s.station_id
    WHERE d.rn = 1
)

SELECT *
FROM with_dims
