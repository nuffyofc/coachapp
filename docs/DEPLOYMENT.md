# Deployment — Coach Training Desk

## Prerequisites

| Tool | Notes |
|------|--------|
| Azure CLI | `az login` (subscription with Container Apps + Cognitive Services) |
| Azure Developer CLI | `azd` 1.10+ |
| Docker Desktop | Running Linux engine |
| Python 3.12 | Local venv / tests |

## Local (offline)

```powershell
cd C:\Users\mike\Desktop\hackaton-next-2
.\.venv\Scripts\python.exe -m uvicorn src.web.app:app --reload --port 8080
.\.venv\Scripts\python.exe -m pytest -q
```

## One-command cloud deploy

```powershell
cd C:\Users\mike\Desktop\hackaton-next-2
az bicep build --file infra/main.bicep
azd auth login   # if needed
azd env new coachdesk
azd env set AZURE_LOCATION westus2
azd up
```

`azd up` provisions Bicep (RG, UAMI, Log Analytics, ACR, ACA, Foundry), builds the Dockerfile, pushes to ACR, and updates the Container App.

Keyless only: User-Assigned Managed Identity — no secrets in Git.

## Live (coachdesk env)

- **URL:** https://ca-api-coachdesk.redsea-49f9f8f0.westus2.azurecontainerapps.io/
- **RG:** `rg-coachdesk` (westus2)
- Foundry skipped by default (`deployFoundry: false`) until the subscription has OpenAI model access.

## Verify

```powershell
curl.exe https://ca-api-coachdesk.redsea-49f9f8f0.westus2.azurecontainerapps.io/healthz
curl.exe https://ca-api-coachdesk.redsea-49f9f8f0.westus2.azurecontainerapps.io/readyz
curl.exe https://ca-api-coachdesk.redsea-49f9f8f0.westus2.azurecontainerapps.io/api/players
```

## Common issues

| Issue | Fix |
|-------|-----|
| Docker daemon not running | Start Docker Desktop, wait until `docker info` works |
| Foundry / AIServices quota | Retry after raising quota, or temporarily remove Foundry module |
| Wrong subscription | `az account set --subscription <id>` then `azd env set AZURE_SUBSCRIPTION_ID <id>` |
