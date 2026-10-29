# Databricks notebook source
# MAGIC %sql
# MAGIC create or replace view formulae1.gold.onstructors_standing
# MAGIC as 
# MAGIC with constructors_session_summary as (
# MAGIC     select r.season, c.constructor_id, c.constructor_name,
# MAGIC     c.nationality, count(*) as race_starts, 
# MAGIC     sum(r.points) as total_points,
# MAGIC     count_if(r.is_win) as number_of_wins,
# MAGIC     count_if(r.is_podium) as number_of_podiums
# MAGIC     from formulae1.gold.facts_session_results r
# MAGIC     join formulae1.gold.dim_constructors c
# MAGIC     on r.constructor_id = c.constructor_id
# MAGIC     group by r.season, c.constructor_id, c.constructor_name, c.nationality
# MAGIC )
# MAGIC
# MAGIC select season, constructor_id, constructor_name, nationality, rank() over(partition by season order by total_points desc, number_of_wins desc) as standing, race_starts, total_points, number_of_wins, number_of_podiums
# MAGIC from constructors_session_summary;