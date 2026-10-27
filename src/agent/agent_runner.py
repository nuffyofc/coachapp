"""Stage 3 — Explain. Local grounded templates; Foundry when endpoint set."""
from __future__ import annotations

import os
from typing import Any


def explain(facts: dict[str, Any], persona: str = "coach") -> dict[str, Any]:
    if facts.get("error"):
        return {"text": "No data for that selection.", "source": "local", "facts_used": []}
    if os.getenv("AZURE_AI_PROJECT_ENDPOINT"):
        try:
            return _explain_with_foundry(facts, persona=persona)
        except Exception:
            pass
    return _explain_local(facts, persona=persona)


def _explain_local(facts: dict[str, Any], persona: str) -> dict[str, Any]:
    qid = facts.get("query_id", "squad")
    flag = facts.get("form_flag", "yellow")
    label = {"green": "in good form", "yellow": "mixed form", "red": "needs attention"}[flag]

    if qid == "squad":
        avg = facts.get("squad_avg_overall", 0)
        n = facts.get("player_count", 0)
        text = (
            f"Squad training form is {label}: average overall {avg} across {n} players "
            f"over {facts.get('session_count', 0)} sessions."
        )
        used = ["squad_avg_overall", "player_count", "session_count", "form_flag"]
    elif qid.startswith("player:"):
        name = facts.get("name", "Player")
        text = (
            f"{name} is {label} — overall {facts.get('avg_overall')} across "
            f"{facts.get('sessions_logged')} sessions "
            f"({facts.get('good_count')} strong, {facts.get('poor_count')} weak)."
        )
        if persona == "coach":
            text += (
                f" Focus stats: passing {facts.get('passing')}, "
                f"stamina {facts.get('stamina')}, finishing {facts.get('finishing')}."
            )
        used = ["avg_overall", "sessions_logged", "good_count", "poor_count", "form_flag"]
    elif qid.startswith("session:"):
        text = (
            f"{facts.get('title')} on {facts.get('date')} finished {label} "
            f"(session average {facts.get('avg_overall')}, intensity {facts.get('intensity')}/5)."
        )
        used = ["avg_overall", "intensity", "form_flag", "title", "date"]
    else:
        text = "Training snapshot ready."
        used = []

    return {"text": text, "source": "local", "facts_used": used, "form_flag": flag}


def _explain_with_foundry(facts: dict[str, Any], persona: str) -> dict[str, Any]:
    raise NotImplementedError("Wire Foundry Agent after offline path is demo-ready")
