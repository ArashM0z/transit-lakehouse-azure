# Runbook

One section per alert. Each section follows: **Symptom** → **Check** → **Mitigation** → **Rollback**.

## `bronze_freshness_breach`

**Symptom:** Bronze-zone freshness p95 > 5 minutes for 15 consecutive minutes.

**Check:**
1. Open the [Bronze freshness](http://localhost:3000/d/transit-bronze-freshness) Grafana dashboard.
2. In Azure Monitor: `AppMetrics | where Name == "lakehouse_bronze_freshness_seconds" | summarize p95=percentile(Sum/Count, 95) by bin(TimeGenerated, 5m)`.
3. Confirm the Event Hubs partition consumer lag (`KafkaConsumerLag`).
4. Check `databricks jobs runs list --job-id bronze_ingest --active-only`.

**Mitigation:**
1. If consumer lag is climbing: scale the bronze ingest job cluster up to the policy ceiling (4 workers).
2. If the job is failing: pull the latest run log via `databricks jobs runs get <run-id>`; common causes are ADLS write throttling and schema-evolution rescues.
3. If Event Hubs is the bottleneck: scale up throughput units (Standard tier) or partitions (one-time operation).

**Rollback:** Re-pin Spark version and revert the most recent DAB deploy: `databricks bundle deploy --target dev -p <prev-tag>`.

---

## `silver_freshness_breach`

**Symptom:** Silver DLT pipeline freshness p95 > 15 minutes.

**Check:**
1. DLT event log for `silver_dlt`: `SELECT * FROM event_log('silver_dlt') ORDER BY timestamp DESC LIMIT 200`.
2. Look for `FLOW_PROGRESS` records with `status = STARTING` for > 10 min, or `STOPPED` with errors.
3. Quarantined rows: `SELECT COUNT(*) FROM transit_lakehouse.silver.silver_afc_taps WHERE _rescued_data IS NOT NULL`.

**Mitigation:**
1. Restart the failing flow: `databricks pipelines update --pipeline-id <id>`.
2. If schema drift caused a column-type conflict, alter the expectation and redeploy.
3. If load is the issue, switch the cluster to enhanced autoscaling and raise max workers.

**Rollback:** Re-deploy the previous DAB tag; bronze data is immutable so silver can be rebuilt safely.

---

## `gold_freshness_breach`

**Symptom:** Gold marts older than 1 hour.

**Check:**
1. `dbt run-operation print_run_status` or check the latest dbt artifacts.
2. Confirm the Databricks SQL Warehouse isn't saturated: warehouse > Queries tab.
3. Check the dbt job in the orchestrator (Airflow / Databricks Workflows).

**Mitigation:**
1. Re-run the failing model: `dbt run --select <model>+ --target prod`.
2. Scale up the SQL warehouse size by one tier; revert after backfill.

**Rollback:** Gold tables are deterministic — re-running dbt restores the previous state.

---

## `pbi_perf_breach`

**Symptom:** Power BI report load time p95 > 3 seconds.

**Check:**
1. Power BI Service > workspace > Settings > Performance.
2. DAX Studio query plan + VertiPaq Analyzer snapshot.
3. Databricks SQL Query History — slow queries hit from DirectQuery.

**Mitigation:**
1. Pre-aggregate large fact tables (composite model + aggregations).
2. Switch low-cardinality measures from DirectQuery to Import mode.
3. Add columnstore-friendly Z-order on the gold table (`dt`, `station_id`).
4. Raise SQL warehouse size temporarily; reduce after.

**Rollback:** Revert the most recent Power BI deployment pipeline stage promotion.

---

## `cost_anomaly`

**Symptom:** Pipeline daily spend > $4 (dev) or > defined budget (prod).

**Check:**
1. Azure Cost Management — drill by tag `cost_center=portfolio`.
2. Databricks Cost & Usage system tables.
3. Cluster policy compliance: `databricks cluster-policies get --policy-id <id>`.

**Mitigation:**
1. Identify the runaway cluster; terminate immediately.
2. Tighten the cluster policy: lower max workers, lower autotermination.
3. Add a budget alert at 80% of the daily ceiling.

**Rollback:** N/A — cost remediation only.
 ## Escalation  Primary acknowledges in 5 minutes; if no ack in 10, PagerDuty rotates to secondary; if no ack in 15, EM-on-call is paged.

## Footer
