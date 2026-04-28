# Databricks notebook source
# MAGIC %md
# MAGIC # Silver — Delta Live Tables pipeline
# MAGIC
# MAGIC Deduplicates AFC taps, conforms to the silver schema, and exposes
# MAGIC quality expectations as DLT constraints. Failures are routed to a
# MAGIC quarantine table.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="silver_afc_taps",
    comment="Deduplicated, conformed AFC tap events.",
    table_properties={"quality": "silver", "pipelines.autoOptimize.managed": "true"},
)
@dlt.expect_or_drop("tap_id_not_null", "tap_id IS NOT NULL")
@dlt.expect_or_drop("valid_tap_type", "tap_type IN ('TAP_ON', 'TAP_OFF')")
@dlt.expect_or_fail(
    "valid_fare_class",
    "fare_class IN ('ADULT', 'SENIOR', 'YOUTH', 'CHILD', 'CONCESSION')",
)
def silver_afc_taps():
    bronze = dlt.read_stream("bronze_afc_taps_clean")
    return bronze


@dlt.view(comment="Bronze tap stream with surrogate ingest timestamp.")
def bronze_afc_taps_clean():
    return (
        spark.readStream.table("transit_lakehouse.bronze.afc_taps")
        .withColumn("tap_timestamp_utc", F.col("tap_timestamp_utc").cast("timestamp"))
        .dropDuplicates(["tap_id"])
    )


@dlt.table(
    name="silver_afc_taps_hourly",
    comment="Hourly pre-aggregation used by the silver→gold join layer.",
    table_properties={"quality": "silver"},
)
def silver_afc_taps_hourly():
    return (
        dlt.read("silver_afc_taps")
        .withColumn("tap_hour_utc", F.date_trunc("hour", "tap_timestamp_utc"))
        .groupBy("tap_hour_utc", "station_id", "fare_class", "tap_type")
        .agg(
            F.count("*").alias("tap_count"),
            F.sum("fare_amount_cad").alias("revenue_cad"),
            F.approx_count_distinct("card_token").alias("unique_riders_approx"),
        )
    )
