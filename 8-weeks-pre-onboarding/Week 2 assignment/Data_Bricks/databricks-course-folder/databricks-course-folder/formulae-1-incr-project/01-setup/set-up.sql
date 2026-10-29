-- Databricks notebook source
-- MAGIC %md
-- MAGIC # create an external location here 

-- COMMAND ----------

create external location if not exists databricks_formulae1_incr_project
url 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/'
with (storage credential `databricks-learning-sc`)
comment 'external location for formulae1-incr-project';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC # now can acess the external location

-- COMMAND ----------

-- MAGIC
-- MAGIC %fs ls 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/landing'
-- MAGIC

-- COMMAND ----------

-- MAGIC %python
-- MAGIC spark.sql("SHOW CATALOGS").show()

-- COMMAND ----------

-- MAGIC %md
-- MAGIC # Create a Catalogue here

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS formulae1_incr
    MANAGED LOCATION 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/' 
    COMMENT 'main catalog for formulae1' ;

-- COMMAND ----------

-- MAGIC %md 
-- MAGIC # create catalog file storage location and schema locations

-- COMMAND ----------

CREATE SCHEMA  IF NOT EXISTS  formulae1_incr.landing;
CREATE SCHEMA  IF NOT EXISTS  formulae1_incr.bronze
    MANAGED LOCATION 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/bronze';
CREATE SCHEMA  IF NOT EXISTS  formulae1_incr.silver
    MANAGED LOCATION 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/silver';
CREATE SCHEMA  IF NOT EXISTS  formulae1_incr.gold
    MANAGED LOCATION 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/gold';

-- COMMAND ----------

select current_catalog();

-- COMMAND ----------

use catalog formulae1_incr;

-- COMMAND ----------

show schemas;

-- COMMAND ----------

-- MAGIC %md 
-- MAGIC # craete external volume

-- COMMAND ----------

create external volume formulae1_incr.landing.files
location 'abfss://formula1-incr@dineshstorageaccountlear.dfs.core.windows.net/landing';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC # Acess external Volume

-- COMMAND ----------

-- MAGIC %fs ls /Volumes/formulae1_incr/landing/files

-- COMMAND ----------

    