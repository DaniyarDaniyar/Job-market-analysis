WITH counts AS (
 SELECT c.name AS company, COUNT(*) AS jobs FROM jobs j JOIN companies c USING(company_id)
 GROUP BY c.company_id
) SELECT *, ROW_NUMBER() OVER(ORDER BY jobs DESC,company) AS company_rank FROM counts
ORDER BY company_rank LIMIT 25;
