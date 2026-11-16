# Job Market Skills Analytics Implementation Plan

> Execute with superpowers:executing-plans, task by task.

**Goal:** Deliver the complete topic-14 project and publish a new GitHub repository.
**Architecture:** Chunked ingestion into SQLite and Parquet; Python analytics; Streamlit interface; generated submission documents.
**Tech Stack:** Python 3.12, Pandas, SQLite, PyArrow, Plotly, Streamlit, statsmodels.
**Spec:** docs/design.md

## Global constraints
- Actual LinkedIn dataset; source provenance and size recorded.
- At least eight SQL queries, EDA, weekly decomposition, rolling means and three forecast methods.
- No fabricated research results; no zero-filling unknown capture gaps.
- Keep credentials and large input data outside Git.

## Review focus
- Mixed/missing currencies must not enter USD comparisons.
- Duplicate IDs across chunks must not multiply skills.
- Missing dates must not be interpreted as zero demand.
- Forecasts must never access future observations.
- Empty filtered data must show a useful message.

## Tasks
1. Data pipeline: tests for salary, skill boundaries, duplicate IDs and missing columns; implement skills.py, ingest.py, schema.sql and downloader.py. Run pytest and ingest actual CSV. Commit.
2. Analytics: tests for temporal leakage and SQL/Pandas parity; implement analytics.py and 10 SQL queries. Export measured results and charts. Run full pipeline. Commit.
3. Interface and submission: implement CLI and app.py; validate Streamlit filter/error states. Generate report.pdf and presentation.pptx from actual output, document sources and requirements matrix. Commit.
4. Final review, clean-environment smoke checks, create repository and push; verify remote files and GitHub CI.
