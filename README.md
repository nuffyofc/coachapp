# Coach Training Desk

Microsoft × Premier League **Inside the Game** hackathon MVP — a soccer-coach training-session monitor.

Squad board, skill graphs, pitch positions, and per-session performance logs (stamina, power, shooting, finishing, passing, dribbling), with grounded explanations and Adaptive Cards 1.6.

**Stack:** Python 3.12 · FastAPI · DuckDB · Adaptive Cards · Bicep · Azure Container Apps (`azd`)

**Live (Azure):** https://ca-api-coachdesk.redsea-49f9f8f0.westus2.azurecontainerapps.io/

**Repo:** https://github.com/nuffyofc/coachapp

---

## What it does

| View | Purpose |
|------|---------|
| **Squad board** | Skill radar, form distribution, filterable player cards |
| **Session logs** | Session picker, pitch map (105×68), metrics table, good/mixed/poor verdicts |
| **Player focus** | Trend chart, six skill chips, session history, coach notes |

**5-stage pipeline:** Ingest → Interpret (DuckDB) → Explain (local templates; Foundry when endpoint set) → Render → Personalize (`coach` \| `fan`)

---

## Prerequisites

- Python **3.12** (3.14 often fails DuckDB/pydantic wheels)
- Optional for cloud: Azure CLI, Azure Developer CLI (`azd`), Docker Desktop

---

## Setup & run locally

```powershell
cd coachapp   # or your clone path
copy .env.example .env   # optional — offline mode works with empty values

& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn src.web.app:app --reload --port 8080
```

Open http://127.0.0.1:8080

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Key routes: `/healthz`, `/readyz`, `/api/players`, `/api/sessions`, `/api/metrics`, `/api/player/{id}`, `/api/session/{id}`, `/api/notes`, `/api/chat`

---

## Deploy to Azure (`azd`)

Keyless: User-Assigned Managed Identity — no API keys in the repo.

```powershell
az login
azd auth login
az bicep build --file infra/main.bicep

azd env new coachdesk          # first time only
azd env set AZURE_LOCATION westus2
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>

# Foundry/OpenAI is off by default (needs model access on the subscription)
# Set deployFoundry true in infra/main.parameters.json when ready.

azd up                         # provision + build image + deploy
# later updates:
azd deploy --no-prompt
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for verify steps and common issues.

---

## Repo layout

```
src/ingest/     synthetic squad + sessions + logs
src/analytics/  DuckDB metrics + form flags
src/agent/      grounded explain (local / Foundry stub)
src/web/        FastAPI + static dashboard + Adaptive Cards
infra/          Bicep + azd parameters
azure.yaml      azd service definition
Dockerfile      ACA image
tests/          pytest
docs/           deployment notes
```

---

## Security

- No secrets in Git — use `.env` locally (gitignored) and managed identity in Azure
- Copy from `.env.example` only; never commit `.env` or `.azure/`
