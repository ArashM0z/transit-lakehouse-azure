# Databricks notebook source
# MAGIC %md
# MAGIC # Gold — orchestrate dbt
# MAGIC
# MAGIC Triggers `dbt build` against the production profile from inside the
# MAGIC Databricks workspace. Used when running gold transformations on the
# MAGIC same compute as silver, instead of via dbt Cloud.

# COMMAND ----------

# MAGIC %pip install dbt-databricks==1.8.7 dbt-core==1.8.7 --quiet
# MAGIC %restart_python

# COMMAND ----------

import os
import subprocess

DBT_PROJECT_DIR = "/Workspace/Repos/transit-lakehouse/dbt"
DBT_PROFILES_DIR = "/Workspace/Repos/transit-lakehouse/dbt/profiles"

result = subprocess.run(
    [
        "dbt",
        "build",
        "--project-dir",
        DBT_PROJECT_DIR,
        "--profiles-dir",
        DBT_PROFILES_DIR,
        "--target",
        "prod",
    ],
    capture_output=True,
    text=True,
    check=False,
)
print("STDOUT:\n", result.stdout)
print("STDERR:\n", result.stderr)

if result.returncode != 0:
    raise RuntimeError(f"dbt build failed (rc={result.returncode})")
