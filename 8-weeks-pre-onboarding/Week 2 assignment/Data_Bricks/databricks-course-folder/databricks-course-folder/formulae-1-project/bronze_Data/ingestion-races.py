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

source_file = f'{landing_folder}/races.csv'
table_name = f'{catalog_name}.{bronze_schema}.races'

# COMMAND ----------


from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, DateType

races_schema = StructType([
    StructField('season', IntegerType()),
    StructField('round', IntegerType()),
    StructField('url', StringType()),
    StructField('raceName', StringType()),
    StructField('date', DateType()),
    StructField('circuitId', StringType())
])


# COMMAND ----------


races_df = (
    spark.read
    .format('csv')
    .option('header','true')
    .option('mode', 'FAILFAST')
    .schema(races_schema)
    .load(source_file)
)

# COMMAND ----------

display(races_df)

# COMMAND ----------

races_df_final_format = add_timestamp_source_file(races_df)

# COMMAND ----------

display(races_df_final_format)

# COMMAND ----------

(
    races_df_final_format
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(table_name)
)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from formulae1.bronze.races;

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

