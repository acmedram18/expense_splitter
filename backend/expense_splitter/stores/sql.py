"""SQLAlchemy-backed store.

Runs on any engine the URL supports (SQLite by default, PostgreSQL/MySQL by
swapping ``ENTRENOS_DB_URL``). Splits are stored as one ``ExpenseShare`` row per
participant; expenses are returned to the rest of the app as plain dict rows so
``logic`` and the routes stay database-agnostic.
"""

from contextlib import contextmanager
from datetime import date
from typing import Any, Iterator

from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from ..errors import ConflictError, NotFoundError
from .base import Store
from .seed import demo_seed


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    is_custom: Mapped[bool] = mapped_column(default=False)


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(200))
    amount_cents: Mapped[int]
    paid_by: Mapped[int] = mapped_column(ForeignKey("members.id"))
    date: Mapped[str] = mapped_column(String(10))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    notes: Mapped[str] = mapped_column(String(500), default="")
    split_mode: Mapped[str] = mapped_column(String(20), default="equal")
    shares: Mapped[list["ExpenseShare"]] = relationship(
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="ExpenseShare.id",
    )


class ExpenseShare(Base):
    __tablename__ = "expense_shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    share_cents: Mapped[int]


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    to_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    amount_cents: Mapped[int]
    date: Mapped[str] = mapped_column(String(10))


class SqlStore(Store):
    def __init__(self, url: str, seed: dict[str, Any] | None = None) -> None:
        self._engine = create_engine(url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self._engine)
        self._session_maker = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._seed(seed if seed is not None else demo_seed())

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _seed(self, seed: dict[str, Any]) -> None:
        with self._session() as session:
            if session.query(Member).first() is not None:
                return
            for category in seed["categories"]:
                session.add(
                    Category(
                        id=category["id"],
                        name=category["name"],
                        is_custom=category.get("is_custom", False),
                    )
                )
            for member in seed["members"]:
                session.add(
                    Member(id=member["id"], name=member["name"], is_active=member.get("is_active", True))
                )
            for expense in seed["expenses"]:
                session.add(
                    Expense(
                        id=expense["id"],
                        description=expense["description"],
                        amount_cents=expense["amount_cents"],
                        paid_by=expense["paid_by"],
                        date=expense["date"],
                        category_id=expense.get("category_id"),
                        notes=expense.get("notes", ""),
                        split_mode=expense.get("split_mode", "equal"),
                        shares=[
                            ExpenseShare(member_id=s["member_id"], share_cents=s["share_cents"])
                            for s in expense["shares"]
                        ],
                    )
                )
            for payment in seed["payments"]:
                session.add(
                    Payment(
                        id=payment["id"],
                        from_member_id=payment["from_member_id"],
                        to_member_id=payment["to_member_id"],
                        amount_cents=payment["amount_cents"],
                        date=payment["date"],
                    )
                )

    # --- dto helpers -------------------------------------------------------

    @staticmethod
    def _member_dto(member: Member) -> dict[str, Any]:
        return {"id": member.id, "name": member.name, "is_active": member.is_active}

    @staticmethod
    def _category_dto(category: Category) -> dict[str, Any]:
        return {"id": category.id, "name": category.name, "is_custom": category.is_custom}

    @staticmethod
    def _expense_dto(expense: Expense) -> dict[str, Any]:
        return {
            "id": expense.id,
            "description": expense.description,
            "amount_cents": expense.amount_cents,
            "paid_by": expense.paid_by,
            "date": expense.date,
            "category_id": expense.category_id,
            "notes": expense.notes,
            "split_mode": expense.split_mode,
            "shares": [
                {"member_id": s.member_id, "share_cents": s.share_cents}
                for s in expense.shares
            ],
        }

    @staticmethod
    def _payment_dto(payment: Payment) -> dict[str, Any]:
        return {
            "id": payment.id,
            "from_member_id": payment.from_member_id,
            "to_member_id": payment.to_member_id,
            "amount_cents": payment.amount_cents,
            "date": payment.date,
        }

    # --- shared ------------------------------------------------------------

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        with self._session() as session:
            members = [self._member_dto(m) for m in session.query(Member).order_by(Member.id).all()]
            categories = [self._category_dto(c) for c in session.query(Category).order_by(Category.id).all()]
            expenses = [self._expense_dto(e) for e in session.query(Expense).order_by(Expense.id).all()]
            payments = [self._payment_dto(p) for p in session.query(Payment).order_by(Payment.id).all()]
        return {
            "members": members,
            "categories": categories,
            "expenses": expenses,
            "payments": payments,
        }

    def member_ids(self) -> set[int]:
        with self._session() as session:
            return {row[0] for row in session.query(Member.id).all()}

    # --- members -----------------------------------------------------------

    def list_members(self) -> list[dict[str, Any]]:
        with self._session() as session:
            return [self._member_dto(m) for m in session.query(Member).order_by(Member.id).all()]

    def create_member(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            member = Member(name=payload["name"].strip(), is_active=True)
            session.add(member)
            session.flush()
            return self._member_dto(member)

    def update_member(self, member_id: int, patch: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            member = session.get(Member, member_id)
            if member is None:
                raise NotFoundError("Miembro no encontrado")
            if "name" in patch:
                member.name = patch["name"].strip()
            if "is_active" in patch:
                member.is_active = patch["is_active"]
            return self._member_dto(member)

    def delete_member(self, member_id: int) -> None:
        with self._session() as session:
            member = session.get(Member, member_id)
            if member is None:
                raise NotFoundError("Miembro no encontrado")
            used_in_expenses = bool(
                session.query(Expense)
                .filter(
                    (Expense.paid_by == member_id)
                    | Expense.shares.any(ExpenseShare.member_id == member_id)
                )
                .first()
            )
            used_in_payments = bool(
                session.query(Payment)
                .filter((Payment.from_member_id == member_id) | (Payment.to_member_id == member_id))
                .first()
            )
            if used_in_expenses or used_in_payments:
                raise ConflictError("El miembro está en uso en gastos o pagos")
            session.delete(member)

    # --- categories --------------------------------------------------------

    def list_categories(self) -> list[dict[str, Any]]:
        with self._session() as session:
            return [self._category_dto(c) for c in session.query(Category).order_by(Category.id).all()]

    # --- expenses ----------------------------------------------------------

    def list_expenses(self) -> list[dict[str, Any]]:
        with self._session() as session:
            return [self._expense_dto(e) for e in session.query(Expense).order_by(Expense.id).all()]

    def create_expense(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            self.validate_expense(payload, self._session_member_ids(session))
            expense = Expense(
                description=payload["description"].strip(),
                amount_cents=payload["amount_cents"],
                paid_by=payload["paid_by"],
                date=payload["date"],
                category_id=payload.get("category_id"),
                notes=payload.get("notes", ""),
                split_mode=payload.get("split_mode", "equal"),
                shares=[
                    ExpenseShare(member_id=s["member_id"], share_cents=s["share_cents"])
                    for s in payload["shares"]
                ],
            )
            session.add(expense)
            session.flush()
            return self._expense_dto(expense)

    def update_expense(self, expense_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            expense = session.get(Expense, expense_id)
            if expense is None:
                raise NotFoundError("Gasto no encontrado")
            self.validate_expense(payload, self._session_member_ids(session))
            expense.description = payload["description"].strip()
            expense.amount_cents = payload["amount_cents"]
            expense.paid_by = payload["paid_by"]
            expense.date = payload["date"]
            expense.category_id = payload.get("category_id")
            expense.notes = payload.get("notes", "")
            expense.split_mode = payload.get("split_mode", "equal")
            expense.shares = [
                ExpenseShare(member_id=s["member_id"], share_cents=s["share_cents"])
                for s in payload["shares"]
            ]
            return self._expense_dto(expense)

    def delete_expense(self, expense_id: int) -> None:
        with self._session() as session:
            expense = session.get(Expense, expense_id)
            if expense is None:
                raise NotFoundError("Gasto no encontrado")
            session.delete(expense)

    # --- payments ----------------------------------------------------------

    def list_payments(self) -> list[dict[str, Any]]:
        with self._session() as session:
            return [self._payment_dto(p) for p in session.query(Payment).order_by(Payment.id).all()]

    def create_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._session() as session:
            self.validate_payment(payload, self._session_member_ids(session))
            payment = Payment(
                from_member_id=payload["from_member_id"],
                to_member_id=payload["to_member_id"],
                amount_cents=payload["amount_cents"],
                date=payload.get("date") or date.today().isoformat(),
            )
            session.add(payment)
            session.flush()
            return self._payment_dto(payment)

    def delete_payment(self, payment_id: int) -> None:
        with self._session() as session:
            payment = session.get(Payment, payment_id)
            if payment is None:
                raise NotFoundError("Pago no encontrado")
            session.delete(payment)

    @staticmethod
    def _session_member_ids(session: Session) -> set[int]:
        return {row[0] for row in session.query(Member.id).all()}