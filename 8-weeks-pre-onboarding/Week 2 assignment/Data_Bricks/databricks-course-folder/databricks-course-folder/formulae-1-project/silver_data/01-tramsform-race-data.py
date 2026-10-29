# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.races"
silver_table = f"{catalog_name}.{silver_schema}.races"

# COMMAND ----------

races_df = spark.table(bronze_table)

# COMMAND ----------

from pyspark.sql import functions as F
races_selected_df = races_df.select(
    F.col("season"),
    F.col("round"),
    F.col("raceName"),
    F.col("date"),
    F.col("circuitId"),
    F.col("timestamp"),
    F.col("source_file")
    )


# COMMAND ----------

races_renamed_df = (
    races_selected_df
    .withColumnRenamed("circuitId", "circuit_id")
    .withColumnRenamed("raceName", "race_name")
    .withColumnRenamed("date", "race_date")
)

# COMMAND ----------

races_distinct_df = races_renamed_df.dropDuplicates(["season","round"])

# COMMAND ----------

races_final_df = races_distinct_df.withColumn('race_name', F.initcap('race_name'))

# COMMAND ----------

display(races_final_df)

# COMMAND ----------

(
    races_final_df
    .write
    .mode('overwrite')
    .format('delta')
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))

# COMMAND ----------

