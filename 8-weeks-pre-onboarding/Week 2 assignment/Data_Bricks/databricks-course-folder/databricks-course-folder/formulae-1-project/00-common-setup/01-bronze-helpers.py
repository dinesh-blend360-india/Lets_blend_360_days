# Databricks notebook source
from pyspark.sql import functions as F
def add_timestamp_source_file(df):
    return (df.withColumn('timestamp', F.current_timestamp())
                .withColumn('source_file', F.col('_metadata.file_path')))
