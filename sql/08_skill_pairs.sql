SELECT a.name AS skill_a,b.name AS skill_b,COUNT(*) AS jobs
FROM job_skills x JOIN job_skills y ON x.job_id=y.job_id AND x.skill_id<y.skill_id
JOIN skills a ON a.skill_id=x.skill_id JOIN skills b ON b.skill_id=y.skill_id
GROUP BY x.skill_id,y.skill_id HAVING COUNT(*)>=10 ORDER BY jobs DESC LIMIT 25;
