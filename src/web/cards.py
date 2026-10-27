"""Stage 4 — Adaptive Cards 1.6 for coach insights."""
from __future__ import annotations

from typing import Any


def build_card(facts: dict[str, Any], explanation: dict[str, Any], persona: str = "coach") -> dict:
    flag = explanation.get("form_flag") or facts.get("form_flag", "yellow")
    color = {"green": "Good", "yellow": "Warning", "red": "Attention"}[flag]
    title = facts.get("name") or facts.get("title") or "Squad overview"
    body: list[dict] = [
        {
            "type": "TextBlock",
            "text": str(title),
            "weight": "Bolder",
            "size": "Medium",
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": color,
                            "color": {
                                "green": "Good",
                                "yellow": "Warning",
                                "red": "Attention",
                            }[flag],
                            "weight": "Bolder",
                        }
                    ],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": explanation.get("text", ""),
                            "wrap": True,
                        }
                    ],
                },
            ],
        },
    ]
    if persona == "coach" and "stamina" in facts:
        body.append(
            {
                "type": "FactSet",
                "facts": [
                    {"title": k.title(), "value": str(facts.get(k))}
                    for k in (
                        "stamina",
                        "power",
                        "shooting",
                        "finishing",
                        "passing",
                        "dribbling",
                        "avg_overall",
                    )
                    if k in facts
                ],
            }
        )
    return {
        "type": "AdaptiveCard",
        "version": "1.6",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": body,
    }
