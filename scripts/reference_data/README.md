# Reference data

Public-network reference catalogues used by the synthetic AFC tap generator and the gold-mart `dim_station` table.

## Networks

### `nyc-mta/`

NYC MTA subway. Station IDs and coordinates pulled from the public GTFS schedule on `data.ny.gov`; ridership priors derived from the *MTA Subway Hourly Ridership: Beginning 2025* open dataset (top 60 stations by 2024 annualised volume, normalised to sum to 1.0).

### `calgary-ct/`

Calgary Transit CTrain Red + Blue lines. Station IDs and coordinates from the open Calgary Transit GTFS feed; ridership priors estimated from Calgary's public quarterly ridership snapshots.

## Files

| File | Description |
|------|-------------|
| `stations.csv` | Station catalogue with line, lat/lon, and a normalised ridership prior. |
| `events.csv` | Reference special-event catalogue: venue, time window, expected attendance. |

## Schema

`stations.csv`:

```
station_id,name,line,latitude,longitude,ridership_prior
```

- `station_id` — primary key; matches the GTFS `stop_id` where applicable.
- `line` — single-character or hyphen-delimited line codes (e.g. `Red`, `4-5-6`, `Red-Blue`).
- `ridership_prior` — relative weight (0..1) used to bias the synthetic generator toward realistic origin distributions.

`events.csv`:

```
event_id,name,venue_name,venue_latitude,venue_longitude,start_iso,end_iso,expected_attendance
```

## Sources

- [MTA Subway Hourly Ridership: Beginning 2025](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/wujg-7c2s)
- [MTA Daily Ridership Data: 2020-2025](https://data.ny.gov/Transportation/MTA-Daily-Ridership-Data-2020-2025/vxuj-8kew)
- [MTA GTFS Static](https://new.mta.info/developers)
- [Calgary Transit GTFS](https://data.calgary.ca/Transportation-Transit/Calgary-Transit-Scheduling-Data-Current-GTFS/npk7-z3bj)
- [Calgary Open Data Portal](https://data.calgary.ca)

All data is public open data. No proprietary or personally-identifying records are included.
 ## Adding a new network  Drop a directory at `scripts/reference_data/<network>/` with `stations.csv` and `events.csv` matching the documented schema. Then add the network to the `Network` literal in `src/common/reference_data.py`.

## Schema notes
