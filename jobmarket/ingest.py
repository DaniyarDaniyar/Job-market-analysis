"""Chunked CSV → validated SQLite and compact Parquet, with audit metadata."""
from pathlib import Path
import hashlib
import json
import math
import sqlite3
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from .skills import extract_skills, classify_role

ROOT = Path(__file__).resolve().parents[1]
FACTORS = {'HOURLY':2080, 'DAILY':260, 'WEEKLY':52, 'BIWEEKLY':26, 'MONTHLY':12, 'YEARLY':1}

def number(value):
    try:
        value=float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None

def annual_salary(row: dict):
    if str(row.get('currency','')).upper() != 'USD':
        return None
    factor=FACTORS.get(str(row.get('pay_period','')).upper())
    if factor is None:
        return None
    low, high, med = (number(row.get(k)) for k in ('min_salary','max_salary','med_salary'))
    if any(v is not None and v<=0 for v in (low,high,med)) or (low is not None and high is not None and low>high):
        return None
    if med is not None:
        value=med
    elif low is not None and high is not None:
        value=(low+high)/2
    else:
        value=low if low is not None else high
    return value*factor if value is not None else None

def posted_date(row):
    value=number(row.get('original_listed_time')) or number(row.get('listed_time'))
    if value is None:
        return None
    date=pd.to_datetime(value,unit='ms',errors='coerce',utc=True)
    return None if pd.isna(date) else date.strftime('%Y-%m-%d')

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def build_database(csv_path, output_dir, chunksize=10000):
    csv_path, output_dir = Path(csv_path), Path(output_dir)
    if chunksize<1:
        raise ValueError('chunksize must be positive')
    columns=pd.read_csv(csv_path,nrows=0).columns
    required={'job_id','title','description','location'}
    if not required.issubset(columns):
        raise ValueError('Missing required columns: '+', '.join(sorted(required-set(columns))))
    output_dir.mkdir(parents=True,exist_ok=True)
    db=output_dir/'jobs.building.db'
    db.unlink(missing_ok=True)
    conn=sqlite3.connect(db)
    conn.executescript((ROOT/'sql/schema.sql').read_text())
    dimensions={t:{} for t in ('companies','locations','roles','skills')}
    def dim(table,name,source_key=None):
        key=source_key or name
        if key not in dimensions[table]:
            idx=len(dimensions[table])+1
            if table=='companies':
                conn.execute('INSERT INTO companies VALUES (?,?,?)',(idx,key,name))
            else:
                conn.execute(f'INSERT INTO {table} VALUES (?,?)',(idx,name))
            dimensions[table][key]=idx
        return dimensions[table][key]
    audit={'input_rows':0,'rows':0,'duplicates':0,'invalid_ids':0,'invalid_dates':0,
           'missing':{},'input_dtypes':{},'chunk_memory_before_bytes':0,'chunk_memory_after_bytes':0,
           'source_bytes':csv_path.stat().st_size,'source_sha256':sha256_file(csv_path),
           'chunksize':chunksize,'salary_assumptions':FACTORS,
           'source_url':'https://www.kaggle.com/datasets/arshkon/linkedin-job-postings'}
    seen=set(); start=time.perf_counter(); writer=None
    schema=pa.schema([('job_id',pa.int64()),('title',pa.string()),('company',pa.string()),
        ('location',pa.string()),('role',pa.string()),('posted_date',pa.string()),
        ('salary_usd',pa.float64()),('experience',pa.string()),('work_type',pa.string()),
        ('remote',pa.int64()),('views',pa.float64()),('applies',pa.float64()),
        ('description_length',pa.int64()),('skills',pa.string())])
    try:
        for chunk in pd.read_csv(csv_path,chunksize=chunksize):
            audit['input_rows']+=len(chunk)
            audit['input_dtypes']={c:str(t) for c,t in chunk.dtypes.items()}
            for col,count in chunk.isna().sum().items():
                audit['missing'][col]=audit['missing'].get(col,0)+int(count)
            audit['chunk_memory_before_bytes']+=int(chunk.memory_usage(deep=True).sum())
            for col in ['pay_period','currency','formatted_work_type','formatted_experience_level','location']:
                if col in chunk:
                    chunk[col]=chunk[col].astype('category')
            for col in ['views','applies']:
                if col in chunk:
                    chunk[col]=pd.to_numeric(chunk[col],errors='coerce',downcast='float')
            audit['chunk_memory_after_bytes']+=int(chunk.memory_usage(deep=True).sum())
            rows=[]
            for row in chunk.astype(object).where(pd.notna(chunk),None).to_dict('records'):
                raw_id=number(row.get('job_id'))
                if raw_id is None or raw_id<=0 or not raw_id.is_integer():
                    audit['invalid_ids']+=1; continue
                jid=int(raw_id)
                if jid in seen:
                    audit['duplicates']+=1; continue
                seen.add(jid)
                title=str(row.get('title') or 'Unknown')
                company=str(row.get('company_name') or 'Unknown')
                source_id=number(row.get('company_id'))
                key=f'id:{int(source_id)}' if source_id else f'name:{company}'
                location=str(row.get('location') or 'Unknown')
                role=classify_role(title)
                description=str(row.get('description') or '')
                skills=extract_skills(description)
                date=posted_date(row)
                audit['invalid_dates']+=int(date is None)
                salary=annual_salary(row)
                exp=str(row.get('formatted_experience_level') or 'Unknown')
                work=str(row.get('formatted_work_type') or 'Unknown')
                remote=int(number(row.get('remote_allowed'))==1)
                views,applies=number(row.get('views')),number(row.get('applies'))
                conn.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (jid,title,dim('companies',company,key),dim('locations',location),dim('roles',role),
                     date,salary,exp,work,remote,views,applies,len(description)))
                conn.executemany('INSERT INTO job_skills VALUES (?,?)',[(jid,dim('skills',s)) for s in skills])
                rows.append(dict(job_id=jid,title=title,company=company,location=location,role=role,
                    posted_date=date,salary_usd=salary,experience=exp,work_type=work,remote=remote,
                    views=views,applies=applies,description_length=len(description),skills='|'.join(skills)))
            if writer is None:
                writer=pq.ParquetWriter(output_dir/'jobs.building.parquet',schema,compression='zstd')
            writer.write_table(pa.Table.from_pylist(rows,schema=schema))
            conn.commit(); audit['rows']+=len(rows)
        if writer is None:
            pq.write_table(pa.Table.from_pylist([],schema=schema),output_dir/'jobs.building.parquet')
        audit['elapsed_seconds']=time.perf_counter()-start
        if conn.execute('pragma foreign_key_check').fetchall():
            raise ValueError('Foreign key validation failed')
    finally:
        if writer: writer.close()
        conn.close()
    db.replace(output_dir/'jobs.db')
    (output_dir/'jobs.building.parquet').replace(output_dir/'jobs.parquet')
    (output_dir/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    return audit
