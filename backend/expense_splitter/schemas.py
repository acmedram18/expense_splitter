from datetime import date

from pydantic import BaseModel, Field, field_validator


def _parse_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("formato de fecha inválido (YYYY-MM-DD)") from exc
    return value


class MemberIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("el nombre no puede estar vacío")
        return value


class MemberPatch(BaseModel):
    name: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("el nombre no puede estar vacío")
        return value


class MemberOut(BaseModel):
    id: int
    name: str
    is_active: bool


class CategoryOut(BaseModel):
    id: int
    name: str
    is_custom: bool


class ShareIn(BaseModel):
    member_id: int
    share_cents: int = Field(ge=0)


class ExpenseIn(BaseModel):
    description: str
    amount_cents: int = Field(gt=0)
    paid_by: int
    date: str
    category_id: int | None = None
    notes: str = ""
    split_mode: str = "equal"
    shares: list[ShareIn] = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("la descripción no puede estar vacía")
        return value

    @field_validator("date")
    @classmethod
    def valid_date(cls, value: str) -> str:
        return _parse_date(value)


class ExpenseOut(BaseModel):
    id: int
    description: str
    amount_cents: int
    paid_by: int
    date: str
    category_id: int | None
    notes: str
    split_mode: str
    shares: list[ShareIn]


class PaymentIn(BaseModel):
    from_member_id: int
    to_member_id: int
    amount_cents: int = Field(gt=0)
    date: str | None = None

    @field_validator("date")
    @classmethod
    def valid_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _parse_date(value)


class PaymentOut(BaseModel):
    id: int
    from_member_id: int
    to_member_id: int
    amount_cents: int
    date: str