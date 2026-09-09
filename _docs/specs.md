# Expense Splitter — Specification

## Overview

A local app for sharing expenses among roommates/partners. It tracks who paid
for what, who owes whom, and suggests a minimal set of payments to settle debts.

## Form factor & tech stack

- **Backend**: FastAPI (Python 3.12, managed with `uv`) + SQLite
- **Frontend**: React + Vite (Node.js), charts with **Recharts**
- Single user, local, no accounts/login (same scope as ChoreBalancer)
- Located at `expense_splitter/` inside this repo

## Data model (4 tables)

| Entity        | Fields                                                    |
|---------------|-----------------------------------------------------------|
| `Member`      | name, is_active                                           |
| `Category`    | name, is_custom                       |
| `Expense`     | description, amount, paid_by (FK Member), date, category (FK, nullable), notes |
| `ExpenseShare`| expense (FK), member (FK), share_amount                   |

`Category` is seeded with defaults: rent, utilities, groceries, transport,
entertainment, other (plus user-created ones via `is_custom`).

## Splitting modes (chosen on each expense)

- **Equal** — amount ÷ number of participants
- **Percentage** — e.g. rent 60/40
- **Custom amounts** — manually entered, must sum to the total exactly

Each split generates one `ExpenseShare` per participant; the sum of all shares
must equal the expense amount.

## The balancing algorithm

- For each expense, the payer "receives" `amount − their share`; every other
  participant "owes" their `share_amount`.
- **Net balance per member** = total to receive − total to owe (+/−).
- **Settlement plan** (greedy, minimal transfers): repeatedly take the largest
  creditor and the largest debtor, transfer `min(balances)`, repeat until all
  net balances are ~0. The output is the suggested payments.

## API endpoints (backend)

| Method | Path              | Purpose                          |
|--------|-------------------|----------------------------------|
| GET/POST/PUT/DELETE | `/members` | Manage household members |
| GET/POST/PUT/DELETE | `/expenses` | Manage expenses (shares included in payload) |
| GET    | `/categories`     | List categories                  |
| GET    | `/balances`       | Net balance per member           |
| GET    | `/settlement-plan`| Suggested minimal payments       |
| POST/GET | `/payments`     | Record actual (realized) payments |
| GET    | `/dashboard`      | Aggregates for the dashboard     |

## Pages (frontend)

1. **Dashboard**
   - Net balance per member (summary cards)
   - Total spent this month, by member and by category
   - Charts (Recharts): spending by category (bar), spending over time (line),
     balance distribution (pie) and a "who owes whom" overview
2. **Expenses** — list with filters (category / month / member) + add/edit form
   covering all three splitting modes
3. **Members** — CRUD, activate/deactivate
4. **Settle Up** — suggested payment plan + record real payments

## Scope explicitly cut

- Auth / multi-user accounts
- Multi-currency
- Recurring/automatic expenses
- Receipt upload / OCR
- Notifications / reminders

## Open assumptions (to confirm before building)

1. **Editing past expenses**: if a paid expense is edited (amount, participants,
   split), shares and balances are recalculated, and any recorded payment
   touching those shares is re-flagged as pending for manual confirmation.
2. **Inactive members**: kept in history and existing shares, but excluded from
   new splits (not selectable as payer or participant) unless reactivated.
3. **Currency**: single currency (USD implied, editable via a single setting).