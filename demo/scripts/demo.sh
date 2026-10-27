#!/usr/bin/env bash
# Usage: ./demo/scripts/demo.sh {local|test|check|deploy}
set -euo pipefail
cd "$(dirname "$0")/../.."
CMD="${1:-local}"

case "$CMD" in
  local)
    ./.venv/bin/python -m uvicorn src.web.app:app --reload --port 8080
    ;;
  test)
    ./.venv/bin/python -m pytest -q
    ;;
  check)
    az bicep build --file infra/main.bicep --stdout >/dev/null
    az bicep build --file infra/modules/identity.bicep --stdout >/dev/null
    az bicep build --file infra/modules/foundry-agent.bicep --stdout >/dev/null
    az bicep build --file infra/modules/container-apps.bicep --stdout >/dev/null
    echo "bicep OK"
    ;;
  deploy)
    azd up
    ;;
  *)
    echo "usage: demo.sh {local|test|check|deploy}"; exit 1
    ;;
esac
