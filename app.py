"""Run: streamlit run app.py"""
from pathlib import Path
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from jobmarket.dashboard import filtered_jobs,skill_counts
from jobmarket.analytics import observed_run

st.set_page_config(page_title='SkillScope · Job Market Analytics',page_icon='📊',layout='wide')
st.markdown('''<style>
.block-container{padding-top:4rem;max-width:1400px}
[data-testid="stMetric"]{background:#edf5f4;border:1px solid #dce9e7;border-radius:12px;padding:18px}
h1{letter-spacing:-1.4px} .eyebrow{color:#168b87;letter-spacing:3px;font-size:12px;font-weight:700}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="eyebrow">LABOUR MARKET RESEARCH / 2023–2024</div>',unsafe_allow_html=True)
st.title('SkillScope')
st.write('Какие навыки встречаются в вакансиях — и как различаются зарплаты?')
base=Path(os.environ.get('JOBMARKET_DATA_DIR','data/processed'))
db=base/'jobs.db'
if not db.exists():
    st.info('Подготовьте демо: `python -m jobmarket demo`, затем запустите `JOBMARKET_DATA_DIR=data/demo streamlit run app.py`. Команды для Windows и полного набора — в README.')
    st.stop()
with sqlite3.connect(db) as conn:
    years=pd.read_sql_query("SELECT DISTINCT substr(posted_date,1,4) AS year FROM jobs WHERE posted_date IS NOT NULL ORDER BY year",conn).year.tolist()
    locations=pd.read_sql_query('SELECT name FROM locations ORDER BY name',conn).name.tolist()
    roles=pd.read_sql_query('SELECT name FROM roles ORDER BY name',conn).name.tolist()
st.sidebar.title('Срез рынка')
year=st.sidebar.multiselect('Год',years)
location=st.sidebar.multiselect('Локация',locations)
role=st.sidebar.multiselect('Группа ролей',roles)
st.sidebar.caption('Пустой фильтр = все значения. Локация — исходная строка LinkedIn, не стандартизованный регион.')
st.sidebar.divider()
st.sidebar.caption('Источник: arshkon / LinkedIn Job Postings · Kaggle · CC BY-SA 4.0')
st.sidebar.warning('Историческая выборка сбора вакансий. Не оценка всего рынка и не текущие вакансии.')
df=filtered_jobs(db,year,location,role)
if df.empty:
    st.info('Нет вакансий для выбранного сочетания. Измените фильтры.')
    st.stop()
skills=skill_counts(db,df.job_id)
known=df.salary_usd.dropna()
a,b,c,d=st.columns(4)
a.metric('Вакансии',f'{len(df):,}')
b.metric('Медиана USD / год',f'${known.median():,.0f}' if len(known) else 'Нет данных')
c.metric('Зарплата известна',f'{100*len(known)/len(df):.1f}%')
d.metric('Локации',f'{df.location.nunique():,}')
st.caption('Зарплаты: только USD с известным периодом. Почасовая оплата × 2 080; месячная × 12. remote = отметка источника, отсутствие отметки не означает офис.')
tabs=st.tabs(['Обзор','Навыки','Зарплаты','Динамика','Данные'])
with tabs[0]:
    l,r=st.columns(2)
    with l:
        st.subheader('Востребованность навыков')
        st.plotly_chart(px.bar(skills.head(12).iloc[::-1],x='jobs',y='skill',color_discrete_sequence=['#168b87'],labels={'jobs':'Вакансии','skill':''}),use_container_width=True)
    with r:
        st.subheader('Структура ролей')
        rc=df.role.value_counts().rename_axis('role').reset_index(name='jobs')
        st.plotly_chart(px.bar(rc,x='jobs',y='role',color_discrete_sequence=['#d88635'],labels={'jobs':'Вакансии','role':''}),use_container_width=True)
with tabs[1]:
    st.subheader('Упоминания навыков в описаниях')
    st.caption('Словарь из 30 навыков; один навык учитывается один раз на вакансию. Упоминание не доказывает обязательность требования.')
    skills['Доля вакансий, %']=(100*skills.jobs/len(df)).round(2)
    st.dataframe(skills,use_container_width=True,hide_index=True)
with tabs[2]:
    if known.empty:
        st.info('В этом срезе нет сопоставимых зарплат в USD.')
    else:
        st.plotly_chart(px.histogram(df.dropna(subset=['salary_usd']),x='salary_usd',nbins=60,color_discrete_sequence=['#168b87'],labels={'salary_usd':'Годовая зарплата, USD'},title='Распределение: выбросы сохранены'),use_container_width=True)
        st.plotly_chart(px.box(df.dropna(subset=['salary_usd']),x='role',y='salary_usd',log_y=True,points=False,labels={'role':'Роль','salary_usd':'USD / год'},title='Сравнение групп ролей'),use_container_width=True)
with tabs[3]:
    run=observed_run(df.posted_date)
    st.info('Показан самый длинный непрерывный отрезок с наблюдениями. Дни без записей считаются неизвестным покрытием, а не нулевым спросом.')
    if len(run):
        timeline=pd.DataFrame({'Вакансии':run,'Среднее за 7 дней':run.rolling(7).mean()})
        st.plotly_chart(px.line(timeline,labels={'value':'Вакансии','index':'Дата'},color_discrete_sequence=['#168b87','#d88635']),use_container_width=True)
    else:
        st.info('В выбранном срезе нет корректных дат.')
with tabs[4]:
    st.dataframe(df[['job_id','title','company','location','role','salary_usd','posted_date']].head(500),use_container_width=True,hide_index=True)
    st.caption('Показаны первые 500 строк; экспорт содержит весь выбранный срез.')
    # Protect spreadsheet applications when opening untrusted source strings.
    export=df.copy()
    for col in export.select_dtypes('object'):
        export[col]=export[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(('=','+','-','@')) else x)
    st.download_button('Скачать срез CSV',export.to_csv(index=False).encode('utf-8-sig'),'jobs_filtered.csv','text/csv')
