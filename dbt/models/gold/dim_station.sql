{{ config(materialized='table', schema='gold') }}

SELECT
    s.station_id,
    s.name,
    s.line_id,
    l.line_name,
    s.zone,
    s.lat,
    s.lon,
    -- approximate distance from Union Station for downstream reachability
    -- and "centrality" analysis
    SQRT(POWER(s.lat - 43.6453, 2) + POWER(s.lon - (-79.3806), 2)) * 111.0 AS km_from_union
FROM {{ source('bronze', 'stations') }} AS s
LEFT JOIN {{ source('bronze', 'lines') }} AS l
    ON s.line_id = l.line_id
