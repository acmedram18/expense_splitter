"""Seed data shared by every store implementation.

Stores receive a plain-dict "seed" describing the initial members, categories,
expenses and payments. The SQL store loads it once when the database file is
created; the in-memory mock loads it on every start.
"""

from typing import Any

DEFAULT_CATEGORIES = [
    {"id": 1, "name": "Alquiler", "is_custom": False},
    {"id": 2, "name": "Servicios", "is_custom": False},
    {"id": 3, "name": "Supermercado", "is_custom": False},
    {"id": 4, "name": "Transporte", "is_custom": False},
    {"id": 5, "name": "Entretenimiento", "is_custom": False},
    {"id": 6, "name": "Otros", "is_custom": False},
]


def empty_seed() -> dict[str, Any]:
    """Members and default categories, no expenses or payments. Used by tests."""
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


def _equal_shares(ids: list[int], amount_cents: int) -> list[dict[str, Any]]:
    base = amount_cents // len(ids)
    rem = amount_cents - base * len(ids)
    shares = []
    for member_id in ids:
        shares.append({"member_id": member_id, "share_cents": base + (1 if rem > 0 else 0)})
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
    members = [
        {"id": 1, "name": "Ana", "is_active": True},
        {"id": 2, "name": "Luis", "is_active": True},
        {"id": 3, "name": "Marta", "is_active": True},
    ]
    return {
        "members": members,
        "categories": [dict(c) for c in DEFAULT_CATEGORIES],
        "expenses": expenses,
        "payments": payments,
    }