# AGENTS.md

Guidance for AI agents (and humans) working in this directory.

## Project layout

- `backend/` — FastAPI app (Python 3.12, managed with `uv`, SQLite)
- `frontend/` — React + Vite single-page app (Node.js, Recharts)
- `_docs/` — design docs (`specs.md` is the source of truth for scope)

## Commands

- Install backend deps: `uv sync --directory backend`
- Run backend dev server: `uv run --directory backend uvicorn expense_splitter.main:app --reload`
- Backend tests: `uv run --directory backend pytest`
- Install frontend deps: `cd frontend && npm install`
- Run frontend dev server: `cd frontend && npm run dev`
- Frontend build: `cd frontend && npm run build`

Note: never `cd` into `backend` and run `uv` bare; always use
`--directory backend` so the working directory convention stays consistent.

## Conventions

- Python code: type hints on all public functions, plain stdlib-style FastAPI
  routes, Pydantic models for all request/response bodies.
- The database lives only in the backend (`expense_splitter/db.sqlite3`).
- Splits are always stored as `ExpenseShare` rows (one per participant); the
  sum of shares must equal the expense amount (validate on write).
- Money values are stored in integer cents to avoid float issues.
- Frontend: one component per file under `frontend/src/components`, API calls
  through a small fetch wrapper in `frontend/src/api.js`.
- Do not add comments unless they explain *why*, not *what*.
- Update `_docs/specs.md` when scope changes, before writing code.
- Write tests for balance/settlement logic (the greedy settlement and net
  balance math are the core of the app).

## Definition of done

- `uv run --directory backend pytest` and `cd frontend && npm run build` pass.
- New backend endpoints have tests.
- New frontend pages/components are wired to the real API (no mocks).