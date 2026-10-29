# Databricks notebook source

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/03-gold-helper

# COMMAND ----------

target_table = f'{catalog_name}.{gold_schema}.dim_constructors'

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

display(spark.table(f'{catalog_name}.{silver_schema}.constructors'))

# COMMAND ----------

constructor_df = (spark.table(f'{catalog_name}.{silver_schema}.constructors')
                  .filter(F.col('batch_id') == v_batch_id)
                  )
ref_nationality_df = spark.table(f'{catalog_name}.{gold_schema}.ref_nationality_region')


# COMMAND ----------

dim_constructor_df = (
    constructor_df
    .join(ref_nationality_df, 
          constructor_df.nationality == ref_nationality_df.nationality,
          'left'
          )
    .select(
        constructor_df.constructor_id,
        constructor_df.constructor_name,
        constructor_df.nationality,
        ref_nationality_df.region.alias('nationality_region')
    )
)

# COMMAND ----------

write_to_gold(
    input_df=dim_constructor_df,
    target_table=target_table,
    merge_condition="t.constructor_id = s.constructor_id",
    columns_to_update=[
        "constructor_name",
        "nationality",
        "nationality_region",
        
    ]
)

# COMMAND ----------

# (
#     dim_constructor_df
#     .write
#     .mode('overwrite')
#     .format('delta')
#     .saveAsTable(target_table)
# )

# COMMAND ----------

display(spark.table(target_table))

# COMMAND ----------

