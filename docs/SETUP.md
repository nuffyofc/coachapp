# Local setup

1. Python **3.12** venv (3.14 often fails to build duckdb/pydantic-core wheels).
2. `pip install -r requirements.txt`
3. Copy `.env.example` → `.env` (leave Azure vars empty for offline stubs).
4. Fill domain stubs, then `.\demo\scripts\demo.ps1 local`
