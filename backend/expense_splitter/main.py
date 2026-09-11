from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import logic, schemas
from .errors import ConflictError, NotFoundError, ValidationError
from .store import MockStore

MOCK_DB_PATH = str(Path(__file__).resolve().parent / "db_mock.json")

store = MockStore(persist_path=MOCK_DB_PATH)


def get_store() -> MockStore:
    return store


app = FastAPI(title="EntreNos API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# --- members ---------------------------------------------------------------


@app.get("/api/members", response_model=list[schemas.MemberOut])
def list_members(store: MockStore = Depends(get_store)):
    return store.list_members()


@app.post("/api/members", response_model=schemas.MemberOut, status_code=201)
def create_member(body: schemas.MemberIn, store: MockStore = Depends(get_store)):
    return store.create_member(body.model_dump())


@app.patch("/api/members/{member_id}", response_model=schemas.MemberOut)
def update_member(
    member_id: int,
    body: schemas.MemberPatch,
    store: MockStore = Depends(get_store),
):
    return store.update_member(member_id, body.model_dump(exclude_unset=True))


@app.delete("/api/members/{member_id}")
def delete_member(member_id: int, store: MockStore = Depends(get_store)):
    store.delete_member(member_id)
    return {"ok": True}


# --- categories ------------------------------------------------------------


@app.get("/api/categories", response_model=list[schemas.CategoryOut])
def list_categories(store: MockStore = Depends(get_store)):
    return store.list_categories()


# --- expenses --------------------------------------------------------------


@app.get("/api/expenses", response_model=list[schemas.ExpenseOut])
def list_expenses(store: MockStore = Depends(get_store)):
    return store.list_expenses()


@app.post("/api/expenses", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(body: schemas.ExpenseIn, store: MockStore = Depends(get_store)):
    return store.create_expense(body.model_dump())


@app.put("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(
    expense_id: int,
    body: schemas.ExpenseIn,
    store: MockStore = Depends(get_store),
):
    return store.update_expense(expense_id, body.model_dump())


@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, store: MockStore = Depends(get_store)):
    store.delete_expense(expense_id)
    return {"ok": True}


# --- balances / settlement -------------------------------------------------


@app.get("/api/balances")
def get_balances(store: MockStore = Depends(get_store)):
    balances = logic.net_balances(store.members, store.expenses, store.payments)
    return [
        {
            "member_id": m["id"],
            "name": m["name"],
            "is_active": m["is_active"],
            "balance_cents": balances[m["id"]],
        }
        for m in store.members
    ]


@app.get("/api/settlement-plan")
def get_settlement_plan(store: MockStore = Depends(get_store)):
    return logic.settlement_plan(store.members, store.expenses, store.payments)


# --- payments --------------------------------------------------------------


@app.get("/api/payments", response_model=list[schemas.PaymentOut])
def list_payments(store: MockStore = Depends(get_store)):
    return store.list_payments()


@app.post("/api/payments", response_model=schemas.PaymentOut, status_code=201)
def create_payment(body: schemas.PaymentIn, store: MockStore = Depends(get_store)):
    return store.create_payment(body.model_dump())


@app.delete("/api/payments/{payment_id}")
def delete_payment(payment_id: int, store: MockStore = Depends(get_store)):
    store.delete_payment(payment_id)
    return {"ok": True}


# --- dashboard -------------------------------------------------------------


@app.get("/api/dashboard")
def get_dashboard(month: str, store: MockStore = Depends(get_store)):
    return logic.dashboard_aggregates(
        store.members,
        store.categories,
        store.expenses,
        store.payments,
        month,
    )