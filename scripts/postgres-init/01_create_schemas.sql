-- Schemas used by the dbt dev profile and MLflow backing store.
-- Run automatically by the Postgres init mount.

CREATE SCHEMA IF NOT EXISTS dbt_dev;
CREATE SCHEMA IF NOT EXISTS dbt_dev_bronze;
CREATE SCHEMA IF NOT EXISTS dbt_dev_silver;
CREATE SCHEMA IF NOT EXISTS dbt_dev_gold;
CREATE SCHEMA IF NOT EXISTS dbt_dev_marts;
CREATE SCHEMA IF NOT EXISTS mlflow;
