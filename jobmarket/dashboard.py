"""Parameterized SQL filters shared by the dashboard and tests."""
import sqlite3
import pandas as pd

def filtered_jobs(db,years=(),locations=(),roles=()):
    filters=[]; params=[]
    for column,values in [('substr(j.posted_date,1,4)',years),('l.name',locations),('r.name',roles)]:
        if values:
            filters.append(f'{column} IN ({",".join("?" for _ in values)})')
            params.extend(str(x) for x in values)
    query='''SELECT j.*,c.name AS company,l.name AS location,r.name AS role
             FROM jobs j JOIN companies c USING(company_id)
             JOIN locations l USING(location_id) JOIN roles r USING(role_id)'''
    if filters: query+=' WHERE '+' AND '.join(filters)
    with sqlite3.connect(db) as conn:
        return pd.read_sql_query(query,conn,params=params)

def skill_counts(db,ids):
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TEMP TABLE selected(job_id INTEGER PRIMARY KEY)')
        conn.executemany('INSERT INTO selected VALUES (?)',[(int(i),) for i in ids])
        return pd.read_sql_query('''SELECT s.name AS skill,COUNT(*) AS jobs FROM selected x
          JOIN job_skills js USING(job_id) JOIN skills s USING(skill_id)
          GROUP BY s.skill_id ORDER BY jobs DESC,skill''',conn)
