"""Light mutations on the in-memory seed bundle."""
from __future__ import annotations

import json

from src.analytics.db import _BUNDLE, _JSON_DIR, ensure_seeded


def append_coach_note(player_id: str, text: str) -> dict:
    """Attach a free-text coach note to the player's most recent log (by session date)."""
    ensure_seeded()
    assert _BUNDLE is not None and _JSON_DIR is not None
    session_dates = {s["session_id"]: s["date"] for s in _BUNDLE["sessions"]}
    player_logs = [l for l in _BUNDLE["logs"] if l["player_id"] == player_id]
    if not player_logs:
        return {"ok": False, "error": "no_logs"}
    player_logs.sort(key=lambda l: session_dates.get(l["session_id"], ""), reverse=True)
    target = player_logs[0]
    prev = target.get("notes") or ""
    target["notes"] = (prev + " | " + text).strip(" |") if prev else text
    (_JSON_DIR / "logs.json").write_text(json.dumps(_BUNDLE["logs"]), encoding="utf-8")
    return {"ok": True, "log_id": target["log_id"], "notes": target["notes"]}
