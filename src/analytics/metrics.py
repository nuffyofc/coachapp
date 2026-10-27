"""Stage 2 — Interpret. Deterministic training metrics via DuckDB."""
from __future__ import annotations

from typing import Any

from src.analytics.db import ensure_seeded, get_connection, query
from src.ingest.seed import ANCHOR_DATE

STAT_KEYS = ("stamina", "power", "shooting", "finishing", "passing", "dribbling")


def _fetch_dicts(con, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    rel = con.execute(sql, params) if params else con.execute(sql)
    cols = [d[0] for d in rel.description]
    return [dict(zip(cols, row)) for row in rel.fetchall()]


def compute_facts(query_id: str = "squad") -> dict[str, Any]:
    if query_id.startswith("player:"):
        return player_summary(query_id.split(":", 1)[1])
    if query_id.startswith("session:"):
        return session_summary(query_id.split(":", 1)[1])
    return squad_overview()


def squad_overview() -> dict[str, Any]:
    ensure_seeded()
    con = get_connection()
    try:
        players = _fetch_dicts(
            con,
            """
            SELECT
              p.player_id,
              p.name,
              p.position,
              p.jersey,
              ROUND(AVG(l.overall), 1) AS avg_overall,
              ROUND(AVG(l.stamina), 1) AS stamina,
              ROUND(AVG(l.power), 1) AS power,
              ROUND(AVG(l.shooting), 1) AS shooting,
              ROUND(AVG(l.finishing), 1) AS finishing,
              ROUND(AVG(l.passing), 1) AS passing,
              ROUND(AVG(l.dribbling), 1) AS dribbling,
              COUNT(*) AS sessions_logged,
              SUM(CASE WHEN l.verdict = 'good' THEN 1 ELSE 0 END) AS good_count,
              SUM(CASE WHEN l.verdict = 'poor' THEN 1 ELSE 0 END) AS poor_count
            FROM players p
            JOIN logs l ON l.player_id = p.player_id
            GROUP BY p.player_id, p.name, p.position, p.jersey
            ORDER BY avg_overall DESC
            """,
        )
        for pl in players:
            pl["form_flag"] = _form_flag(
                float(pl["avg_overall"]), int(pl["poor_count"]), int(pl["sessions_logged"])
            )
        sess = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        return {
            "query_id": "squad",
            "anchor_date": ANCHOR_DATE.isoformat(),
            "session_count": int(sess),
            "player_count": len(players),
            "players": players,
            "squad_avg_overall": round(
                sum(float(p["avg_overall"]) for p in players) / max(len(players), 1), 1
            ),
            "form_flag": _form_flag(
                sum(float(p["avg_overall"]) for p in players) / max(len(players), 1),
                sum(int(p["poor_count"]) for p in players),
                sum(int(p["sessions_logged"]) for p in players),
            ),
        }
    finally:
        con.close()


def player_summary(player_id: str) -> dict[str, Any]:
    ensure_seeded()
    con = get_connection()
    try:
        info = con.execute(
            "SELECT player_id, name, position, jersey FROM players WHERE player_id = ?",
            [player_id],
        ).fetchone()
        if not info:
            return {"query_id": f"player:{player_id}", "error": "not_found"}
        avg = con.execute(
            """
            SELECT
              ROUND(AVG(overall), 1),
              ROUND(AVG(stamina), 1),
              ROUND(AVG(power), 1),
              ROUND(AVG(shooting), 1),
              ROUND(AVG(finishing), 1),
              ROUND(AVG(passing), 1),
              ROUND(AVG(dribbling), 1),
              COUNT(*),
              SUM(CASE WHEN verdict = 'good' THEN 1 ELSE 0 END),
              SUM(CASE WHEN verdict = 'poor' THEN 1 ELSE 0 END)
            FROM logs WHERE player_id = ?
            """,
            [player_id],
        ).fetchone()
        history = _fetch_dicts(
            con,
            """
            SELECT l.log_id, l.session_id, s.date, s.title, s.intensity,
                   l.stamina, l.power, l.shooting, l.finishing, l.passing, l.dribbling,
                   l.overall, l.verdict, l.pos_x_m, l.pos_y_m, l.distance_m, l.notes
            FROM logs l
            JOIN sessions s ON s.session_id = l.session_id
            WHERE l.player_id = ?
            ORDER BY s.date DESC
            """,
            [player_id],
        )
        trend = [
            {"date": h["date"], "overall": h["overall"], "verdict": h["verdict"]}
            for h in reversed(history)
        ]
        facts: dict[str, Any] = {
            "query_id": f"player:{player_id}",
            "player_id": info[0],
            "name": info[1],
            "position": info[2],
            "jersey": int(info[3]),
            "avg_overall": float(avg[0] or 0),
            "stamina": float(avg[1] or 0),
            "power": float(avg[2] or 0),
            "shooting": float(avg[3] or 0),
            "finishing": float(avg[4] or 0),
            "passing": float(avg[5] or 0),
            "dribbling": float(avg[6] or 0),
            "sessions_logged": int(avg[7] or 0),
            "good_count": int(avg[8] or 0),
            "poor_count": int(avg[9] or 0),
            "history": history,
            "trend": trend,
            "latest_position": (
                {"x": history[0]["pos_x_m"], "y": history[0]["pos_y_m"]}
                if history
                else None
            ),
        }
        facts["form_flag"] = _form_flag(
            facts["avg_overall"], facts["poor_count"], facts["sessions_logged"]
        )
        return facts
    finally:
        con.close()


def session_summary(session_id: str) -> dict[str, Any]:
    ensure_seeded()
    con = get_connection()
    try:
        s = con.execute(
            "SELECT session_id, date, title, intensity, duration_min FROM sessions WHERE session_id = ?",
            [session_id],
        ).fetchone()
        if not s:
            return {"query_id": f"session:{session_id}", "error": "not_found"}
        logs = _fetch_dicts(
            con,
            """
            SELECT l.log_id, l.session_id, l.player_id, l.stamina, l.power, l.shooting,
                   l.finishing, l.passing, l.dribbling, l.overall, l.verdict,
                   l.pos_x_m, l.pos_y_m, l.distance_m, l.notes,
                   p.name, p.position, p.jersey
            FROM logs l
            JOIN players p ON p.player_id = l.player_id
            WHERE l.session_id = ?
            ORDER BY l.overall DESC
            """,
            [session_id],
        )
        avg_overall = round(sum(float(x["overall"]) for x in logs) / max(len(logs), 1), 1)
        poor = sum(1 for x in logs if x["verdict"] == "poor")
        return {
            "query_id": f"session:{session_id}",
            "session_id": s[0],
            "date": s[1],
            "title": s[2],
            "intensity": int(s[3]),
            "duration_min": int(s[4]),
            "avg_overall": avg_overall,
            "form_flag": _form_flag(avg_overall, poor, len(logs)),
            "logs": logs,
            # Fixed formation board (not random GPS scatter) — jersey always present.
            "positions": _formation_positions(logs),
        }
    finally:
        con.close()


def _formation_positions(logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Place session players on a basic GK–DF–MF–FW board (pitch 105×68, attack right)."""
    # Distinct lanes left→right (GK–DF–MF–FW). Never stack two tokens on one point.
    slots = {
        "GK": [(10.0, 28.0), (10.0, 40.0)],
        "DF": [(32.0, 10.0), (32.0, 24.0), (32.0, 38.0), (32.0, 52.0)],
        "MF": [(55.0, 10.0), (55.0, 24.0), (55.0, 38.0), (55.0, 52.0)],
        "FW": [(80.0, 14.0), (80.0, 28.0), (80.0, 42.0), (80.0, 56.0)],
    }
    order = {"GK": 0, "DF": 1, "MF": 2, "FW": 3}
    grouped: dict[str, list[dict[str, Any]]] = {"GK": [], "DF": [], "MF": [], "FW": []}
    for row in logs:
        pos = str(row.get("position") or "MF").upper()
        if pos not in grouped:
            pos = "MF"
        grouped[pos].append(row)

    out: list[dict[str, Any]] = []
    for pos in ("GK", "DF", "MF", "FW"):
        band = slots[pos]
        for i, row in enumerate(sorted(grouped[pos], key=lambda r: int(r.get("jersey") or 0))):
            if i < len(band):
                x, y = band[i]
            else:
                # Overflow: nudge further up the pitch in the same line
                base_x = band[-1][0] + 4.0
                y_vals = [p[1] for p in band]
                y = y_vals[i % len(y_vals)]
                x = base_x
            out.append(
                {
                    "player_id": row["player_id"],
                    "name": row["name"],
                    "position": row.get("position"),
                    "jersey": int(row["jersey"]),
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "overall": row["overall"],
                    "verdict": row["verdict"],
                    "stamina": row.get("stamina"),
                    "power": row.get("power"),
                    "shooting": row.get("shooting"),
                    "finishing": row.get("finishing"),
                    "passing": row.get("passing"),
                    "dribbling": row.get("dribbling"),
                    "line": pos,
                    "line_order": order[pos],
                }
            )
    return out


def list_sessions() -> list[dict[str, Any]]:
    return query(
        """
        SELECT s.session_id, s.date, s.title, s.intensity, s.duration_min,
               COUNT(l.log_id) AS players_logged,
               ROUND(AVG(l.overall), 1) AS avg_overall
        FROM sessions s
        LEFT JOIN logs l ON l.session_id = s.session_id
        GROUP BY s.session_id, s.date, s.title, s.intensity, s.duration_min
        ORDER BY s.date DESC
        """
    )


def list_players() -> list[dict[str, Any]]:
    return query(
        "SELECT player_id, name, position, jersey FROM players ORDER BY jersey"
    )


def squad_stat_averages() -> dict[str, float]:
    rows = query(
        """
        SELECT
          ROUND(AVG(stamina), 1) AS stamina,
          ROUND(AVG(power), 1) AS power,
          ROUND(AVG(shooting), 1) AS shooting,
          ROUND(AVG(finishing), 1) AS finishing,
          ROUND(AVG(passing), 1) AS passing,
          ROUND(AVG(dribbling), 1) AS dribbling
        FROM logs
        """
    )
    row = rows[0]
    return {k: float(row[k]) for k in STAT_KEYS}


def _form_flag(avg_overall: float, poor_count: int, sessions: int) -> str:
    poor_rate = poor_count / sessions if sessions else 0
    if avg_overall >= 70 and poor_rate < 0.25:
        return "green"
    if avg_overall >= 55 and poor_rate < 0.45:
        return "yellow"
    return "red"
