# Databricks notebook source
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/02-silver-helper

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.circuits"
silver_table = f"{catalog_name}.{silver_schema}.circuits"


# COMMAND ----------

from pyspark.sql import functions as F 

# COMMAND ----------

circuits_df = spark.table(bronze_table).filter(F.col(F"batch_id") == v_batch_id)

# COMMAND ----------

circuits_selected_df = circuits_df.select(
    F.col("circuitId"),
    F.col("circuitName"),
    F.col("lat"),
    F.col("long"),
    F.col("locality"),
    F.col("country"),
    F.col("timestamp"),
    F.col("source_file"),
    F.col("batch_id")
)

# COMMAND ----------

circuits_renamed_df = (
    circuits_selected_df
        .withColumnsRenamed({
            "circuitId": "circuit_id",
            "circuitName": "circuit_name",
            "lat": "latitude",
            "long": "longitude"
        })
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

circuit_final_df = (
    circuit_distinct_df
    .withColumn("created_timestamp", F.current_timestamp())
    .withColumn("updated_timestamp", F.current_timestamp())
)

# COMMAND ----------

display(circuit_final_df)


# COMMAND ----------

# if not spark.catalog.tableExists(silver_table):
#     (
#     circuit_final_df
#     .write
#     .mode("overwrite")
#     .format("delta")
#     .saveAsTable(silver_table)
#     )
# else:
#     from delta.tables import DeltaTable
#     delta_table = DeltaTable.forName(spark, silver_table)
#     (
#         delta_table.alias("t")
#         .merge(
#             circuit_distinct_df.alias("s"),
#             "t.circuit_id = s.circuit_id"
#         )
#         .whenMatchedUpdate(
#             condition="s.batch_id>=t.batch_id",
#             set = {
#                     "circuit_name": "s.circuit_name",
#                     "latitude": "s.latitude",
#                     "longitude": "s.longitude",
#                     "locality": "s.locality",
#                     "country": "s.country",
#                     "ingestion_timestamp": "s.ingestion_timestamp",
#                     "source_file": "s.source_file",
#                     "batch_id": "s.batch_id",
#                     "updated_timestamp": "s.updated_timestamp"    
#             }
#         )
#         .whenNotMatchedInsertAll()
#         .execute()
#     )

# COMMAND ----------

write_to_silver(
    input_df=circuit_final_df,
    target_table=silver_table,
    merge_condition="t.circuit_id = s.circuit_id",
    columns_to_update=[
        "circuit_name",
        "latitude",
        "longitude",
        "locality",
        "country",
        "timestamp",
        "source_file",
        "batch_id"        
    ]
)

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