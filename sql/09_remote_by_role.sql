SELECT r.name AS role, COUNT(*) AS jobs, SUM(j.remote) AS remote_flagged,
 100.0*SUM(j.remote)/COUNT(*) AS remote_flagged_pct
FROM jobs j JOIN roles r USING(role_id) GROUP BY r.role_id ORDER BY jobs DESC;
