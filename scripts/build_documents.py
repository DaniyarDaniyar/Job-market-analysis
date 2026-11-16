"""Build Russian report PDF/Markdown and PPTX from measured full-run artifacts."""
from pathlib import Path
import json
import html
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import cm
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports'

def build():
    summary=json.loads((OUT/'summary.json').read_text())
    audit=json.loads((OUT/'audit.json').read_text())
    metrics=pd.read_csv(OUT/'forecast_metrics.csv') if (OUT/'forecast_metrics.csv').exists() else pd.DataFrame()
    storage=pd.read_csv(OUT/'storage_benchmark.csv').groupby('format').agg({'bytes':'first','seconds':'median','python_peak_bytes':'median'})
    parity=pd.read_csv(OUT/'sql_pandas_benchmark.csv')
    skills=pd.read_csv(OUT/'sql/01_skill_demand.csv')
    missing=pd.read_csv(OUT/'missingness.csv')
    toptext='; '.join(f'{r.skill}: {r.jobs:,} ({r.pct_jobs:.1f}%)' for r in skills.head(5).itertuples())
    memory=100*(1-audit['chunk_memory_after_bytes']/audit['chunk_memory_before_bytes'])
    methods='; '.join(f'{r.method}: MAE {r.mae:,.2f}' for r in metrics.itertuples())
    best=metrics.sort_values('mae').iloc[0]['method'] if len(metrics) else 'не оценивался'
    sections=[
        ('1. Цель и исследовательские вопросы',
         'Тема №14 — Job Market Skills Analytics, Cluster 2. Цель — исследовать упоминания навыков, распределения зарплат и состав ролей по локациям на исторических вакансиях LinkedIn. Вопросы: какие навыки чаще упоминаются; как различаются зарплаты между группами; какие закономерности видны во времени; насколько простые методы предсказывают число собранных вакансий?'),
        ('2. Источник, объём и воспроизводимость',
         f'Использован LinkedIn Job Postings (2023–2024), автор arshkon, Kaggle, версия 13, лицензия CC BY-SA 4.0. Исходный postings.csv: {audit["source_bytes"]:,} байт, {audit["input_rows"]:,} строк. После обработки: {summary["rows"]:,} вакансий. Рекомендация задания выполнена по объёму >200 МБ, а не искусственным увеличением числа строк. Источник: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings. SHA-256 записан в audit.json. В репозитории есть реальный пример из первых 1 000 записей и скрипт полной загрузки.'),
        ('3. Очистка и качество данных',
         f'CSV читается чанками по {audit["chunksize"]:,} строк. Дубликатов ID: {audit["duplicates"]}; некорректных ID: {audit["invalid_ids"]}; отсутствующих или неразбираемых дат: {audit["invalid_dates"]}. Для повторного ID сохраняется первая строка, в том числе между чанками. Пропуски не заполняются средними значениями. Известных сопоставимых зарплат: {summary["salary_known"]:,} ({summary["salary_coverage_pct"]:.2f}%). Полная таблица пропусков и типов признаков включена в артефакты.'),
        ('4. Нормализация зарплат и ограничения',
         f'Сравниваются только USD с известным pay_period. Приоритет: med_salary, затем середина min/max, затем единственная известная граница. Неположительные значения и обратные диапазоны исключены из зарплатного анализа. Коэффициенты годового пересчёта: час 2 080, день 260, неделя 52, две недели 26, месяц 12, год 1. Это допущения о полной занятости, а не фактическом доходе. Медиана: ${summary["median_salary_usd"]:,.0f}/год. По правилу IQR найдено {summary["iqr_outliers"]:,} выбросов; они сохранены, поскольку высокая зарплата сама по себе не ошибка.'),
        ('5. Извлечение навыков и группировка ролей',
         f'Использован прозрачный английский словарь из 30 навыков: нормализованные названия, алиасы и регулярные выражения с границами токенов. Повторные упоминания в вакансии считаются один раз. Покрытие словаря: {summary["skills_coverage_pct"]:.2f}% вакансий. Лидеры: {toptext}. Роли определяются упорядоченными правилами по заголовку, неоднозначные заголовки могут классифицироваться ошибочно. Словарь не извлекает все возможные профессии и навыки. Размеченного gold standard нет: метрики качества NLP не заявляются.'),
        ('6. База данных и SQL',
         'SQLite содержит шесть таблиц: companies, locations, roles, jobs, skills, job_skills. Схема разделяет справочники и факты, связь вакансий с навыками — многие ко многим. Первичные и внешние ключи проверяются после загрузки. ER-диаграмма: docs/schema.md. Реализованы 10 SQL-запросов с JOIN, GROUP BY/HAVING, CTE, DENSE_RANK, ROW_NUMBER, оконным средним и подзапросом и предагрегированными средними. Все результаты загружены в Pandas и сохранены в reports/sql.'),
        ('7. EDA, визуализации и интерпретация',
         'Построены частоты навыков, гистограмма логарифма зарплаты, boxplot зарплаты по ролям, тепловая карта корреляций, временной ряд со скользящим средним, недельная декомпозиция и интерактивный HTML Plotly. Корреляции рассчитываются попарно; число доступных наблюдений для каждой пары приведено отдельно. Связи не доказывают причинность. Сравнения зарплат по навыкам могут отражать состав профессий, географию и отбор вакансий с опубликованной зарплатой.'),
        ('8. Покрытие времени и декомпозиция',
         f'Диапазон исходных дат: {summary["date_min"]} — {summary["date_max"]}. Поле даты — original_listed_time, при отсутствии listed_time; UTC. Отсутствие записей за день не трактуется как нулевой спрос. Для эксперимента выбран самый длинный непрерывный отрезок наблюдений: {summary["observed_run_start"]} — {summary["observed_run_end"]}, {summary["observed_run_days"]} дней. Дневной resample, trailing mean за 7 дней, additive decomposition с периодом 7. Это исследование режима сбора; рыночная сезонность не доказана. Декомпозиция описательная и не используется для прогнозирования.'),
        ('9. Сравнение методов и baseline',
         f'Сравниваются naive (последнее значение, baseline), moving_average (среднее предыдущих 7 дней) и linear_trend (линейный тренд на предыдущих 14 днях с ограничением прогноза снизу нулём). Последние 7 дней — holdout. На каждом шаге доступны только прошлые значения; после наблюдения факта окно обновляется. Окна выбраны заранее. Метрики: MAE, время, пик Python-аллокаций tracemalloc. {methods}. Минимальный MAE на этом holdout: {best}. Один короткий holdout не доказывает устойчивое преимущество; для выбора модели в эксплуатации нужна отдельная временная валидация.'),
        ('10. Производительность и проверка совпадения',
         f'Оптимизация category/downcast сократила сумму deep-memory размеров входных чанков на {memory:.2f}%. Это не пиковый RSS процесса; оригинальные текстовые описания занимают большую часть памяти. CSV и Parquet сравниваются на одной очищенной витрине, по три последовательных чтения, отчёт содержит медиану времени. Кэш ОС не сбрасывается, результаты зависят от машины. SQL и Pandas независимо рассчитали частоты навыков; полное совпадение проверено assert_series_equal. tracemalloc не измеряет весь объём нативных буферов библиотек.'),
        ('11. Выводы и ограничения',
         f'В данной выборке наиболее частое упоминание — {skills.iloc[0]["skill"]}; сопоставимые зарплаты опубликованы для {summary["salary_coverage_pct"]:.1f}% вакансий. Это обосновывает анализ покрытия вместе с зарплатными показателями. Метод {best} получил наименьшую ошибку в коротком эксперименте, но прогнозирует число собранных объявлений, а не занятость. Данные 2023–2024 гг. не отражают текущий рынок. Дополнительные ограничения: неполный словарь, отсутствие ручной оценки извлечения, эвристические роли, неслучайные пропуски, необработанная география и неодинаковое покрытие дат.'),
        ('12. Запуск и подготовка к защите',
         'Инструкции приведены в README.md. Полный цикл: python -m jobmarket download; python -m jobmarket ingest; python -m jobmarket analyze; python scripts/build_documents.py; streamlit run app.py. Тесты: python -m pytest -q. Участник и группа должны быть проверены перед сдачей; утверждение темы преподавателем и загрузка в Moodle выполняются отдельно. Проект подготовлен с помощью AI-ассистента; перед защитой необходимо самостоятельно проверить код, результаты и требования университета к раскрытию такого использования.')
    ]
    md=['# Job Market Skills Analytics','', 'Итоговый проект · Programming for Data Analysis and Database','',
        'Автор: Kylyshbekov Daniyar. Группа: указать перед сдачей.','']
    for title,text in sections:md += ['## '+title,'',text,'']
    md += ['## Метрики прогноза','',metrics.to_csv(index=False),'','## Сравнение хранения','',storage.to_csv(),
           '','## Источники','',
           '- Требования курса: https://docs.google.com/document/d/1zRCV-QfaxMzQfb93VNtoRfnA_t4KakCdV05Bhc34bWg/mobilebasic',
           '- Dataset: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings',
           '- Pandas: https://pandas.pydata.org/docs/',
           '- SQLite: https://www.sqlite.org/windowfunctions.html',
           '- statsmodels: https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.seasonal_decompose.html']
    (OUT/'report.md').write_text('\n'.join(md),encoding='utf-8')
    # Matplotlib bundles DejaVu Sans, so Cyrillic PDF fonts are portable.
    import matplotlib
    fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    pdfmetrics.registerFont(TTFont('DejaVu',str(fonts/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVuBold',str(fonts/'DejaVuSans-Bold.ttf')))
    styles=getSampleStyleSheet()
    for name in ['Normal','Title','Heading1','Heading2']:
        styles[name].fontName='DejaVuBold' if name!='Normal' else 'DejaVu'
    styles['Normal'].fontSize=9; styles['Normal'].leading=14
    styles['Heading2'].fontSize=13; styles['Heading2'].leading=17
    story=[Paragraph('Job Market Skills Analytics',styles['Title']),Spacer(1,.5*cm),
           Paragraph('Итоговый проект · Тема 14 · Cluster 2',styles['Heading2']),
           Paragraph('Kylyshbekov Daniyar<br/>Группа: указать перед сдачей',styles['Normal']),Spacer(1,.5*cm)]
    def table(data):
        values=[[Paragraph(html.escape(str(c)),styles['Normal']) for c in row] for row in data]
        t=Table(values,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0efec')),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.extend([t,Spacer(1,.4*cm)])
    for i,(title,text) in enumerate(sections):
        story.extend([Paragraph(title,styles['Heading2']),Paragraph(html.escape(text),styles['Normal']),Spacer(1,.3*cm)])
        if i==2: table([['Поле','Пропусков, %']]+[[r.column,f'{r.pct:.1f}'] for r in missing.head(7).itertuples()])
        if i==4: story.append(Image(str(OUT/'figures/01_skills.png'),width=16*cm,height=8*cm))
        if i==6:
            for name in ['02_salary.png','03_roles.png','04_correlations.png']:
                story.append(Image(str(OUT/'figures'/name),width=16*cm,height=8*cm))
        if i==7:
            story.append(Image(str(OUT/'figures/05_timeline.png'),width=16*cm,height=8*cm))
            if (OUT/'figures/06_decomposition.png').exists():story.append(Image(str(OUT/'figures/06_decomposition.png'),width=16*cm,height=12*cm))
        if i==8 and len(metrics):table([['Метод','MAE','Время, мс','Python peak, КБ']]+[[r.method,f'{r.mae:.2f}',f'{r.seconds*1000:.2f}',f'{r.python_peak_bytes/1024:.1f}'] for r in metrics.itertuples()])
        if i==9:table([['Формат','Размер, МБ','Медиана чтения, с']]+[[idx,f'{r.bytes/1e6:.2f}',f'{r.seconds:.4f}'] for idx,r in storage.iterrows()])
    def footer(canvas,doc):
        canvas.setFont('DejaVu',8);canvas.drawString(2*cm,1*cm,'Job Market Skills Analytics · historical LinkedIn sample');canvas.drawRightString(19*cm,1*cm,str(doc.page))
    SimpleDocTemplate(str(OUT/'report.pdf'),title='Job Market Skills Analytics',author='Kylyshbekov Daniyar',rightMargin=2*cm,leftMargin=2*cm,topMargin=1.7*cm,bottomMargin=1.7*cm).build(story,onFirstPage=footer,onLaterPages=footer)
    prs=Presentation(); prs.slide_width=Inches(13.333);prs.slide_height=Inches(7.5)
    def slide(title,lines,image=None):
        s=prs.slides.add_slide(prs.slide_layouts[6])
        bg=s.background.fill;bg.solid();bg.fore_color.rgb=RGBColor.from_string('F6F8F8')
        def box(x,y,w,h,text,size,color='172E3B',bold=False):
            tf=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame;tf.word_wrap=True
            for i,line in enumerate(text.split('\n')):
                p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.size=Pt(size);p.font.name='DejaVu Sans';p.font.bold=bold;p.font.color.rgb=RGBColor.from_string(color);p.space_after=Pt(16)
        box(.6,.3,12,.35,'SKILLSCOPE / JOB MARKET RESEARCH',11,'168B87',True)
        box(.6,.9,12,1.1,title,29,bold=True)
        box(.6,2.0,5.0 if image else 11.8,4.7,'\n'.join(lines),19 if image else 23)
        if image:s.shapes.add_picture(str(OUT/'figures'/image),Inches(5.9),Inches(2.1),width=Inches(6.8))
        box(.6,7.05,12,.3,f'Topic 14 · LinkedIn 2023–2024 · CC BY-SA 4.0                                  {len(prs.slides):02}',10,'657E87')
    slide('Job Market Skills Analytics',['Итоговый проект по Python, анализу данных и базам данных','Kylyshbekov Daniyar','Группа: указать перед сдачей'])
    slide('Исследовательские вопросы',['Какие навыки чаще упоминаются?','Как различаются зарплаты и группы ролей?','Что можно узнать из временной динамики собранных вакансий?'])
    slide('Реальные данные, воспроизводимый запуск',[f'{summary["rows"]:,} вакансий · {audit["source_bytes"]/1e6:.1f} МБ CSV','Kaggle / arshkon · версия 13','Чанки → SQLite + Parquet → SQL/EDA → Streamlit','Исходники, тесты, отчёт и слайды — в GitHub'])
    slide('Качество и зарплаты',[f'Зарплата известна: {summary["salary_coverage_pct"]:.1f}%',f'Медиана: ${summary["median_salary_usd"]:,.0f}/год','Только USD; почасовая × 2 080',f'IQR-выбросы сохранены: {summary["iqr_outliers"]:,}'],'02_salary.png')
    slide('Какие навыки встречаются чаще',[f'{r.skill}: {r.pct_jobs:.1f}%' for r in skills.head(4).itertuples()]+['Упоминание ≠ обязательное требование'],'01_skills.png')
    slide('Архитектура и SQL',['companies / locations / roles → jobs','jobs ↔ job_skills ↔ skills','6 таблиц, ключи и проверка связности','10 запросов: JOIN, HAVING, CTE, ранги, подзапросы','SQL и Pandas: результаты совпадают'])
    slide('Зарплаты по группам ролей',['Группировка заголовков правилами','Зарплаты пропущены неслучайно','Различия не доказывают причинность','Boxplot: маркеры выбросов скрыты'],'03_roles.png')
    slide('Покрытие времени важнее красивого тренда',[f'Непрерывный отрезок: {summary["observed_run_days"]} дней',f'{summary["observed_run_start"]} — {summary["observed_run_end"]}','Пропуски сбора не заполняются нулями','Недельная декомпозиция — описательная'],'05_timeline.png')
    slide('Baseline и два метода',[f'{r.method}: MAE {r.mae:,.1f}' for r in metrics.itertuples()]+['7 дней holdout; прогноз на один день вперёд','Каждый прогноз использует только прошлые значения','Короткий эксперимент не гарантирует устойчивость'])
    slide('Память и хранение',[f'Category/downcast: −{memory:.2f}% deep-memory чанков']+[f'{idx}: {r.bytes/1e6:.2f} МБ, чтение {r.seconds:.4f} с' for idx,r in storage.iterrows()]+['Одинаковая очищенная витрина; 3 повтора','tracemalloc не равен пиковому RSS'])
    slide('Выводы и демонстрация',['Историческая выборка, не весь рынок труда','Словарь навыков и группы ролей имеют ограничения','Демо: фильтры → навыки → зарплаты → экспорт','Далее: ручная оценка извлечения, расширение дат и географии'])
    slide('Источники и воспроизводимость',['Kaggle: arshkon/linkedin-job-postings, v13, CC BY-SA 4.0','Pandas · SQLite · statsmodels · Plotly · Streamlit','README: полный запуск, demo, тесты, соответствие заданию','Подготовлено с помощью AI; проверить и освоить перед защитой'])
    prs.core_properties.author='Kylyshbekov Daniyar'
    prs.core_properties.title='Job Market Skills Analytics'
    prs.save(OUT/'presentation.pptx')
    print(f'Created report.md, report.pdf and presentation.pptx ({len(prs.slides)} slides)')

if __name__=='__main__':build()
