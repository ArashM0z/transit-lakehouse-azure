{{ config(materialized='view', schema='bronze') }}

-- Bronze passthrough: surfaces the source under a model name so downstream
-- silver models depend on a dbt node rather than a raw source.

SELECT
    tap_id,
    card_token,
    station_id,
    line,
    zone,
    fare_class,
    fare_amount_cad,
    tap_type,
    tap_timestamp_utc,
    device_id,
    schema_version,
    ingest_timestamp_utc
FROM {{ source('bronze', 'afc_taps') }}
