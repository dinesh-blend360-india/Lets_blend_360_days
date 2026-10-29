# Databricks notebook source
# MAGIC %run ../00-common-setup/envirement-var-setup

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.drivers"
silver_table = f"{catalog_name}.{silver_schema}.drivers"

# COMMAND ----------

drivers_df = spark.table(bronze_table)

# COMMAND ----------

drivers_dropped_df = drivers_df.drop("url")

# COMMAND ----------

drivers_renamed_df = drivers_dropped_df.withColumnRenamed("driverId", "driver_id").withColumnRenamed("dateOfBirth", "date_of_birth")


# COMMAND ----------

from pyspark.sql import functions as F
drivers_concatinate_df =(
        drivers_renamed_df
        .withColumn("driver_name",
                    F.initcap(F.concat_ws(" ", F.col("name.givenName"), F.col("name.familyName")))
    ).drop("name")
        .withColumn("nationality", F.initcap(F.col("nationality")))

        )
    

# COMMAND ----------

display(drivers_concatinate_df)

# COMMAND ----------

drivers_distinct_df = drivers_concatinate_df.dropDuplicates(["driver_id"])
#here this is final since we alredy done all operations so lets take distinct as final

# COMMAND ----------

(
    drivers_concatinate_df
    .write
    .mode("overwrite")
    .format("delta")
    .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))


# COMMAND ----------

