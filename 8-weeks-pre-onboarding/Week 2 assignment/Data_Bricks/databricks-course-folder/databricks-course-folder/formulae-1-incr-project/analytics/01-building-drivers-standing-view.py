# Databricks notebook source
# MAGIC %sql
# MAGIC create or replace view formulae1.gold.drivers_standing
# MAGIC as 
# MAGIC with driver_session_summary as (
# MAGIC     select r.season, d.driver_id, d.driver_name,
# MAGIC     d.nationality, count(*) as race_starts, 
# MAGIC     sum(r.points) as total_points,
# MAGIC     count_if(r.is_win) as number_of_wins,
# MAGIC     count_if(r.is_podium) as number_of_podiums
# MAGIC     from formulae1.gold.facts_session_results r
# MAGIC     join formulae1.gold.drivers_dim d
# MAGIC     on r.driver_id = d.driver_id
# MAGIC     group by r.season, d.driver_id, d.driver_name, d.nationality
# MAGIC )
# MAGIC
# MAGIC select season, driver_id,driver_name, nationality, rank() over(partition by season order by total_points desc, number_of_wins desc) as standing, race_starts, total_points, number_of_wins, number_of_podiums
# MAGIC from driver_session_summary;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from formulae1.gold.drivers_standing where season = 2025;