"""Coach Training Desk — FastAPI wiring Ingest→Interpret→Explain→Render→Personalize."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agent.agent_runner import explain
from src.analytics import metrics, store
from src.analytics.db import ensure_seeded
from src.web.cards import build_card

app = FastAPI(title="Coach Training Desk")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class NoteIn(BaseModel):
    player_id: str
    text: str


class ChatIn(BaseModel):
    message: str
    persona: str = "coach"
    query_id: str = "squad"


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    ensure_seeded()
    metrics.squad_overview()
    return {"status": "ready"}


@app.get("/api/players")
def api_players():
    ensure_seeded()
    return metrics.list_players()


@app.get("/api/sessions")
def api_sessions():
    ensure_seeded()
    return metrics.list_sessions()


@app.get("/api/stats/averages")
def api_stat_averages():
    ensure_seeded()
    return metrics.squad_stat_averages()


@app.get("/api/metrics")
def api_metrics(
    query_id: str = Query("squad"),
    persona: str = Query("coach"),
):
    ensure_seeded()
    facts = metrics.compute_facts(query_id)
    explanation = explain(facts, persona=persona)
    return {
        "facts": facts,
        "explanation": explanation,
        "card": build_card(facts, explanation, persona=persona),
    }


@app.get("/api/player/{player_id}")
def api_player(player_id: str, persona: str = Query("coach")):
    return api_metrics(query_id=f"player:{player_id}", persona=persona)


@app.get("/api/session/{session_id}")
def api_session(session_id: str, persona: str = Query("coach")):
    return api_metrics(query_id=f"session:{session_id}", persona=persona)


@app.post("/api/notes")
def api_notes(body: NoteIn):
    ensure_seeded()
    return store.append_coach_note(body.player_id, body.text)


@app.post("/api/chat")
def api_chat(body: ChatIn):
    """Explain + Adaptive Card for a query_id inferred from message or explicit field."""
    ensure_seeded()
    qid = body.query_id
    msg = body.message.lower()
    if "player:" in msg:
        qid = msg.strip()
    facts = metrics.compute_facts(qid)
    explanation = explain(facts, persona=body.persona)
    return {
        "facts": facts,
        "explanation": explanation,
        "card": build_card(facts, explanation, persona=body.persona),
    }
