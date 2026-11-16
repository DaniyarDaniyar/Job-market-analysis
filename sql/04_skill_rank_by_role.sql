WITH counts AS (
 SELECT r.name AS role, s.name AS skill, COUNT(*) AS jobs
 FROM jobs j JOIN roles r USING(role_id) JOIN job_skills js USING(job_id) JOIN skills s USING(skill_id)
 GROUP BY r.role_id,s.skill_id
), ranked AS (
 SELECT *, DENSE_RANK() OVER(PARTITION BY role ORDER BY jobs DESC) AS skill_rank FROM counts
) SELECT * FROM ranked WHERE skill_rank<=5 ORDER BY role,skill_rank,skill;
