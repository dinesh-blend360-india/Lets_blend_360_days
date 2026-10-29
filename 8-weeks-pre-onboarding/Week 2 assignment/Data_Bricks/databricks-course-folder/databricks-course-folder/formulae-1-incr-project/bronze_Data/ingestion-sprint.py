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

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/01-bronze-helpers

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

source_file = f'{landing_folder}/{v_batch_id}//sprints'
table_name = f'{catalog_name}.{bronze_schema}.sprints'

# COMMAND ----------


from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType, DoubleType

sprints_schema = StructType([
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


# sprints_df = (
#     spark.read
#     .format('json')
#     .option('mode', 'FAILFAST')
#     .schema(sprints_schema)
#     .option('multiLine', True)
#     .load(source_file)
# )
sprints_df = sprints_df.withColumn("batch_id", lit(v_batch_id))
write_to_bronze(sprints_df, table_name, v_batch_id)

# COMMAND ----------

display(sprints_df)

# COMMAND ----------

sprints_df_final_format = add_timestamp_source_file(sprints_df)

# COMMAND ----------

display(sprints_df_final_format)

# COMMAND ----------

(
    sprints_df_final_format
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(table_name)
)

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

