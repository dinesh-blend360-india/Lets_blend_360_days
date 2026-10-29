-- Databricks notebook source
-- MAGIC %fs ls 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/landing'
-- MAGIC

-- COMMAND ----------

create external location if not exists databricks_formulae1_project
url 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/'
with (storage credential `databricks-learning-sc`)
comment 'external location for formulae1-project';

-- COMMAND ----------

-- MAGIC %python
-- MAGIC spark.sql("SHOW CATALOGS").show()

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS formulae1
    MANAGED LOCATION 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/' 
    COMMENT 'main catalog for formulae1' ;

-- COMMAND ----------

CREATE SCHEMA  IF NOT EXISTS  formulae1.landing;
CREATE SCHEMA  IF NOT EXISTS  formulae1.bronze
    MANAGED LOCATION 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/bronze';
CREATE SCHEMA  IF NOT EXISTS  formulae1.silver
    MANAGED LOCATION 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/silver';
CREATE SCHEMA  IF NOT EXISTS  formulae1.gold
    MANAGED LOCATION 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/gold';

-- COMMAND ----------

select current_catalog();

-- COMMAND ----------

use catalog formulae1;

-- COMMAND ----------

show schemas;

-- COMMAND ----------

create external volume formulae1.landing.files
location 'abfss://formula1@dineshstorageaccountlear.dfs.core.windows.net/landing';