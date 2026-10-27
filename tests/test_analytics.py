"""Deterministic metric checks against seeded training data."""
from src.analytics.db import reset_seed
from src.analytics.metrics import (
    compute_facts,
    player_summary,
    session_summary,
    squad_overview,
    squad_stat_averages,
)


def setup_function():
    reset_seed(42)


def test_squad_has_players_and_form_flags():
    squad = squad_overview()
    assert squad["player_count"] >= 10
    assert squad["session_count"] >= 1
    flags = {p["form_flag"] for p in squad["players"]}
    assert flags & {"green", "yellow", "red"}
    assert 1 <= squad["squad_avg_overall"] <= 99


def test_player_metrics_include_six_skills():
    squad = squad_overview()
    pid = squad["players"][0]["player_id"]
    facts = player_summary(pid)
    for key in ("stamina", "power", "shooting", "finishing", "passing", "dribbling"):
        assert key in facts
        assert 1 <= facts[key] <= 99
    assert facts["history"]
    assert facts["trend"]


def test_session_logs_and_positions():
    from src.analytics.metrics import list_sessions

    sessions = list_sessions()
    assert sessions
    sid = sessions[0]["session_id"]
    facts = session_summary(sid)
    assert facts["logs"]
    assert facts["positions"]
    assert "pos_x_m" in facts["logs"][0] or "overall" in facts["logs"][0]
    assert all("jersey" in row for row in facts["logs"])
    assert all(p.get("jersey") is not None for p in facts["positions"])
    assert all(p.get("line") in ("GK", "DF", "MF", "FW") for p in facts["positions"])
    # Formation board: players share discrete X lanes, not random scatter
    xs = {round(float(p["x"]), 1) for p in facts["positions"]}
    assert len(xs) <= 8


def test_compute_facts_routes():
    assert compute_facts("squad")["query_id"] == "squad"
    av = squad_stat_averages()
    assert set(av) == {"stamina", "power", "shooting", "finishing", "passing", "dribbling"}


def test_explain_grounded_in_facts():
    from src.agent.agent_runner import explain

    facts = squad_overview()
    out = explain(facts, persona="coach")
    assert str(facts["squad_avg_overall"]) in out["text"]
    assert out["source"] == "local"
