# Databricks notebook source

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")  

# COMMAND ----------


from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `constructors` table

# COMMAND ----------


# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/02-silver-helper

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.constructors"
silver_table = f"{catalog_name}.{silver_schema}.constructors"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

constructors_dropped_df = constructors_df.drop("url")

# COMMAND ----------


constructors_df = (
    spark.table(bronze_table)
         .filter((F.col("batch_id") == v_batch_id))
)

# COMMAND ----------



constructors_selected_df = constructors_df.select(
    F.col("constructorId"),
    F.col("name"),
    F.col("nationality"),
    F.col("timestamp"),
    F.col("source_file"),
    F.col("batch_id")
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

constructors_final_df = (
    constructors_final_df
    .withColumn("created_timestamp", F.current_timestamp())
    .withColumn("updated_timestamp", F.current_timestamp())
)

# COMMAND ----------

display(constructors_final_df)

# COMMAND ----------


write_to_silver(
    input_df=constructors_final_df,
    target_table=silver_table,
    merge_condition="t.constructor_id = s.constructor_id",
    columns_to_update=[
        "constructor_name",
        "nationality",
        "timestamp",
        "source_file",
        "batch_id",
    ]
)

# COMMAND ----------

# (
#     constructors_final_df
#     .write
#     .mode("overwrite")
#     .format("delta")
#     .saveAsTable(silver_table)
# )

# COMMAND ----------

display(spark.table(silver_table))

# COMMAND ----------

