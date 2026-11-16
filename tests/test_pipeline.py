import sqlite3
import pandas as pd
import pytest
from jobmarket.ingest import annual_salary, build_database
from jobmarket.skills import extract_skills

@pytest.mark.parametrize('row,expected', [
    ({'min_salary': 20, 'max_salary': 30, 'pay_period': 'HOURLY', 'currency':'USD'},52000),
    ({'med_salary': 5000, 'pay_period':'MONTHLY','currency':'USD'},60000),
    ({'min_salary': 100, 'max_salary': 50, 'pay_period':'YEARLY','currency':'USD'},None),
    ({'med_salary': -1,'pay_period':'YEARLY','currency':'USD'},None),
    ({'med_salary': 80000,'pay_period':'YEARLY','currency':'EUR'},None),
    ({'med_salary': 80000,'pay_period':'YEARLY'},None),
    ({'med_salary': 80000,'pay_period':'UNKNOWN','currency':'USD'},None),
])
def test_salary_units_and_invalid_ranges(row, expected):
    assert annual_salary(row) == expected

def test_skill_boundaries_aliases_and_deduplication():
    assert extract_skills('JavaScript and Python, python; PostgreSQL. C++ and C#.') == ['C#','C++','JavaScript','Python','SQL']
    assert extract_skills('Excellent communication; excel at tasks; go to work') == ['Communication']
    assert extract_skills('Microsoft Excel, Amazon Web Services and PowerBI') == ['AWS','Excel','Power BI']

def test_ingestion_deduplicates_across_chunks_and_has_foreign_keys(tmp_path):
    path=tmp_path/'input.csv'
    pd.DataFrame([
        dict(job_id='1',title='Data Analyst',company_name='A',location='NY',description='Python SQL',original_listed_time=1712880000000),
        dict(job_id='1',title='Duplicate',company_name='B',location='NY',description='Java',original_listed_time=1712880000000),
        dict(job_id='2',title='Engineer',company_name='A',location='LA',description='SQL',original_listed_time=1712966400000),
    ]).to_csv(path,index=False)
    result=build_database(path,tmp_path/'out',chunksize=1)
    with sqlite3.connect(tmp_path/'out/jobs.db') as conn:
        assert conn.execute('select count(*) from jobs').fetchone()[0]==2
        assert conn.execute('select count(*) from job_skills').fetchone()[0]==3
        assert conn.execute('pragma foreign_key_check').fetchall()==[]
        assert conn.execute('select title from jobs where job_id=1').fetchone()[0]=='Data Analyst'
    assert result['duplicates']==1
    assert len(pd.read_parquet(tmp_path/'out/jobs.parquet'))==2

def test_missing_columns_rejected(tmp_path):
    p=tmp_path/'bad.csv'; p.write_text('foo\nbar\n')
    with pytest.raises(ValueError,match='Missing required'):
        build_database(p,tmp_path/'out')
