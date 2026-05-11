# Row-Level Security (RLS)

## Model

Dynamic RLS on the `dim_station` dimension, scoped by `USERPRINCIPALNAME()`
against a `dim_user_access` (user × allowed_station_ids) table.

```dax
[station_id] IN
CALCULATETABLE(
    VALUES('dim_user_access'[station_id]),
    'dim_user_access'[user_principal_name] = USERPRINCIPALNAME()
)
```

## Roles

| Role | Scope |
|------|-------|
| `executive` | All stations |
| `marketing-analyst` | All stations except experimental pilots |
| `operations-{line}` | One line only |
| `external-partner-{partner-id}` | Specific station(s) on partnership pilots |

## Test users

| User | Role | Expected access |
|------|------|-----------------|
| `analyst-all@example.com` | executive | All |
| `analyst-lsw@example.com` | operations-lsw | Lakeshore West only |
| `partner-pearson@example.com` | external-partner-PEARSON | Pearson UP only |

Use Tabular Editor's "View as Roles" feature with the test users above
before each Production promotion.

## Validation in CI

`pbi-tools` test the RLS model by querying with each role and asserting the
visible row count. See `.github/workflows/powerbi.yml`.
