import pandas as pd
from jobmarket.ingest import build_database
from jobmarket.dashboard import filtered_jobs,skill_counts

def test_filters_and_empty_results(tmp_path):
    p=tmp_path/'data.csv'
    pd.DataFrame([dict(job_id=1,title='Data Analyst',location="O'Fallon",description='SQL',original_listed_time=1712880000000)]).to_csv(p,index=False)
    build_database(p,tmp_path/'out')
    db=tmp_path/'out/jobs.db'
    assert len(filtered_jobs(db,years=['2024'],locations=["O'Fallon"]))==1
    assert filtered_jobs(db,locations=["' OR 1=1 --"]).empty
    assert skill_counts(db,[]).empty
    assert skill_counts(db,[1]).iloc[0]['jobs']==1
