# Databricks notebook source
from pyspark.sql import functions as F
def add_timestamp_source_file(df):
    return (df.withColumn('timestamp', F.current_timestamp())
                .withColumn('source_file', F.col('_metadata.file_path')))


# COMMAND ----------

def write_to_bronze(input_df, table_name, batch_id):
    # input_df = input_df.withColumn("batch_id", F.lit(batch_id))
    (input_df
    .write
    .mode('overwrite')
    .partitionBy("batch_id")
    .option("replaceWhere", f"batch_id = '{batch_id}'")
    .format('delta')
    .saveAsTable(table_name))


# COMMAND ----------

