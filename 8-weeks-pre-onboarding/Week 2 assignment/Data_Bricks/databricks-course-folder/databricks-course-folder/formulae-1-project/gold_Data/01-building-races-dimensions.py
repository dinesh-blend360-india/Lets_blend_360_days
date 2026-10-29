# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

from pyspark.sql import functions as F


# COMMAND ----------

target_table = f'{catalog_name}.{gold_schema}.dim_races'

# COMMAND ----------

circuits_df = spark.table(f'{catalog_name}.{silver_schema}.circuits')
races_df = spark.table(f'{catalog_name}.{silver_schema}.races')

# COMMAND ----------

dim_races_df = (
    races_df
    .join(circuits_df,
          races_df.circuit_id == circuits_df.circuit_id,
          'inner'
          )
    .select(
        races_df.season,
        races_df.round,
        races_df.race_name,
        races_df.race_date,
        circuits_df.circuit_id,
        circuits_df.locality,
        circuits_df.country
    )
)

# COMMAND ----------

display(dim_races_df)

# COMMAND ----------

(
    dim_races_df
    .write
    .format('delta')
    .mode('overwrite')
    .saveAsTable(target_table)
)