"""Stage 1 — Ingest.

Synthetic squad, training sessions, per-player skill samples, pitch positions,
and session verdict logs. Deterministic seed so demos stay reproducible.
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

ANCHOR_DATE = date(2026, 10, 27)
SQUAD_SIZE = 14
SKILLS = ["stamina", "power", "shooting", "finishing", "passing", "dribbling"]
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _players(rng: random.Random) -> list[dict]:
    first = [
        "Amir", "Ben", "Carlos", "Diego", "Eli", "Finn", "Gio", "Hugo",
        "Ivan", "Jae", "Kai", "Leo", "Mateo", "Noah",
    ]
    last = [
        "Okoro", "Silva", "Nguyen", "Berg", "Sato", "Costa", "Ibrahim",
        "Petrov", "Walsh", "Kim", "Rossi", "Anders", "Mbeki", "Quinn",
    ]
    positions = ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "MF", "FW", "FW", "FW", "DF", "MF"]
    players = []
    for i in range(SQUAD_SIZE):
        baseline = {s: rng.randint(48, 88) for s in SKILLS}
        if positions[i] == "GK":
            baseline["shooting"] = rng.randint(20, 40)
            baseline["finishing"] = rng.randint(15, 35)
        players.append({
            "player_id": f"PLR_{i + 1:02d}",
            "name": f"{first[i]} {last[i]}",
            "position": positions[i],
            "number": i + 1,
            **{f"base_{k}": v for k, v in baseline.items()},
        })
    return players


def _sessions(rng: random.Random) -> list[dict]:
    titles = [
        "Technical circuit",
        "Possession rondo",
        "Finishing station",
        "Pressing shape",
        "Conditioning blocks",
        "Small-sided 5v5",
        "Set-piece walkthrough",
    ]
    sessions = []
    idx = 0
    for day in range(-18, 0):
        if rng.random() < 0.55:
            idx += 1
            sessions.append({
                "session_id": f"SES_{idx:03d}",
                "date": (ANCHOR_DATE + timedelta(days=day)).isoformat(),
                "title": rng.choice(titles),
                "intensity": rng.randint(2, 5),
                "minutes": rng.choice([60, 75, 90]),
            })
    return sessions


def _session_logs(players: list[dict], sessions: list[dict], rng: random.Random) -> list[dict]:
    """One row per player per session: skills, pitch position, overall verdict."""
    rows = []
    for s in sessions:
        for p in players:
            # Skip ~8% absences
            if rng.random() < 0.08:
                continue
            skills = {}
            for skill in SKILLS:
                base = p[f"base_{skill}"]
                jitter = rng.randint(-12, 10)
                # High intensity drains stamina/power a bit
                if skill in ("stamina", "power") and s["intensity"] >= 4:
                    jitter -= rng.randint(3, 8)
                skills[skill] = max(15, min(99, base + jitter))
            overall = round(sum(skills.values()) / len(skills), 1)
            if overall >= 72:
                verdict = "good"
                flag = "green"
            elif overall >= 55:
                verdict = "mixed"
                flag = "yellow"
            else:
                verdict = "poor"
                flag = "red"
            # Pitch coords: 105x68 synthetic pitch, role-biased
            role = p["position"]
            if role == "GK":
                x, y = rng.uniform(5, 18), rng.uniform(20, 48)
            elif role == "DF":
                x, y = rng.uniform(18, 45), rng.uniform(8, 60)
            elif role == "MF":
                x, y = rng.uniform(40, 70), rng.uniform(12, 56)
            else:
                x, y = rng.uniform(65, 95), rng.uniform(10, 58)
            rows.append({
                "log_id": f"{s['session_id']}_{p['player_id']}",
                "session_id": s["session_id"],
                "player_id": p["player_id"],
                "date": s["date"],
                "title": s["title"],
                "intensity": s["intensity"],
                "minutes_played": s["minutes"] - rng.randint(0, 15),
                **skills,
                "overall": overall,
                "verdict": verdict,
                "flag": flag,
                "pos_x": round(x, 1),
                "pos_y": round(y, 1),
            })
    return rows


def generate_all(seed: int = 42) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    players = _players(rng)
    sessions = _sessions(rng)
    logs = _session_logs(players, sessions, rng)
    return {"players": players, "sessions": sessions, "logs": logs}


def load_and_write_parquet(
    source: Path | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Write synthetic tables as JSON sidecars + Parquet via DuckDB when available.

    Always writes JSON under data/ for offline inspection; Parquet when duckdb works.
    """
    out = Path(output_dir) if output_dir else DATA_DIR
    out.mkdir(parents=True, exist_ok=True)
    payload = generate_all()
    for name, rows in payload.items():
        (out / f"{name}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    try:
        import duckdb

        con = duckdb.connect()
        for name, rows in payload.items():
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_json_auto(?)", [str(out / f"{name}.json")])
            con.execute(f"COPY {name} TO ? (FORMAT PARQUET)", [str(out / f"{name}.parquet")])
        con.close()
    except Exception:
        # JSON alone is enough for the analytics layer fallback
        pass

    return out


if __name__ == "__main__":
    path = load_and_write_parquet()
    print(f"Seeded synthetic data under {path}")
