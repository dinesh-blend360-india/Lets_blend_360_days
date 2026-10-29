# Databricks notebook source

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/03-gold-helper

# COMMAND ----------

from pyspark.sql import functions as F


# COMMAND ----------

target_table = f'{catalog_name}.{gold_schema}.drivers_dim'

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

driver_df = spark.table(f"{catalog_name}.{silver_schema}.drivers").filter(F.col("batch_id")==v_batch_id)
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

write_to_gold(
    input_df=drivers_dim_df,
    target_table=target_table,
    merge_condition="t.driver_id=s.driver_id",
    columns_to_update=[
        "driver_name",
        "date_of_birth",
        "nationality",
        "nationality_of_region"
    ]
)