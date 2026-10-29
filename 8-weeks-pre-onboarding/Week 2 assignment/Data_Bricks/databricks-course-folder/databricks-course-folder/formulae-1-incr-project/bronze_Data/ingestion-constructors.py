# Databricks notebook source
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup
# MAGIC

# COMMAND ----------

# MAGIC %run ../00-common-setup/01-bronze-helpers

# COMMAND ----------

source_file = f'{landing_folder}/{v_batch_id}/constructors.json'
table_name = f'{catalog_name}.{bronze_schema}.constructors'

# COMMAND ----------

constructor_schema = """
constructorId STRING,
name STRING,
nationality String,
url STRING"""

# COMMAND ----------

constructor_df = (
    spark.read
    .format('json')
    .schema(constructor_schema)
    .option('mode', 'FAILFAST')
    .load(source_file)
)

# COMMAND ----------

display(constructor_df)

# COMMAND ----------

constructor_final_df = add_timestamp_source_file(constructor_df)

# COMMAND ----------

constructor_final_df = constructor_final_df.withColumn("batch_id", F.lit(v_batch_id))

# COMMAND ----------

# (
#     constructor_final_df
#     .write
#     .format('delta')
#     .mode('overwrite')
#     .saveAsTable(table_name)
# )
write_to_bronze(constructor_final_df, table_name, v_batch_id)

# COMMAND ----------

# (
#     constructor_final_df
#     .write
#     .format('delta')
#     .mode('overwrite')
#     .saveAsTable(table_name)
# )

# COMMAND ----------

display(constructor_final_df)

# COMMAND ----------

