# Squola

A web app for generating school timetables with workspace-scoped multiuser support. Each account owns a workspace and can manage only its own data.

## What it does

The authenticated user inserts all workspace data (teachers with their unavailabilities and preferences, classes, subject matters with hours/week), and triggers a schedule generation. The solver finds a valid assignment of lessons to time slots respecting all constraints (no teacher in two places at once, teacher unavailabilities, subject requirements, scheduling preferences). Generated schedules are saved and can be browsed inside the same workspace.

## Architecture

Full-stack app:

- **Backend** — FastAPI app (`src/squola/`) with SQLite via SQLAlchemy. Routers for teachers, classes, matters, and scheduling. The scheduler uses Google OR-Tools CP-SAT solver to generate timetables as constraint-satisfaction problems.
- **Frontend** — React 19 + TypeScript SPA (`frontend/`) built with Vite. Uses React Query for data fetching and React Router for navigation.
- **Database** — SQLite (`squola.db`), managed with Alembic migrations.

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Solver | Google OR-Tools (CP-SAT) |
| Frontend | React 19, TypeScript, Vite, React Query |
| DB | SQLite (swap-ready via SQLAlchemy) |
| Package mgr | uv |

## Current status

| Feature | Backend | Frontend |
|---|---|---|
| Registrazione/login a cookie HTTP-only | X | X |
| Gestione account (cambio password, rename workspace, logout) | X | X |
| Isolamento dati per workspace | X | X |
| Gestione insegnanti (CRUD) | X | X |
| Indisponibilità insegnante (slot e giorni) | X | X |
| Preferenze di scheduling insegnante | X | X |
| Requisiti singole materie | X | X | 
| Gestione materie (CRUD) | X | X |
| Gestione classi (CRUD) | X | X |
| Assegnazione materia/insegnante a classe | X | X |
| Generazione orario (CP-SAT) | X | X |
| Preview pre-generazione | X | X |
| Salvataggio e browse orari generati | X | X |
| Export PDF | | |
| Ore pomeridiane per classi | | |

---

## Teacher unavailabilities

A teacher can be marked as unavailable for specific time slots — e.g., hours they spend at another school. The CP-SAT solver hard-excludes those slots when generating the timetable.

**Data model:** `TeacherUnavailability` (`teacher_unavailabilities` table) — one row per blocked slot with `day_of_week` (0–4) and `hour_slot` (1–6).

**API:** `GET/POST /teachers/{id}/unavailabilities`, `DELETE /teachers/{id}/unavailabilities/{slot_id}` — see `src/squola/routers/teachers.py`.

**UI:** `/teachers/:id` — teacher detail page with a 5×6 interactive grid. Click a cell to toggle a single slot; click a day header to block/unblock the entire day (sends one request per hour slot).

**Solver:** `ScheduleGenerator._add_teacher_unavailability_constraint()` in `src/squola/scheduler.py` forces the corresponding CP-SAT variable to 0.

---

## Getting started

```bash
# Backend
uv run squola

# Frontend
cd frontend && npm install && npm run dev
```

Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`. API docs at `http://localhost:8000/docs`.
