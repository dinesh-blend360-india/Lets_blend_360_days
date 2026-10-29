# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.circuits"
silver_table = f"{catalog_name}.{silver_schema}.circuits"


# COMMAND ----------

circuits_df = spark.table(bronze_table)

# COMMAND ----------

circuits_selected_df = circuits_df.select("circuitId", "circuitName","lat", "long", "locality", "country" "timestamp", "source_file")

# COMMAND ----------

from pyspark.sql import functions as F
circuits_selected_df = circuits_df.select(
    F.col("circuitId"),
    F.col("circuitName"),
    F.col("lat"),
    F.col("long"),
    F.col("locality"),
    F.col("country"),
    F.col("timestamp")
    )


# COMMAND ----------

circuits_renamed_df = (
    circuits_selected_df
    .withColumnRenamed("circuitId", "circuit_id")
    .withColumnRenamed("circuitName", "circuit_name")
    .withColumnRenamed("lat", "latitude")
    .withColumnRenamed("long", "longitude")
)

# COMMAND ----------

circuit_valid_df = circuits_renamed_df.filter(
    F.col("circuit_id").isNotNull()
)

# COMMAND ----------

#circuit_distinct_df = circuit_valid_df.distinct()
circuit_distinct_df = circuit_valid_df.dropDuplicates(["circuit_id"])

# COMMAND ----------

display(circuit_distinct_df)


# COMMAND ----------

circuit_final_df = (
    circuit_distinct_df
    .withColumn("circuit_name", F.initcap(F.col("circuit_name")))
    .withColumn("locality", F.initcap(F.col("locality")))
)



# COMMAND ----------

display(circuit_final_df)


# COMMAND ----------

(
    circuit_final_df
    .write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))