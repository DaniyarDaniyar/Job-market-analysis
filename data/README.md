# Data provenance

- Author: Arsh Kon and dataset contributors.
- Dataset: **LinkedIn Job Postings (2023–2024)**, version 13.
- Canonical source: https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
- License: [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- Accessed during this project: 2026-11-09.
- `postings.csv`: 516,843,769 uncompressed bytes (>200 MB requirement).
- Source SHA-256 and exact input/clean row counts: `reports/audit.json`.
- `sample/postings.csv`: first 1,000 real records in original file order, provided
  under CC BY-SA 4.0 with this attribution. A startup fixture, **not** a random or
  representative research sample. No synthetic vacancies or row multiplication.
- Full raw CSV, ZIP, SQLite and Parquet are excluded from Git due to their size.
  `python -m jobmarket download` retrieves pinned version 13 without needing
  credentials when Kaggle permits public download. If unavailable, download
  manually from the source and put `postings.csv` in `data/raw/linkedin/`.
- Dataset license also applies to derived data tables included here. Code is
  original project code; see root LICENSE.

This is historical, opportunistically collected vacancy data. Geographic,
occupational and date coverage are uneven. Salary is optional and missingness is
not random. A vacancy can mention skills that are optional or not required.
Source captures are not a representative probability sample of any labour market.
