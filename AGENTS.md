# Agent Guidelines

## Project
- School timetable generator, single-user, local app
- Backend: FastAPI + SQLAlchemy + SQLite + OR-Tools CP-SAT solver
- Frontend: React 19 + TypeScript + Vite + React Query
- Package manager: `uv` (backend), `npm` (frontend) — add backend deps with `uv add PACKAGE_NAME`

## Running
- Backend: `uv run squola` → `http://localhost:8000` (API docs at `/docs`)
- Frontend: `cd frontend && npm run dev` → `http://localhost:5173`

## Source layout
- `src/squola/` — backend package
  - `main.py` — FastAPI app + CORS + router wiring
  - `models.py` — SQLAlchemy ORM models
  - `schemas.py` — Pydantic DTOs
  - `database.py` — DB session + init
  - `scheduler.py` — OR-Tools CP-SAT scheduling logic
  - `routers/` — one file per resource (teachers, classes, matters, scheduling)
- `frontend/src/` — React SPA
- `alembic/` — DB migrations (use Alembic to add/change schema, don't edit the DB directly)

## Docs & specs
- `specs/` — product specs (source of truth for domain rules and requirements). Read these before implementing features.
- `docs/` — technical documentation for agents and developers. Keep it up to date when making significant changes. Create new files here when adding major features or modules.

## Tests
- `tests/` — backend tests only (pytest + httpx)
- Run with: `uv run pytest tests/`
- Write tests for all new backend endpoints and scheduler logic
