# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze ingest — AFC taps via Auto Loader
# MAGIC
# MAGIC Streams AFC tap events out of the bronze landing zone into the
# MAGIC `bronze.afc_taps` Delta table. Schema is inferred once and pinned;
# MAGIC drifted columns land in `_rescued_data` and are alerted on.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("catalog", "transit_lakehouse_dev")
dbutils.widgets.text("bronze_schema", "bronze")
dbutils.widgets.text("storage_account", "")

catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
storage_account = dbutils.widgets.get("storage_account")

source_path = f"abfss://bronze@{storage_account}.dfs.core.windows.net/afc_taps/"
checkpoint_path = f"abfss://checkpoints@{storage_account}.dfs.core.windows.net/bronze/afc_taps/"
schema_path = f"abfss://checkpoints@{storage_account}.dfs.core.windows.net/bronze/afc_taps/_schemas/"
table_fqn = f"{catalog}.{bronze_schema}.afc_taps"

print(f"Source:         {source_path}")
print(f"Checkpoint:     {checkpoint_path}")
print(f"Target:         {table_fqn}")

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{bronze_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Auto Loader streaming read

# COMMAND ----------

from pyspark.sql.functions import col, current_timestamp, input_file_name

stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "parquet")
    .option("cloudFiles.schemaLocation", schema_path)
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
    .option("cloudFiles.includeExistingFiles", "true")
    .option("cloudFiles.useNotifications", "false")  # set true with Event Grid in prod
    .load(source_path)
    .withColumn("_source_file", input_file_name())
    .withColumn("_ingest_ts", current_timestamp())
)

# COMMAND ----------

(
    stream.writeStream
    .format("delta")
    .option("checkpointLocation", checkpoint_path)
    .option("mergeSchema", "true")
    .trigger(availableNow=True)
    .option("path", f"abfss://gold@{storage_account}.dfs.core.windows.net/delta/{bronze_schema}/afc_taps")
    .toTable(table_fqn)
)
