# Job Market Skills Analytics — design

Topic 14, Cluster 2, Programming for Data Analysis and Database.
Source specification: https://docs.google.com/document/d/1zRCV-QfaxMzQfb93VNtoRfnA_t4KakCdV05Bhc34bWg/mobilebasic

Build a reproducible Python research project using the actual arshkon/linkedin-job-postings Kaggle dataset. Use Python 3.11–3.12, Pandas, SQLite, Parquet, Streamlit, Plotly and statsmodels. These are implementation choices made for the task. No hosted service required.

Alternatives: a notebook alone is simple but less reusable; a separate web API adds unnecessary deployment work. A modular CLI pipeline plus Streamlit meets the required interactive interface and remains easy to demonstrate.

Pipeline: stream CSV in chunks of 10,000, validate IDs, normalize annual USD salary with explicit assumptions, extract a bounded English skill vocabulary, store 3NF dimensions and many-to-many skills in SQLite, write Parquet. Keep first occurrence of a job ID across chunks. Missing salary stays missing; reject nonpositive and reversed ranges. Keep IQR outliers for analysis. Do not mix currencies.

Research: missingness, descriptive stats, IQR, salary distributions, skill demand by role/location, correlations. Daily resampling must preserve unknown capture gaps; decomposition and forecasting use a documented contiguous observed-date run. Compare naive baseline, trailing mean and linear trend using rolling-origin holdout, MAE, timing and Python allocation peaks. Never label this convenience sample representative or current.

Deliverables: Python code, pinned dependencies, small real input sample, source URL and downloader, normalized schema/ER diagram, 10+ SQL queries and CSV outputs, five charts including interactive HTML, Russian report in Markdown/PDF, PPTX slides, README, tests and GitHub CI. Big raw/processed files excluded from Git; full analysis reproducible locally.

Verification: salary units/currency, skill token boundaries, duplicates across chunks, foreign keys, SQL/Pandas equality, temporal leakage, missing dates, empty dashboard filters, full real-data run and Streamlit smoke test.
