{{ config(
    materialized="incremental",
    unique_key=["station_id", "service_date"],
    on_schema_change="append_new_columns",
    cluster_by=["service_date"],
    tags=["gold", "marts", "station"]
) }}

with hourly as (
    select * from {{ ref("fact_ridership_hourly") }}
),
fare as (
    select
        station_id,
        service_date,
        sum(fare_amount_cents) as fare_revenue_cents,
        count_if(fare_class = 'concession') as concession_taps,
        count_if(fare_class = 'youth') as youth_taps,
        count_if(fare_class = 'senior') as senior_taps,
        count_if(fare_class = 'employee') as employee_taps
    from {{ ref("fact_fare_revenue") }}
    {% if is_incremental() %} where service_date >= dateadd(day, -7, current_date()) {% endif %}
    group by station_id, service_date
),
ridership as (
    select
        station_id,
        date(hour_ts) as service_date,
        sum(tap_count) as daily_taps,
        max(tap_count) as peak_hour_taps,
        avg(tap_count) as avg_hour_taps,
        count(distinct hour_ts) as active_hours
    from hourly
    {% if is_incremental() %} where date(hour_ts) >= dateadd(day, -7, current_date()) {% endif %}
    group by station_id, date(hour_ts)
)
select
    r.station_id, r.service_date, r.daily_taps, r.peak_hour_taps, r.avg_hour_taps, r.active_hours,
    coalesce(f.fare_revenue_cents, 0) as fare_revenue_cents,
    coalesce(f.fare_revenue_cents, 0) / 100.0 as fare_revenue_dollars,
    coalesce(f.concession_taps, 0) as concession_taps,
    coalesce(f.youth_taps, 0) as youth_taps,
    coalesce(f.senior_taps, 0) as senior_taps,
    coalesce(f.employee_taps, 0) as employee_taps,
    safe_divide(coalesce(f.concession_taps, 0), nullif(r.daily_taps, 0)) as concession_share,
    case
        when r.daily_taps >= 50000 then 'very_high'
        when r.daily_taps >= 20000 then 'high'
        when r.daily_taps >= 5000  then 'medium'
        when r.daily_taps >= 500   then 'low'
        else 'very_low'
    end as daily_volume_band,
    current_timestamp() as _materialized_at
from ridership r
left join fare f using (station_id, service_date)
