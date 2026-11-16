WITH averages AS (
 SELECT role_id, AVG(salary_usd) AS role_mean FROM jobs GROUP BY role_id
)
SELECT r.name AS role,COUNT(*) AS above_average_jobs
FROM jobs j JOIN roles r USING(role_id) JOIN averages a USING(role_id)
WHERE j.salary_usd>a.role_mean
GROUP BY r.role_id ORDER BY above_average_jobs DESC;
