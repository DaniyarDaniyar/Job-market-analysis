# Матрица соответствия заданию

Источник: [Final project requirements](https://docs.google.com/document/d/1zRCV-QfaxMzQfb93VNtoRfnA_t4KakCdV05Bhc34bWg/mobilebasic).

| Требование | Реализация / доказательство |
|---|---|
| Python 3.x, версии библиотек | requirements.txt, requirements-lock.txt |
| 5+ функций, list/dict, if/elif/else, циклы | jobmarket/ingest.py, skills.py, analytics.py, __main__.py |
| Файлы и обработка ошибок | CSV/JSON/Parquet, downloader.py, CLI try/except |
| Интерактивный интерфейс | app.py: фильтры года/локации/роли; CLI menu |
| Модульность и стандартная библиотека | jobmarket/, pathlib/json/sqlite3/datetime через Pandas |
| Большой датасет | 516 843 769 байт исходного CSV; reports/audit.json |
| Чанки, категории, downcast, Parquet | ingest.py, измерение до/после в audit.json |
| SQLite и ER-диаграмма | sql/schema.sql, docs/schema.md; 6 таблиц |
| 8+ SQL-запросов | sql/01…10; JOIN/HAVING/CTE/подзапросы/окна |
| Результаты SQL в Pandas | analytics.run_queries; reports/sql/*.csv |
| Сравнение SQL и Pandas | assert_series_equal; sql_pandas_benchmark.csv |
| EDA: статистика, пропуски, типы, IQR | descriptive_statistics.csv, missingness.csv, audit.json, summary.json |
| Временные ряды, resample, среднее, декомпозиция | analytics.py; daily_observed_run.csv, decomposition.csv |
| Корреляции и heatmap | correlations.csv, correlation_pair_counts.csv, figures/04_correlations.png |
| 4–5 визуализаций, Plotly | figures/01…07 и интерактивные графики в app.py |
| Baseline и два подхода | naive + moving_average + linear_trend, forecast_metrics.csv |
| MAE, время, память | forecast_metrics.csv, storage_benchmark.csv; ограничения измерения в отчёте |
| Извлечение навыков и зарплатные распределения | skills.py, figures/01…03 |
| Исходники, данные или ссылка, README | репозиторий, data/README.md, downloader.py |
| Письменный отчёт и презентация | reports/report.pdf, report.md, presentation.pptx |
| Проверки и воспроизводимость | tests/, GitHub Actions, README |

Административные действия, которые код не выполняет: утверждение темы,
проверка авторства и группы, загрузка материалов в Moodle, личная защита.
Метрики извлечения навыков не заявляются без ручной разметки.
