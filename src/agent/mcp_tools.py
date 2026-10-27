"""MCP-style tool bindings over DuckDB metrics."""
from __future__ import annotations

from typing import Any

from src.analytics import metrics


def run_metrics_tool(query_id: str) -> dict[str, Any]:
    return metrics.compute_facts(query_id)


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "run_metrics",
            "description": "Compute deterministic training metrics (squad, player:ID, session:ID).",
            "parameters": {"query_id": "string"},
        }
    ]
