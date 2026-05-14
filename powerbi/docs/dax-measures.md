# DAX measure dictionary

Every measure used in the Power BI semantic model. Update in lockstep with `powerbi/model/`.

## Core ridership

### `Daily Taps`

```dax
Daily Taps := SUM ( 'fact_ridership_hourly'[tap_count] )
```

### `Daily Taps YoY %`

```dax
Daily Taps YoY % :=
VAR _current = [Daily Taps]
VAR _py = CALCULATE ( [Daily Taps], DATEADD ( 'dim_date'[date], -1, YEAR ) )
RETURN DIVIDE ( _current - _py, _py )
```

### `Peak Hour Share`

```dax
Peak Hour Share :=
DIVIDE (
    CALCULATE ( [Daily Taps], 'fact_ridership_hourly'[hour_of_day] IN { 8, 17 } ),
    [Daily Taps]
)
```

## Revenue

### `Fare Revenue (CAD)`

```dax
Fare Revenue (CAD) := DIVIDE ( SUM ( 'fact_fare_revenue'[fare_amount_cents] ), 100 )
```

### `Revenue per Tap`

```dax
Revenue per Tap := DIVIDE ( [Fare Revenue (CAD)], [Daily Taps] )
```

## Event uplift

### `Event Day Uplift %`

```dax
Event Day Uplift % :=
VAR _event = CALCULATE ( [Daily Taps], 'dim_date'[is_event_day] = TRUE )
VAR _baseline =
    CALCULATE (
        AVERAGEX (
            FILTER ( 'dim_date', 'dim_date'[is_event_day] = FALSE ),
            [Daily Taps]
        )
    )
RETURN DIVIDE ( _event - _baseline, _baseline )
```

## Operational

### `Active Hours`

```dax
Active Hours := DISTINCTCOUNT ( 'fact_ridership_hourly'[hour_ts] )
```

### `Forecast vs Actual Variance`

```dax
Forecast vs Actual Variance :=
DIVIDE ( [Daily Taps] - [Forecast Taps], [Forecast Taps] )
```

`Forecast Taps` is sourced from the Azure ML batch-scoring output published to `mart_forecast`.

## Calculation groups

The semantic model also defines a `Time Intelligence` calculation group with MTD / YTD / vs PY / vs PP variants. See `powerbi/model/calculation_groups/`.
