# Databricks notebook source
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

# MAGIC %run ../00-common-setup/02-silver-helper

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.results"
silver_table = f"{catalog_name}.{silver_schema}.results"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

results_df = (
  spark.table(bronze_table)
       .filter((F.col("batch_id") == v_batch_id))
       .select("season",
                "round",
                "constructorId",
                "driverId",
                "date",
                "raceName",
                "grid",
                "laps",
                "number",
                "points",
                "position",
                "positionText",
                "status",
                "timestamp",
                "source_file",
                "batch_id")

)

# COMMAND ----------

display(results_df)

# COMMAND ----------

# results_selected_df = results_df.select(
#     "season",
#     "round",
#     "constructorId",
#     "date",
#     "raceName",
#     "grid",
#     "laps",
#     "number",
#     "points",
#     "position",
#     "positionText",
#     "status",
#     "timestamp",
#     "source_file",
#     "driverId"
# )

# COMMAND ----------

results_renamed_df =(results_df.withColumnRenamed('constructorId', 'constructor_id')
.withColumnRenamed('raceName', 'race_name')
.withColumnRenamed('positionText', 'position_text')
.withColumnRenamed('position', 'final_position')
.withColumnRenamed('date', 'race_date')
.withColumnRenamed('driverId', 'driver_id')
)


# COMMAND ----------

results_valid_data = results_renamed_df.filter(
    F.col("season").isNotNull() & F.col("round").isNotNull() & F.col('constructor_id').isNotNull() & F.col('driver_id').isNotNull()
)

# COMMAND ----------

results_distinct_df = results_valid_data.dropDuplicates(
    ["season", "round", "constructor_id", "driver_id"]
)

# COMMAND ----------

resutls_final_df = results_distinct_df.withColumn("race_name", F.initcap(F.col("race_name")))

# COMMAND ----------


write_to_silver(
    input_df=resutls_final_df,
    target_table=silver_table,
    merge_condition="t.season = s.season AND t.round = s.round AND t.constructor_id = s.constructor_id AND t.driver_id = s.driver_id",
    columns_to_update=[
        "race_name",
        "race_date",
        "grid_position",
        "completed_laps",
        "car_number",
        "points",
        "final_position",
        "final_position_text",
        "status",
        "timestamp",
        "source_file",
        "batch_id"
    ]
)

# COMMAND ----------

(
    resutls_final_df
    .write
    .format('delta')
    .mode('overwrite')
   .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))