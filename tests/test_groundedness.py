"""Groundedness: explain text must only use numbers present in facts."""
from src.agent.agent_runner import explain
from src.analytics.db import reset_seed
from src.analytics.metrics import player_summary, squad_overview


def setup_function():
    reset_seed(42)


def test_player_explain_mentions_counts_from_facts():
    squad = squad_overview()
    pid = squad["players"][0]["player_id"]
    facts = player_summary(pid)
    out = explain(facts, persona="coach")
    assert str(facts["sessions_logged"]) in out["text"]
    assert str(facts["good_count"]) in out["text"]
    assert facts["name"] in out["text"]


def test_card_builds():
    from src.web.cards import build_card

    facts = squad_overview()
    exp = explain(facts)
    card = build_card(facts, exp, persona="coach")
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.6"
