SELECT r.name AS role, COUNT(*) AS jobs, COUNT(j.salary_usd) AS salary_known,
 AVG(j.salary_usd) AS mean_salary_usd, MIN(j.salary_usd) AS min_salary_usd,
 MAX(j.salary_usd) AS max_salary_usd
FROM jobs j JOIN roles r USING(role_id) GROUP BY r.role_id ORDER BY jobs DESC;
