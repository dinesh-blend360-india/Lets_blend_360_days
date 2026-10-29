# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

bronze_table = f'{catalog_name}.{bronze_schema}.sprints'
silver_table = f'{catalog_name}.{silver_schema}.sprints'


# COMMAND ----------

sprints_df = (
    spark.table(bronze_table)
)

# COMMAND ----------

from pyspark.sql import functions as F
sprints_final_df = ( sprints_df
    .select(
        "season",
        "round",
        "constructorId",
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
        "driverId"
    )
    .withColumnRenamed("raceName", "race_name")
    .withColumnRenamed("constructorId", "constructor_id")
    .withColumnRenamed("driverId", "driver_id")
    .withColumnRenamed("positionText", "position_text")
    .withColumnRenamed("position", "final_position")
    .withColumnRenamed("date", "race_date")
    .filter(
    F.col("season").isNotNull() & F.col("round").isNotNull() & F.col('constructor_id').isNotNull() & F.col('driver_id').isNotNull()
           )
    .dropDuplicates(
    ["season", "round", "constructor_id", "driver_id"]
        )
    .withColumn("race_name", F.initcap(F.col("race_name")))

)

# COMMAND ----------

(
    sprints_final_df
    .write
    .format('delta')
    .mode('overwrite')
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))