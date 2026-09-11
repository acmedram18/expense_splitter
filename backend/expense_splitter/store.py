"""Storage layer.

``MockStore`` keeps the whole database in memory as plain dict rows. It is the
only place that knows the data shape, so later we can replace it with a
SQLite-backed store behind the same method signatures without touching routes.
"""

from datetime import date
from typing import Any

from .errors import ConflictError, NotFoundError, ValidationError

DEFAULT_CATEGORIES = [
    {"id": 1, "name": "Alquiler", "is_custom": False},
    {"id": 2, "name": "Servicios", "is_custom": False},
    {"id": 3, "name": "Supermercado", "is_custom": False},
    {"id": 4, "name": "Transporte", "is_custom": False},
    {"id": 5, "name": "Entretenimiento", "is_custom": False},
    {"id": 6, "name": "Otros", "is_custom": False},
]


def empty_seed() -> dict[str, Any]:
    return {
        "members": [
            {"id": 1, "name": "Ana", "is_active": True},
            {"id": 2, "name": "Luis", "is_active": True},
            {"id": 3, "name": "Marta", "is_active": True},
        ],
        "categories": [dict(c) for c in DEFAULT_CATEGORIES],
        "expenses": [],
        "payments": [],
    }


def _share(ids, member, share_cents):
    return {"member_id": member, "share_cents": share_cents}


def _equal_shares(ids, amount_cents) -> list[dict[str, Any]]:
    base = amount_cents // len(ids)
    rem = amount_cents - base * len(ids)
    shares = []
    for member_id in ids:
        shares.append(_share(ids, member_id, base + (1 if rem > 0 else 0)))
        if rem > 0:
            rem -= 1
    return shares


def demo_seed() -> dict[str, Any]:
    """A few months of realistic data so the app feels alive on first run."""
    rent = [1, 2, 3]
    expenses = [
        {"id": 1, "description": "Alquiler", "amount_cents": 150000, "paid_by": 1, "date": "2026-09-01", "category_id": 1, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 150000)},
        {"id": 2, "description": "Alquiler", "amount_cents": 150000, "paid_by": 2, "date": "2026-08-01", "category_id": 1, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 150000)},
        {"id": 3, "description": "Alquiler", "amount_cents": 150000, "paid_by": 1, "date": "2026-07-01", "category_id": 1, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 150000)},
        {"id": 4, "description": "Luz y agua", "amount_cents": 21500, "paid_by": 1, "date": "2026-08-09", "category_id": 2, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 21500)},
        {"id": 5, "description": "Internet", "amount_cents": 18900, "paid_by": 2, "date": "2026-07-12", "category_id": 2, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 18900)},
        {"id": 6, "description": "Supermercado", "amount_cents": 8400, "paid_by": 3, "date": "2026-09-03", "category_id": 3, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 8400)},
        {"id": 7, "description": "Supermercado", "amount_cents": 6320, "paid_by": 2, "date": "2026-09-04", "category_id": 3, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 6320)},
        {"id": 8, "description": "Supermercado", "amount_cents": 11800, "paid_by": 1, "date": "2026-08-10", "category_id": 3, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 11800)},
        {"id": 9, "description": "Gasolina / tarjeta metro", "amount_cents": 6800, "paid_by": 2, "date": "2026-08-12", "category_id": 4, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 6800)},
        {"id": 10, "description": "Cena afuera", "amount_cents": 23000, "paid_by": 3, "date": "2026-07-21", "category_id": 5, "notes": "", "split_mode": "percent", "shares": [
            {"member_id": 3, "share_cents": 9200},
            {"member_id": 2, "share_cents": 8050},
            {"member_id": 1, "share_cents": 5750},
        ]},
        {"id": 11, "description": "Artículos para la casa", "amount_cents": 5400, "paid_by": 1, "date": "2026-06-20", "category_id": 6, "notes": "", "split_mode": "equal", "shares": _equal_shares(rent, 5400)},
    ]
    payments = [
        {"id": 1, "from_member_id": 3, "to_member_id": 1, "amount_cents": 50000, "date": "2026-08-07"},
    ]
    return {
        "members": [
            {"id": 1, "name": "Ana", "is_active": True},
            {"id": 2, "name": "Luis", "is_active": True},
            {"id": 3, "name": "Marta", "is_active": True},
        ],
        "categories": [dict(c) for c in DEFAULT_CATEGORIES],
        "expenses": expenses,
        "payments": payments,
    }


class MockStore:
    """In-memory store. Thread-safety: route handlers run in a single worker
    thread in the dev server, so no locking is needed for the mock."""

    def __init__(self, seed: dict[str, Any] | None = None) -> None:
        data = seed if seed is not None else demo_seed()
        self.members: list[dict[str, Any]] = [dict(r) for r in data["members"]]
        self.categories: list[dict[str, Any]] = [dict(r) for r in data["categories"]]
        self.expenses: list[dict[str, Any]] = [dict(r) for r in data["expenses"]]
        self.payments: list[dict[str, Any]] = [dict(r) for r in data["payments"]]

    @staticmethod
    def _next_id(rows: list[dict[str, Any]]) -> int:
        return max((r["id"] for r in rows), default=0) + 1

    def _member_ids(self) -> set[int]:
        return {m["id"] for m in self.members}

    # --- members -----------------------------------------------------------

    def list_members(self) -> list[dict[str, Any]]:
        return [dict(m) for m in self.members]

    def get_member(self, member_id: int) -> dict[str, Any]:
        for member in self.members:
            if member["id"] == member_id:
                return dict(member)
        raise NotFoundError("Miembro no encontrado")

    def create_member(self, payload: dict[str, Any]) -> dict[str, Any]:
        member = {
            "id": self._next_id(self.members),
            "name": payload["name"].strip(),
            "is_active": True,
        }
        self.members.append(member)
        return dict(member)

    def update_member(self, member_id: int, patch: dict[str, Any]) -> dict[str, Any]:
        member = self.get_member(member_id)
        if "name" in patch:
            member["name"] = patch["name"].strip()
        if "is_active" in patch:
            member["is_active"] = patch["is_active"]
        return dict(member)

    def delete_member(self, member_id: int) -> None:
        self.get_member(member_id)
        used_in_expenses = any(
            e["paid_by"] == member_id or any(s["member_id"] == member_id for s in e["shares"])
            for e in self.expenses
        )
        used_in_payments = any(
            p["from_member_id"] == member_id or p["to_member_id"] == member_id
            for p in self.payments
        )
        if used_in_expenses or used_in_payments:
            raise ConflictError("El miembro está en uso en gastos o pagos")
        self.members = [m for m in self.members if m["id"] != member_id]

    # --- categories --------------------------------------------------------

    def list_categories(self) -> list[dict[str, Any]]:
        return [dict(c) for c in self.categories]

    # --- expenses ----------------------------------------------------------

    def list_expenses(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self.expenses]

    def get_expense(self, expense_id: int) -> dict[str, Any]:
        for expense in self.expenses:
            if expense["id"] == expense_id:
                return dict(expense)
        raise NotFoundError("Gasto no encontrado")

    def _validate_expense(self, payload: dict[str, Any]) -> None:
        if not payload["description"].strip():
            raise ValidationError("La descripción es obligatoria")
        if payload["amount_cents"] <= 0:
            raise ValidationError("El monto debe ser mayor que cero")
        member_ids = self._member_ids()
        if payload["paid_by"] not in member_ids:
            raise ValidationError("Miembro no encontrado")
        if not payload["shares"]:
            raise ValidationError("Debe haber al menos un participante")
        for share in payload["shares"]:
            if share["member_id"] not in member_ids:
                raise ValidationError("Miembro no encontrado")
            if share["share_cents"] < 0:
                raise ValidationError("Las partes no pueden ser negativas")
        total = sum(s["share_cents"] for s in payload["shares"])
        if total != payload["amount_cents"]:
            raise ValidationError("Las partes deben sumar el monto del gasto")

    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_expense(payload)
        expense = {
            "id": self._next_id(self.expenses),
            "description": payload["description"].strip(),
            "amount_cents": payload["amount_cents"],
            "paid_by": payload["paid_by"],
            "date": payload["date"],
            "category_id": payload.get("category_id"),
            "notes": payload.get("notes", ""),
            "split_mode": payload.get("split_mode", "equal"),
            "shares": [
                {"member_id": s["member_id"], "share_cents": s["share_cents"]}
                for s in payload["shares"]
            ],
        }
        self.expenses.append(expense)
        return dict(expense)

    def update_expense(self, expense_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        expense = self.get_expense(expense_id)
        self._validate_expense(payload)
        expense["description"] = payload["description"].strip()
        expense["amount_cents"] = payload["amount_cents"]
        expense["paid_by"] = payload["paid_by"]
        expense["date"] = payload["date"]
        expense["category_id"] = payload.get("category_id")
        expense["notes"] = payload.get("notes", "")
        expense["split_mode"] = payload.get("split_mode", "equal")
        expense["shares"] = [
            {"member_id": s["member_id"], "share_cents": s["share_cents"]}
            for s in payload["shares"]
        ]
        return dict(expense)

    def delete_expense(self, expense_id: int) -> None:
        self.get_expense(expense_id)
        self.expenses = [e for e in self.expenses if e["id"] != expense_id]

    # --- payments ----------------------------------------------------------

    def list_payments(self) -> list[dict[str, Any]]:
        return [dict(p) for p in self.payments]

    def get_payment(self, payment_id: int) -> dict[str, Any]:
        for payment in self.payments:
            if payment["id"] == payment_id:
                return dict(payment)
        raise NotFoundError("Pago no encontrado")

    def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        member_ids = self._member_ids()
        if payload["from_member_id"] not in member_ids or payload["to_member_id"] not in member_ids:
            raise ValidationError("Miembro no encontrado")
        if payload["from_member_id"] == payload["to_member_id"]:
            raise ValidationError("No puedes pagarte a ti mismo")
        if payload["amount_cents"] <= 0:
            raise ValidationError("El monto debe ser positivo")
        payment = {
            "id": self._next_id(self.payments),
            "from_member_id": payload["from_member_id"],
            "to_member_id": payload["to_member_id"],
            "amount_cents": payload["amount_cents"],
            "date": payload.get("date") or date.today().isoformat(),
        }
        self.payments.append(payment)
        return dict(payment)

    def delete_payment(self, payment_id: int) -> None:
        self.get_payment(payment_id)
        self.payments = [p for p in self.payments if p["id"] != payment_id]