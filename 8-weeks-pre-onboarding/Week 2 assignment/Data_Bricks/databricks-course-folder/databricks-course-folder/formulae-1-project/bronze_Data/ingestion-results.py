# Databricks notebook source
# MAGIC %md
# MAGIC 1 - read files using spark dataframe api
# MAGIC
# MAGIC 2 - add meta datacolumns:
# MAGIC         - source file
# MAGIC         - ingestion time stamp
# MAGIC         
# MAGIC 3 - write to bronze delta table 

# COMMAND ----------

# MAGIC %run ../00-common-setup/01-bronze-helpers

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

source_file = f'{landing_folder}/results'
table_name = f'{catalog_name}.{bronze_schema}.results'

# COMMAND ----------


from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType, DoubleType

results_schema = StructType([
    StructField('date', DateType()),
    StructField('raceName', StringType()),
    StructField('round', IntegerType()),
    StructField('season', IntegerType()),
    StructField('url', StringType()),
    StructField('constructorId', StringType()),
    StructField('driverId', StringType()),
    StructField('grid', IntegerType()),
    StructField('laps', IntegerType()),
    StructField('number',IntegerType()),
    StructField('points',DoubleType()),
    StructField('position', IntegerType()),
    StructField('positionText', StringType()),
    StructField('status', StringType())


])


# COMMAND ----------


results_df = (
    spark.read
    .format('json')
    .option('mode', 'FAILFAST')
    .schema(results_schema)
    .load(source_file)
)

# COMMAND ----------

display(results_df)

# COMMAND ----------

results_df_final_format = add_timestamp_source_file(results_df)

# COMMAND ----------

display(results_df_final_format)

# COMMAND ----------

(
    results_df_final_format
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(table_name)
)

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

