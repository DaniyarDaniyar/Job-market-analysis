WITH daily AS (
 SELECT posted_date, COUNT(*) AS jobs FROM jobs WHERE posted_date IS NOT NULL GROUP BY posted_date
) SELECT *, AVG(jobs) OVER(ORDER BY julianday(posted_date) RANGE BETWEEN 6 PRECEDING AND CURRENT ROW)
 AS mean_over_observed_days_last_week FROM daily ORDER BY posted_date;
