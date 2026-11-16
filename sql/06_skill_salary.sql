SELECT s.name AS skill, COUNT(j.salary_usd) AS salary_known, AVG(j.salary_usd) AS mean_salary_usd
FROM jobs j JOIN job_skills js USING(job_id) JOIN skills s USING(skill_id)
WHERE j.salary_usd IS NOT NULL GROUP BY s.skill_id HAVING COUNT(*)>=10 ORDER BY mean_salary_usd DESC;
