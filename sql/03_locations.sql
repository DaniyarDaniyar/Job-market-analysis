SELECT l.name AS location, COUNT(*) AS jobs, AVG(j.salary_usd) AS mean_salary_usd
FROM jobs j JOIN locations l USING(location_id)
GROUP BY l.location_id HAVING COUNT(*)>=10 ORDER BY jobs DESC LIMIT 25;
