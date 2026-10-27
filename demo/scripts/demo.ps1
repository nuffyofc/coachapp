# Usage: .\demo\scripts\demo.ps1 {local|test|check|deploy}
param([string]$Command = "local")
Set-Location (Join-Path $PSScriptRoot "..\..")

switch ($Command) {
  "local"  {
    if (-not (Test-Path .\.venv\Scripts\python.exe)) {
      Write-Host "Create a Python 3.12 venv and pip install -r requirements.txt first."
      exit 1
    }
    & .\.venv\Scripts\python.exe -m uvicorn src.web.app:app --reload --port 8080
  }
  "test"   { & .\.venv\Scripts\python.exe -m pytest -q }
  "check"  {
    az bicep build --file infra\main.bicep --stdout | Out-Null
    az bicep build --file infra\modules\identity.bicep --stdout | Out-Null
    az bicep build --file infra\modules\foundry-agent.bicep --stdout | Out-Null
    az bicep build --file infra\modules\container-apps.bicep --stdout | Out-Null
    Write-Host "bicep OK"
  }
  "deploy" { azd up }
  default  { Write-Host "usage: demo.ps1 {local|test|check|deploy}"; exit 1 }
}
