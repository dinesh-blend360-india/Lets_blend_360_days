# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup
# MAGIC

# COMMAND ----------

# MAGIC %run ../00-common-setup/01-bronze-helpers

# COMMAND ----------

source_file = f'{landing_folder}/drivers.json'
table_name = f'{catalog_name}.{bronze_schema}.drivers'

# COMMAND ----------

from pyspark.sql.types import StructField, StructType, StringType, DateType

name_schema = StructType([
    StructField('givenName', StringType()),
    StructField('familyName',StringType())
])

drivers_schema = StructType([
    StructField('driverId', StringType()),
    StructField('name', name_schema),
    StructField('dateOfBirth', DateType()),
    StructField('nationality',StringType()),
    StructField('url',StringType())
])

# COMMAND ----------

drivers_df = (
    spark.read
    .format('json')
    .schema(drivers_schema)
    .option('mode','FAILFAST')
    .load(source_file)
)

# COMMAND ----------

drivers_final_df = add_timestamp_source_file(drivers_df)

# COMMAND ----------

(
    drivers_final_df
    .write
    .mode('overwrite')
    .saveAsTable(table_name)
)

# COMMAND ----------

display(drivers_final_df)

# COMMAND ----------

