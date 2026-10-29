# Databricks notebook source
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/02-silver-helper

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.races"
silver_table = f"{catalog_name}.{silver_schema}.races"

# COMMAND ----------

from pyspark.sql import functions as F 

# COMMAND ----------

races_df = spark.table(bronze_table).filter(F.col(F"batch_id") == v_batch_id)

# COMMAND ----------

from pyspark.sql import functions as F
races_selected_df = races_df.select(
    F.col("season"),
    F.col("circuitId"),
    F.col("round"),
    F.col("raceName"),
    F.col("date"),
    F.col("timestamp"),
    F.col("source_file"),
    F.col("batch_id")
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

races_final_df = (
    races_final_df
    .withColumn("created_timestamp", F.current_timestamp())
    .withColumn("updated_timestamp", F.current_timestamp())
)

# COMMAND ----------

if races_final_df.isEmpty():
    print("races_final_df is empty. Please check upstream filters or data availability for batch_id:", v_batch_id)
else:
    display(races_final_df)

# COMMAND ----------

write_to_silver(
    input_df=races_final_df,
    target_table=silver_table,
    merge_condition="t.season = s.season AND t.round = s.round",
    columns_to_update=[
        "race_name",
        "race_date",
        "circuit_id",
        "timestamp",
        "source_file",
        "batch_id"
    ]
)

# COMMAND ----------

# (
#     races_final_df
#     .write
#     .mode('overwrite')
#     .format('delta')
#     .saveAsTable(silver_table)
# )

# COMMAND ----------

display(spark.table(silver_table))

# COMMAND ----------

