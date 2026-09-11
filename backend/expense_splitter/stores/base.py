"""Store abstraction.

Routes in ``main.py`` depend only on this interface, so the persistence
backend (in-memory mock vs SQLAlchemy) can be swapped without touching the
HTTP layer. Validation rules shared by every implementation live here.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..errors import ValidationError


class Store(ABC):
    """Storage interface implemented by ``MockStore`` and ``SqlStore``.

    All methods operate on plain-dict rows, the same shape ``logic`` expects.
    """

    @abstractmethod
    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        """Full state as dict rows: members, categories, expenses, payments."""

    @abstractmethod
    def member_ids(self) -> set[int]:
        """Ids of every member currently stored."""

    # --- members -----------------------------------------------------------

    @abstractmethod
    def list_members(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def create_member(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update_member(self, member_id: int, patch: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def delete_member(self, member_id: int) -> None: ...

    # --- categories --------------------------------------------------------

    @abstractmethod
    def list_categories(self) -> list[dict[str, Any]]: ...

    # --- expenses ----------------------------------------------------------

    @abstractmethod
    def list_expenses(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def update_expense(self, expense_id: int, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def delete_expense(self, expense_id: int) -> None: ...

    # --- payments ----------------------------------------------------------

    @abstractmethod
    def list_payments(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    def delete_payment(self, payment_id: int) -> None: ...

    # --- shared validation -------------------------------------------------

    @staticmethod
    def validate_expense(payload: dict[str, Any], member_ids: set[int]) -> None:
        if not payload["description"].strip():
            raise ValidationError("La descripción es obligatoria")
        if payload["amount_cents"] <= 0:
            raise ValidationError("El monto debe ser mayor que cero")
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

    @staticmethod
    def validate_payment(payload: dict[str, Any], member_ids: set[int]) -> None:
        if payload["from_member_id"] not in member_ids or payload["to_member_id"] not in member_ids:
            raise ValidationError("Miembro no encontrado")
        if payload["from_member_id"] == payload["to_member_id"]:
            raise ValidationError("No puedes pagarte a ti mismo")
        if payload["amount_cents"] <= 0:
            raise ValidationError("El monto debe ser positivo")