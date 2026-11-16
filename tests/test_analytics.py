import numpy as np
import pandas as pd
from jobmarket.analytics import forecast_backtest, observed_run, run_queries
from jobmarket.ingest import build_database

def test_forecast_has_no_future_leakage():
    series=pd.Series(np.arange(1.,51.),index=pd.date_range('2024-01-01',periods=50))
    first,metrics=forecast_backtest(series,14)
    altered=series.copy(); altered.iloc[40:]=9999
    second,_=forecast_backtest(altered,14)
    pd.testing.assert_frame_equal(first.iloc[:5].drop(columns='actual'),second.iloc[:5].drop(columns='actual'))
    assert first.iloc[0]['naive']==36
    assert first.iloc[0]['moving_average']==33
    assert abs(first.iloc[0]['linear_trend']-37)<1e-8
    assert set(metrics['method'])=={'naive','moving_average','linear_trend'}

def test_observation_gaps_never_become_zero_counts():
    dates=pd.Series(['2024-01-01','2024-01-02','2024-03-01','2024-03-02','2024-03-03'])
    result=observed_run(dates)
    assert len(result)==3
    assert result.index.min()==pd.Timestamp('2024-03-01')
    assert list(result)==[1,1,1]

def test_all_queries_execute_and_skill_counts_match(tmp_path):
    p=tmp_path/'sample.csv'
    pd.DataFrame([dict(job_id=1,title='Analyst',location='NY',description='Python SQL',original_listed_time=1712880000000),dict(job_id=2,title='Engineer',location='LA',description='SQL',original_listed_time=1712966400000)]).to_csv(p,index=False)
    build_database(p,tmp_path/'data')
    tables=run_queries(tmp_path/'data/jobs.db',tmp_path/'reports')
    assert len(tables)>=8
    assert tables['01_skill_demand'].set_index('skill')['jobs'].to_dict()=={'SQL':2,'Python':1}

def test_analysis_without_salary_is_valid_json(tmp_path):
    import json
    from jobmarket.analytics import generate_analysis
    p=tmp_path/'sample.csv'
    pd.DataFrame([dict(job_id=1,title='Analyst',location='NY',description='SQL')]).to_csv(p,index=False)
    build_database(p,tmp_path/'data')
    generate_analysis(tmp_path/'data',tmp_path/'reports')
    result=json.loads((tmp_path/'reports/summary.json').read_text())
    assert result['salary_known']==0
    assert result['median_salary_usd'] is None
    assert result['iqr_low'] is None
    assert result['forecast_status'].startswith('insufficient')
