# Architecture — Coach Training Desk

```
Browser dashboard (static/index.html)
  │  menus: Squad · Sessions · Player
  ▼
FastAPI (src/web/app.py)
  ├─ Ingest      src/ingest/seed.py     synthetic players/sessions/logs
  ├─ Interpret   src/analytics/metrics.py  DuckDB → overall + 6 skills + form_flag
  ├─ Explain     src/agent/agent_runner.py local template (Foundry later)
  ├─ Render      Adaptive Card JSON + visual dashboard graphs
  └─ Personalize persona=coach|fan (detail density)
```

Form flag: green / yellow / red from average overall + poor-session rate.
Positioning: last drill coordinates on a 105×68m pitch per session log.
