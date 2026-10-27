# Data

Raw datasets are **never** committed to Git.

- Put generated Parquet/JSON under this folder locally (gitignored).
- `sample/` may hold tiny fixture snippets for offline validation once a domain is chosen.
- Ingest entry point: `src/ingest/loader.py` (stub — not implemented).
