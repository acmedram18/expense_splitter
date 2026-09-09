# Expense Splitter

A local app for sharing expenses among roommates/partners. Track who paid for
what, see who owes whom, and settle up with a minimal payment plan.

## Idea

Record expenses with different split modes (equal, percentage, custom
amounts). The app computes each member's net balance and suggests a minimal
set of transfers to settle everyone. A dashboard visualizes spending across
members, categories, and time.

## Status

In development. See [`_docs/specs.md`](_docs/specs.md) for the specification.

## Scope

- Members and categories management
- Expenses with equal / percentage / custom splits
- Net balance calculation per member
- Minimal settlement plan (greedy)
- Payment tracking (record actual transfers)
- Dashboard with charts (Recharts)

## Tech stack

- **Backend**: FastAPI, Python 3.12 (managed with `uv`), SQLite
- **Frontend**: React + Vite (Node.js), Recharts for charts
- Single user, local, no auth

## Setup

```bash
# Backend
uv sync --directory backend
uv run --directory backend python -m expense_splitter.seed   # seed default categories

# Frontend
cd frontend
npm install
```

## Run

```bash
# Backend (http://127.0.0.1:8000)
uv run --directory backend uvicorn expense_splitter.main:app --reload

# Frontend (http://127.0.0.1:5173)
cd frontend
npm run dev
```

## Tests

```bash
uv run --directory backend pytest
cd frontend && npm run test
```

## Production note

Intended for local, single-user use. No auth, no deployment hardening.