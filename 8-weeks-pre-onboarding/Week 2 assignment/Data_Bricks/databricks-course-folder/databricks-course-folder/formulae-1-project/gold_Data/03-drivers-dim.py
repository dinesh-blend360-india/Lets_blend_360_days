# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

target_table = f'{catalog_name}.{gold_schema}.drivers_dim'

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

driver_df = spark.table(f"{catalog_name}.{silver_schema}.drivers")
ref_nationality_df = spark.table(f'{catalog_name}.{gold_schema}.ref_nationality_region')

# COMMAND ----------

drivers_dim_df = (
    driver_df
    .join(ref_nationality_df,
          driver_df.nationality == ref_nationality_df.nationality,
          'left'
          )
    .select(
        driver_df.driver_id,
        driver_df.driver_name,
        driver_df.date_of_birth,
        driver_df.nationality,
        ref_nationality_df.region.alias("nationality_region")
    )
)

# COMMAND ----------

display(drivers_dim_df)

# COMMAND ----------


(
    drivers_dim_df 
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(target_table)
)