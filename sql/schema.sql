PRAGMA foreign_keys=ON;
CREATE TABLE companies(company_id INTEGER PRIMARY KEY, source_key TEXT UNIQUE NOT NULL, name TEXT NOT NULL);
CREATE TABLE locations(location_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE roles(role_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE skills(skill_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE jobs(
 job_id INTEGER PRIMARY KEY, title TEXT NOT NULL,
 company_id INTEGER NOT NULL REFERENCES companies(company_id),
 location_id INTEGER NOT NULL REFERENCES locations(location_id),
 role_id INTEGER NOT NULL REFERENCES roles(role_id),
 posted_date TEXT, salary_usd REAL CHECK(salary_usd>0),
 experience TEXT, work_type TEXT, remote INTEGER NOT NULL CHECK(remote IN (0,1)),
 views REAL, applies REAL, description_length INTEGER NOT NULL
);
CREATE TABLE job_skills(
 job_id INTEGER REFERENCES jobs(job_id), skill_id INTEGER REFERENCES skills(skill_id),
 PRIMARY KEY(job_id,skill_id)
);
CREATE INDEX idx_jobs_date ON jobs(posted_date);
CREATE INDEX idx_jobs_location ON jobs(location_id);
CREATE INDEX idx_jobs_role ON jobs(role_id);
CREATE INDEX idx_job_skills_skill ON job_skills(skill_id);
