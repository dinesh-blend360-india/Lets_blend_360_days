# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

target_table = f"{catalog_name}.{gold_schema}.facts_session_results"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

results_df = (
    spark.table(f'{catalog_name}.{silver_schema}.results')
    .withColumn("session_type", F.lit("RACE"))
    .drop("race_name", "race_date", "timestamp", "source_file")
)

# COMMAND ----------

sprints_df = (
    spark.table(f'{catalog_name}.{silver_schema}.sprints')
    .withColumn("session_type", F.lit("SPRINT"))
    .drop("race_name", "race_date", "timestamp", "source_file")
)

# COMMAND ----------

results_sprint_df = results_df.unionByName(sprints_df)

# COMMAND ----------

fact_session_df = (
    results_sprint_df
    .withColumn("is_win", F.col("final_position")==1)
    .withColumn("is_podium", F.col("final_position").between(1,3))
    .withColumn("has_points", F.col("points")>0)

)

# COMMAND ----------

display(fact_session_df.filter("season = 2025"))

# COMMAND ----------

(
    fact_session_df
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))