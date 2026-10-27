"""DuckDB connection over synthetic training tables (in-memory via JSON)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import duckdb

from src.ingest.seed import seed_all

_BUNDLE: dict[str, list[dict]] | None = None
_JSON_DIR: Path | None = None


def ensure_seeded() -> dict[str, list[dict]]:
    global _BUNDLE, _JSON_DIR
    if _BUNDLE is None:
        _BUNDLE = seed_all()
        _JSON_DIR = Path(tempfile.mkdtemp(prefix="coachdesk_"))
        for name, rows in _BUNDLE.items():
            (_JSON_DIR / f"{name}.json").write_text(
                json.dumps(rows), encoding="utf-8"
            )
    return _BUNDLE


def reset_seed(seed: int = 42) -> dict[str, list[dict]]:
    global _BUNDLE, _JSON_DIR
    _BUNDLE = None
    _JSON_DIR = None
    # force re-seed with explicit seed
    bundle = seed_all(seed)
    _BUNDLE = bundle
    _JSON_DIR = Path(tempfile.mkdtemp(prefix="coachdesk_"))
    for name, rows in bundle.items():
        (_JSON_DIR / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")
    return bundle


def get_connection() -> duckdb.DuckDBPyConnection:
    ensure_seeded()
    assert _JSON_DIR is not None
    con = duckdb.connect(database=":memory:")
    for name in ("players", "sessions", "logs"):
        path = str(_JSON_DIR / f"{name}.json").replace("\\", "/")
        con.execute(
            f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_json_auto('{path}')"
        )
    return con


def query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    con = get_connection()
    try:
        rel = con.execute(sql, params) if params else con.execute(sql)
        cols = [d[0] for d in rel.description]
        return [dict(zip(cols, row)) for row in rel.fetchall()]
    finally:
        con.close()
