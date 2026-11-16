"""Measured, reproducible descriptive analytics; no inference of population demand."""
from pathlib import Path
import json
import shutil
import sqlite3
import time
import tracemalloc
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
from statsmodels.tsa.seasonal import seasonal_decompose

ROOT=Path(__file__).resolve().parents[1]

def measure(call):
    tracemalloc.start()
    start=time.perf_counter()
    try:
        value=call()
        elapsed=time.perf_counter()-start
        _,peak=tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return value,elapsed,peak

def run_queries(db,output):
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    tables={}
    with sqlite3.connect(db) as conn:
        for file in sorted((ROOT/'sql').glob('[0-9]*.sql')):
            table=pd.read_sql_query(file.read_text(),conn)
            table.to_csv(output/(file.stem+'.csv'),index=False)
            tables[file.stem]=table
    return tables

def observed_run(dates):
    """Longest consecutive run with >=1 captured listing each day; gaps unknown."""
    dates=pd.to_datetime(dates,errors='coerce').dropna()
    if dates.empty:
        return pd.Series(dtype=float,index=pd.DatetimeIndex([]))
    daily=pd.Series(1,index=pd.DatetimeIndex(dates)).resample('D').sum(min_count=1)
    present=daily.notna()
    groups=present.ne(present.shift()).cumsum()
    runs=[g for _,g in daily[present].groupby(groups[present])]
    return max(runs,key=lambda g:(len(g),g.index.max())).astype(float)

def forecast_backtest(series,holdout=7):
    """Expanding one-step evaluation. Every prediction sees strictly earlier days."""
    if holdout<1 or len(series)-holdout<14 or series.isna().any():
        raise ValueError('Need 14 training days, positive holdout and no missing days')
    values=series.to_numpy(dtype=float)
    results=pd.DataFrame({'date':series.index[-holdout:],'actual':values[-holdout:]})
    metrics=[]
    for method in ['naive','moving_average','linear_trend']:
        def predict():
            predictions=[]
            for i in range(len(values)-holdout,len(values)):
                history=values[:i]
                if method=='naive':
                    pred=history[-1]
                elif method=='moving_average':
                    pred=history[-7:].mean()
                else:
                    # Fixed trailing 14 days: parameters chosen before holdout evaluation.
                    y=history[-14:]; slope,intercept=np.polyfit(np.arange(len(y)),y,1)
                    pred=max(0.,slope*len(y)+intercept)
                predictions.append(pred)
            return np.asarray(predictions)
        predictions,seconds,peak=measure(predict)
        results[method]=predictions
        metrics.append(dict(method=method,mae=float(np.abs(results.actual-predictions).mean()),
                            seconds=seconds,python_peak_bytes=peak,holdout_days=holdout))
    return results,pd.DataFrame(metrics)

def benchmark_storage(df,output):
    output=Path(output)
    csv=output/'benchmark.csv'; parquet=output/'benchmark.parquet'
    df.to_csv(csv,index=False); df.to_parquet(parquet,index=False,compression='zstd')
    rows=[]
    for fmt,path,reader in [('CSV',csv,pd.read_csv),('Parquet',parquet,pd.read_parquet)]:
        for trial in range(3):
            loaded,seconds,peak=measure(lambda:reader(path))
            rows.append(dict(format=fmt,trial=trial+1,bytes=path.stat().st_size,
                             seconds=seconds,python_peak_bytes=peak,rows=len(loaded)))
    csv.unlink(); parquet.unlink()
    return pd.DataFrame(rows)

def generate_analysis(processed='data/processed',output='reports'):
    processed,output=Path(processed),Path(output)
    figures=output/'figures'; figures.mkdir(parents=True,exist_ok=True)
    df=pd.read_parquet(processed/'jobs.parquet')
    if df.empty:
        raise ValueError('No valid jobs to analyze')
    queries=run_queries(processed/'jobs.db',output/'sql')
    audit=json.loads((processed/'audit.json').read_text())
    (output/'audit.json').write_text(json.dumps(audit,indent=2))
    missing=pd.DataFrame([{'column':k,'missing':v,'pct':100*v/audit['input_rows']} for k,v in audit['missing'].items()])
    missing.sort_values('pct',ascending=False).to_csv(output/'missingness.csv',index=False)
    df.select_dtypes('number').describe().to_csv(output/'descriptive_statistics.csv')
    salary=df.salary_usd.dropna()
    q1,q3=salary.quantile([.25,.75]) if len(salary) else (np.nan,np.nan)
    low,high=q1-1.5*(q3-q1),q3+1.5*(q3-q1)
    outlier=(salary<low)|(salary>high)
    corrcols=['salary_usd','views','applies','description_length']
    corr=df[corrcols].corr()
    corr.to_csv(output/'correlations.csv')
    df[corrcols].notna().astype(int).T.dot(df[corrcols].notna().astype(int)).to_csv(output/'correlation_pair_counts.csv')
    # Same definition and same rows, independently implemented in SQL and Pandas.
    with sqlite3.connect(processed/'jobs.db') as conn:
        sql_counts,sql_seconds,sql_peak=measure(lambda:pd.read_sql_query((ROOT/'sql/01_skill_demand.sql').read_text(),conn))
    def pandas_counts():
        s=df.skills.fillna('').str.split('|').explode()
        return s[s!=''].value_counts().sort_index()
    pc,pd_seconds,pd_peak=measure(pandas_counts)
    sc=sql_counts.set_index('skill').jobs.sort_index()
    pd.testing.assert_series_equal(pc,sc,check_names=False,check_dtype=False)
    pd.DataFrame([dict(method='SQL',seconds=sql_seconds,python_peak_bytes=sql_peak),dict(method='Pandas',seconds=pd_seconds,python_peak_bytes=pd_peak)]).to_csv(output/'sql_pandas_benchmark.csv',index=False)
    benchmark_storage(df,processed).to_csv(output/'storage_benchmark.csv',index=False)
    daily=observed_run(df.posted_date)
    daily.rename('jobs').to_csv(output/'daily_observed_run.csv')
    summary={'rows':len(df),'source_bytes':audit['source_bytes'],'salary_known':len(salary),
        'salary_coverage_pct':100*len(salary)/len(df),'median_salary_usd':float(salary.median()) if len(salary) else None,
        'iqr_low':float(low) if len(salary) else None,'iqr_high':float(high) if len(salary) else None,'iqr_outliers':int(outlier.sum()),
        'date_min':str(df.posted_date.dropna().min()),'date_max':str(df.posted_date.dropna().max()),
        'observed_run_days':len(daily),'observed_run_start':str(daily.index.min().date()) if len(daily) else None,
        'observed_run_end':str(daily.index.max().date()) if len(daily) else None,
        'sql_pandas_equal':True,'skills_coverage_pct':float(100*(df.skills.fillna('')!='').mean()),
        'top_skills':queries['01_skill_demand'].head(10).to_dict('records')}
    if len(daily)>=21:
        predictions,metrics=forecast_backtest(daily,holdout=7)
        predictions.to_csv(output/'forecast_predictions.csv',index=False)
        metrics.to_csv(output/'forecast_metrics.csv',index=False)
        summary['forecast_status']='evaluated'; summary['forecast_metrics']=metrics.to_dict('records')
    else:
        summary['forecast_status']='insufficient contiguous coverage (need 21 days)'
        for name in ['forecast_predictions.csv','forecast_metrics.csv']:
            (output/name).unlink(missing_ok=True)
    plt.rcParams.update({'figure.figsize':(10,5),'axes.spines.top':False,'axes.spines.right':False,'font.size':11})
    def save(name):
        plt.tight_layout(); plt.savefig(figures/name,dpi=150,bbox_inches='tight'); plt.close()
    top=queries['01_skill_demand'].head(15).iloc[::-1]
    plt.figure(); plt.barh(top.skill,top.jobs,color='#168b87'); plt.xlabel('Postings mentioning skill'); plt.title('Skill mentions in the captured sample'); save('01_skills.png')
    plt.figure(); positive=salary[salary>0]; plt.hist(np.log10(positive),bins=45,color='#168b87')
    plt.xlabel('log10(Annualized USD salary)'); plt.ylabel('Postings'); plt.title('Salary distribution — all valid values retained'); save('02_salary.png')
    groups=[(name,g.salary_usd.dropna()) for name,g in df.groupby('role') if g.salary_usd.notna().sum()>=5]
    plt.figure()
    if groups:
        plt.boxplot([g for _,g in groups],tick_labels=[n for n,_ in groups],orientation='horizontal',showfliers=False)
        plt.xscale('log')
    plt.xlabel('Annualized USD salary (log scale)'); plt.title('Salary by role — outlier markers hidden, not removed'); save('03_roles.png')
    plt.figure(); plt.imshow(corr,vmin=-1,vmax=1,cmap='BrBG'); plt.colorbar(label='Pearson r')
    plt.xticks(range(len(corr)),corr.columns,rotation=25,ha='right'); plt.yticks(range(len(corr)),corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)): plt.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center')
    plt.title('Pairwise correlations; see pair counts CSV'); save('04_correlations.png')
    plt.figure(); plt.plot(daily.index,daily,label='Captured postings',color='#168b87')
    plt.plot(daily.index,daily.rolling(7,min_periods=7).mean(),label='Trailing 7-day mean',color='#d88635')
    plt.legend(); plt.ylabel('Postings'); plt.xticks(rotation=25); plt.title('Longest consecutive observed-date run'); save('05_timeline.png')
    if len(daily)>=14:
        decomposition=seasonal_decompose(daily,model='additive',period=7,extrapolate_trend=0)
        pd.DataFrame({'observed':daily,'trend':decomposition.trend,'seasonal':decomposition.seasonal,'residual':decomposition.resid}).to_csv(output/'decomposition.csv')
        fig=decomposition.plot(); fig.set_size_inches(10,8); save('06_decomposition.png')
        summary['decomposition_status']='weekly period=7; exploratory capture pattern, not proven market seasonality'
    else:
        summary['decomposition_status']='insufficient consecutive days (need 14)'
        (output/'decomposition.csv').unlink(missing_ok=True)
        (figures/'06_decomposition.png').unlink(missing_ok=True)
    interactive=px.bar(queries['04_skill_rank_by_role'],x='jobs',y='skill',color='role',facet_col='role',facet_col_wrap=2,title='Top skills within each rule-based role group')
    interactive.update_yaxes(matches=None)
    interactive.write_html(figures/'07_interactive_skills.html',include_plotlyjs=True)
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    return summary
