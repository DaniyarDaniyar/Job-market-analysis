SELECT s.name AS skill, COUNT(*) AS jobs,
 ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM jobs),2) AS pct_jobs
FROM job_skills js JOIN skills s USING(skill_id)
GROUP BY s.skill_id ORDER BY jobs DESC, skill;
