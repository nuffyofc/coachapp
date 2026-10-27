"""Synthetic squad + training sessions + per-player performance logs.

Deterministic seeds so metrics/tests stay reproducible. Anchor date is the
demo's "today" (not wall-clock).
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ANCHOR_DATE = date(2026, 10, 27)
SQUAD_SIZE = 14
SESSION_HISTORY_DAYS = 18

FIRST_NAMES = [
    "Marco", "Luis", "Omar", "Kai", "Noah", "Eli", "Sam", "Leo",
    "Jonas", "Ravi", "Theo", "Andre", "Chris", "Mateo",
]
LAST_NAMES = [
    "Silva", "Park", "Hassan", "Novak", "Reed", "Costa", "Kim", "Berg",
    "Diaz", "Nguyen", "Walsh", "Okoro", "Petrov", "Almeida",
]
SESSION_TITLES = [
    "Technical drills",
    "Small-sided games",
    "Fitness block",
    "Finishing practice",
    "Passing patterns",
    "Press & recover",
]


def generate_players(seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    players = []
    for i in range(1, SQUAD_SIZE + 1):
        if i <= 2:
            pos = "GK"
        elif i <= 6:
            pos = "DF"
        elif i <= 10:
            pos = "MF"
        else:
            pos = "FW"
        # Baseline skill bands 45–85 so session deltas create spread
        base = {
            "stamina": rng.randint(55, 85),
            "power": rng.randint(50, 82),
            "shooting": rng.randint(40, 80) if pos != "GK" else rng.randint(20, 40),
            "finishing": rng.randint(40, 82) if pos in ("FW", "MF") else rng.randint(30, 60),
            "passing": rng.randint(55, 88),
            "dribbling": rng.randint(45, 85) if pos != "GK" else rng.randint(25, 45),
        }
        players.append({
            "player_id": f"PLR_{i:02d}",
            "name": f"{FIRST_NAMES[i - 1]} {LAST_NAMES[i - 1]}",
            "position": pos,
            "jersey": i,
            **{f"base_{k}": v for k, v in base.items()},
        })
    return players


def generate_sessions(seed: int = 11) -> list[dict]:
    rng = random.Random(seed)
    sessions = []
    idx = 0
    for day in range(-SESSION_HISTORY_DAYS, 0):
        if rng.random() < 0.55:
            idx += 1
            sessions.append({
                "session_id": f"SES_{idx:03d}",
                "date": (ANCHOR_DATE + timedelta(days=day)).isoformat(),
                "title": rng.choice(SESSION_TITLES),
                "intensity": rng.randint(2, 5),
                "duration_min": rng.choice([60, 75, 90]),
            })
    return sessions


def _clamp(n: int, lo: int = 1, hi: int = 99) -> int:
    return max(lo, min(hi, n))


def generate_session_logs(
    players: list[dict],
    sessions: list[dict],
    seed: int = 19,
) -> list[dict]:
    """One performance log per player per session (present players only)."""
    rng = random.Random(seed)
    # Pin a couple of weak/strong tendencies so red/green always appear
    bias = {}
    for i, p in enumerate(players):
        if i < 2:
            bias[p["player_id"]] = -18
        elif i >= SQUAD_SIZE - 2:
            bias[p["player_id"]] = 12
        else:
            bias[p["player_id"]] = rng.randint(-8, 8)

    logs = []
    for s in sessions:
        for p in players:
            # ~12% absence
            if rng.random() < 0.12:
                continue
            b = bias[p["player_id"]]
            intensity = s["intensity"]
            fatigue = intensity * rng.randint(1, 3)
            stamina = _clamp(p["base_stamina"] + b - fatigue + rng.randint(-5, 5))
            power = _clamp(p["base_power"] + b + rng.randint(-6, 6))
            shooting = _clamp(p["base_shooting"] + b + rng.randint(-7, 7))
            finishing = _clamp(p["base_finishing"] + b + rng.randint(-7, 7))
            passing = _clamp(p["base_passing"] + b + rng.randint(-5, 5))
            dribbling = _clamp(p["base_dribbling"] + b + rng.randint(-6, 6))
            overall = round(
                (stamina + power + shooting + finishing + passing + dribbling) / 6, 1
            )
            # Pitch position during drills (0–105 x, 0–68 y) — last known zone
            x_m = round(rng.uniform(8, 97), 1)
            y_m = round(rng.uniform(5, 63), 1)
            if overall >= 72:
                verdict = "good"
            elif overall >= 55:
                verdict = "mixed"
            else:
                verdict = "poor"
            logs.append({
                "log_id": f"LOG_{s['session_id']}_{p['player_id']}",
                "session_id": s["session_id"],
                "player_id": p["player_id"],
                "stamina": stamina,
                "power": power,
                "shooting": shooting,
                "finishing": finishing,
                "passing": passing,
                "dribbling": dribbling,
                "overall": overall,
                "verdict": verdict,
                "pos_x_m": x_m,
                "pos_y_m": y_m,
                "distance_m": round(rng.uniform(3200, 7800) * (intensity / 3), 0),
                "notes": "",
            })
    return logs


def seed_all(seed: int = 42) -> dict:
    players = generate_players(seed)
    sessions = generate_sessions(seed + 1)
    logs = generate_session_logs(players, sessions, seed + 2)
    return {"players": players, "sessions": sessions, "logs": logs}


def write_parquet(bundle: dict, output_dir: Path) -> Path:
    """Write JSON sidecars (always) and Parquet when duckdb is available."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in bundle.items():
        (output_dir / f"{name}.json").write_text(
            json.dumps(rows, indent=2), encoding="utf-8"
        )
    try:
        import duckdb

        con = duckdb.connect()
        for name, rows in bundle.items():
            path = str(output_dir / f"{name}.parquet").replace("\\", "/")
            con.execute("CREATE OR REPLACE TABLE t AS SELECT * FROM rows", {"rows": rows})
            # duckdb register via python list
            con.register(f"_{name}", rows)
            con.execute(f"COPY (SELECT * FROM _{name}) TO '{path}' (FORMAT PARQUET)")
        con.close()
    except Exception:
        # JSON is enough for local demo if parquet write fails
        pass
    return output_dir
