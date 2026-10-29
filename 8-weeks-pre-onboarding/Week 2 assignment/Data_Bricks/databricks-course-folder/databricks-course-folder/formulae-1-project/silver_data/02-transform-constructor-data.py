# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.constructors"
silver_table = f"{catalog_name}.{silver_schema}.constructors"

# COMMAND ----------

constructors_df = spark.table(bronze_table)

# COMMAND ----------

from pyspark.sql import functions as F

constructors_selected_df = constructors_df.select(
    F.col("constructorId"),
    F.col("name"),
    F.col("nationality"),
    F.col("timestamp"),
    F.col("source_file")
)

# COMMAND ----------

constructors_renamed_df = (constructors_selected_df
                            .withColumnRenamed("constructorId", "constructor_id")
                            .withColumnRenamed("name", "constructor_name")                      
)

# COMMAND ----------

constructors_distinct_df = constructors_renamed_df.dropDuplicates(["constructor_id"])

# COMMAND ----------

constructors_final_df = (
    constructors_distinct_df
    .withColumn("nationality", F.initcap(F.col("nationality")))
)

# COMMAND ----------

display(constructors_final_df)

# COMMAND ----------

(
    constructors_final_df
    .write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))

# COMMAND ----------

