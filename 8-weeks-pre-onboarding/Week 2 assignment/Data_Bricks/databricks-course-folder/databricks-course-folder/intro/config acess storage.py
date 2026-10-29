# Databricks notebook source
# MAGIC %md #configure acess storage

# COMMAND ----------

# MAGIC %fs ls 'abfss://demodatabriks@dineshstorageaccountlear.dfs.core.windows.net/'

# COMMAND ----------

# MAGIC %sql
# MAGIC create external location if not exists databricks_storage_account_container_name_here
# MAGIC url 'abfss://demodatabriks@dineshstorageaccountlear.dfs.core.windows.net/'
# MAGIC with (storage credential `databricks-learning-sc`)
# MAGIC comment 'external location for the demo container';