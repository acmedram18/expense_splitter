"""In-memory store used for tests and as a fast local fallback.

Keeps the whole database as plain dict rows. Thread-safety: route handlers run
in a single worker thread in the dev server, so no locking is needed here.
"""

import json
import os
from datetime import date
from typing import Any

from ..errors import ConflictError, NotFoundError
from .base import Store
from .seed import demo_seed


class MockStore(Store):
    def __init__(
        self,
        seed: dict[str, Any] | None = None,
        persist_path: str | None = None,
    ) -> None:
        self.persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            try:
                with open(persist_path, encoding="utf-8") as fh:
                    seed = json.load(fh)
            except (OSError, ValueError):
                seed = seed if seed is not None else demo_seed()
        data = seed if seed is not None else demo_seed()
        self.members: list[dict[str, Any]] = [dict(r) for r in data["members"]]
        self.categories: list[dict[str, Any]] = [dict(r) for r in data["categories"]]
        self.expenses: list[dict[str, Any]] = [dict(r) for r in data["expenses"]]
        self.payments: list[dict[str, Any]] = [dict(r) for r in data["payments"]]
        self._persist()

    def _persist(self) -> None:
        if not self.persist_path:
            return
        state = {
            "members": self.members,
            "categories": self.categories,
            "expenses": self.expenses,
            "payments": self.payments,
        }
        with open(self.persist_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False)

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "members": [dict(m) for m in self.members],
            "categories": [dict(c) for c in self.categories],
            "expenses": [dict(e) for e in self.expenses],
            "payments": [dict(p) for p in self.payments],
        }

    def member_ids(self) -> set[int]:
        return {m["id"] for m in self.members}

    @staticmethod
    def _next_id(rows: list[dict[str, Any]]) -> int:
        return max((r["id"] for r in rows), default=0) + 1

    def _find_member(self, member_id: int) -> dict[str, Any] | None:
        return next((m for m in self.members if m["id"] == member_id), None)

    def _find_expense(self, expense_id: int) -> dict[str, Any] | None:
        return next((e for e in self.expenses if e["id"] == expense_id), None)

    def _find_payment(self, payment_id: int) -> dict[str, Any] | None:
        return next((p for p in self.payments if p["id"] == payment_id), None)

    # --- members -----------------------------------------------------------

    def list_members(self) -> list[dict[str, Any]]:
        return [dict(m) for m in self.members]

    def create_member(self, payload: dict[str, Any]) -> dict[str, Any]:
        member = {
            "id": self._next_id(self.members),
            "name": payload["name"].strip(),
            "is_active": True,
        }
        self.members.append(member)
        self._persist()
        return dict(member)

    def update_member(self, member_id: int, patch: dict[str, Any]) -> dict[str, Any]:
        row = self._find_member(member_id)
        if row is None:
            raise NotFoundError("Miembro no encontrado")
        if "name" in patch:
            row["name"] = patch["name"].strip()
        if "is_active" in patch:
            row["is_active"] = patch["is_active"]
        self._persist()
        return dict(row)

    def delete_member(self, member_id: int) -> None:
        if self._find_member(member_id) is None:
            raise NotFoundError("Miembro no encontrado")
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
        self._persist()

    # --- categories --------------------------------------------------------

    def list_categories(self) -> list[dict[str, Any]]:
        return [dict(c) for c in self.categories]

    # --- expenses ----------------------------------------------------------

    def list_expenses(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self.expenses]

    def _expense_dto(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "description": row["description"],
            "amount_cents": row["amount_cents"],
            "paid_by": row["paid_by"],
            "date": row["date"],
            "category_id": row["category_id"],
            "notes": row["notes"],
            "split_mode": row["split_mode"],
            "shares": [dict(s) for s in row["shares"]],
        }

    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_expense(payload, self.member_ids())
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
        self._persist()
        return self._expense_dto(expense)

    def update_expense(self, expense_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        row = self._find_expense(expense_id)
        if row is None:
            raise NotFoundError("Gasto no encontrado")
        self.validate_expense(payload, self.member_ids())
        row["description"] = payload["description"].strip()
        row["amount_cents"] = payload["amount_cents"]
        row["paid_by"] = payload["paid_by"]
        row["date"] = payload["date"]
        row["category_id"] = payload.get("category_id")
        row["notes"] = payload.get("notes", "")
        row["split_mode"] = payload.get("split_mode", "equal")
        row["shares"] = [
            {"member_id": s["member_id"], "share_cents": s["share_cents"]}
            for s in payload["shares"]
        ]
        self._persist()
        return self._expense_dto(row)

    def delete_expense(self, expense_id: int) -> None:
        if self._find_expense(expense_id) is None:
            raise NotFoundError("Gasto no encontrado")
        self.expenses = [e for e in self.expenses if e["id"] != expense_id]
        self._persist()

    # --- payments ----------------------------------------------------------

    def list_payments(self) -> list[dict[str, Any]]:
        return [dict(p) for p in self.payments]

    def _payment_dto(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "from_member_id": row["from_member_id"],
            "to_member_id": row["to_member_id"],
            "amount_cents": row["amount_cents"],
            "date": row["date"],
        }

    def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.validate_payment(payload, self.member_ids())
        payment = {
            "id": self._next_id(self.payments),
            "from_member_id": payload["from_member_id"],
            "to_member_id": payload["to_member_id"],
            "amount_cents": payload["amount_cents"],
            "date": payload.get("date") or date.today().isoformat(),
        }
        self.payments.append(payment)
        self._persist()
        return dict(payment)

    def delete_payment(self, payment_id: int) -> None:
        if self._find_payment(payment_id) is None:
            raise NotFoundError("Pago no encontrado")
        self.payments = [p for p in self.payments if p["id"] != payment_id]
        self._persist()