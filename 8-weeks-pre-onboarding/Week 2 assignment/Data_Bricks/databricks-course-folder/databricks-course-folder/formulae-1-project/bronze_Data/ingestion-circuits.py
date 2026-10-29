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

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/01-bronze-helpers

# COMMAND ----------

source_file = f'{landing_folder}/circuits.csv'
table_name = f'{catalog_name}.{bronze_schema}.circuits'


# COMMAND ----------


from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

circuit_schema = StructType([
    StructField('circuitId', StringType()),
    StructField('url', StringType()),
    StructField('circuitName', StringType()),
    StructField('lat', DoubleType()),
    StructField('long', DoubleType()),
    StructField('locality', StringType()),
    StructField('country', StringType())
])


# COMMAND ----------


circuit_df = (
    spark.read
    .format('csv')
    .option('header','true')
    .option('mode', 'FAILFAST')
    .schema(circuit_schema)
    .load(source_file)
)

# COMMAND ----------

display(circuit_df)

# COMMAND ----------

circuit_df_final_format = add_timestamp_source_file(circuit_df)

# COMMAND ----------

display(circuit_df_final_format)

# COMMAND ----------

(
    circuit_df_final_format
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(table_name)
)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from formulae1.bronze.circuits;

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

