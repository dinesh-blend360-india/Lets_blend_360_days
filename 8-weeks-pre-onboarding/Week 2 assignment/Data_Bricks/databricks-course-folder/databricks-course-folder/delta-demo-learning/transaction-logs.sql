-- Databricks notebook source
create catalog if not exists democatalog
managed location 'abfss://demodatabriks@dineshstorageaccountlear.dfs.core.windows.net/'

-- COMMAND ----------

create schema if not exists democatalog.deltalake
managed location 'abfss://demodatabriks@dineshstorageaccountlear.dfs.core.windows.net/deltalake'

-- COMMAND ----------

create table if not exists democatalog.deltalake.companies(
    company_name string,
    format_date date,
    country string
)
using delta;

-- COMMAND ----------

desc extended democatalog.deltalake.companies

-- COMMAND ----------

insert into democatalog.deltalake.companies values
("microsoft", '1920-01-01', 'USA'),
("apple", '1921-01-01', 'london'),
("google", '1922-01-01', 'germany');


-- COMMAND ----------

select * from democatalog.deltalake.companies;

-- COMMAND ----------

