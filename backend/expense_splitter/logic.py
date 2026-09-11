"""Pure balance and settlement math, plus dashboard aggregation helpers.

All functions operate on plain dict rows (the shape stored by a store) so they
can be tested in isolation and reused once a real database is swapped in.
"""

import re
from typing import Any

from .errors import ValidationError

MONTH_LABELS = {
    1: "ene",
    2: "feb",
    3: "mar",
    4: "abr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dic",
}

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def net_balances(
    members: list[dict[str, Any]],
    expenses: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> dict[int, int]:
    """Net balance per member id, in integer cents.

    For each expense the payer receives ``amount - their share`` and every other
    participant owes their share. Recorded payments move debt from the payer to
    the receiver.
    """
    balances = {m["id"]: 0 for m in members}
    for expense in expenses:
        payer = expense["paid_by"]
        payer_share = next(
            (s["share_cents"] for s in expense["shares"] if s["member_id"] == payer),
            0,
        )
        balances[payer] += expense["amount_cents"] - payer_share
        for share in expense["shares"]:
            if share["member_id"] != payer:
                balances[share["member_id"]] -= share["share_cents"]
    for payment in payments:
        balances[payment["from_member_id"]] += payment["amount_cents"]
        balances[payment["to_member_id"]] -= payment["amount_cents"]
    return balances


def settlement_plan(
    members: list[dict[str, Any]],
    expenses: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Greedy minimal-transfer plan: largest debtor repays largest creditor.

    Ties are broken by member id so the output is deterministic.
    """
    names = {m["id"]: m["name"] for m in members}
    balances = net_balances(members, expenses, payments)

    debtors = sorted(
        ((mid, b) for mid, b in balances.items() if b < 0),
        key=lambda item: (-item[1], item[0]),
    )
    creditors = sorted(
        ((mid, b) for mid, b in balances.items() if b > 0),
        key=lambda item: (-item[1], item[0]),
    )

    plan: list[dict[str, Any]] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor_id, debtor_balance = debtors[i]
        creditor_id, creditor_balance = creditors[j]
        transfer = min(-debtor_balance, creditor_balance)
        if transfer > 0:
            plan.append(
                {
                    "from_member_id": debtor_id,
                    "from_name": names.get(debtor_id, "?"),
                    "to_member_id": creditor_id,
                    "to_name": names.get(creditor_id, "?"),
                    "amount_cents": transfer,
                }
            )
            debtors[i] = (debtor_id, debtor_balance + transfer)
            creditors[j] = (creditor_id, creditor_balance - transfer)
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1
    return plan


def dashboard_aggregates(
    members: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    expenses: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    month: str,
) -> dict[str, Any]:
    """Everything the dashboard page needs for a single month."""
    if not _MONTH_RE.match(month):
        raise ValidationError("el mes debe tener formato YYYY-MM")

    in_month = [e for e in expenses if e["date"][:7] == month]

    by_category_month = [
        {
            "category_id": c["id"],
            "name": c["name"],
            "total_cents": sum(e["amount_cents"] for e in in_month if e["category_id"] == c["id"]),
        }
        for c in categories
    ]
    by_category_month = [row for row in by_category_month if row["total_cents"] > 0]

    by_member_month = [
        {
            "member_id": m["id"],
            "name": m["name"],
            "total_cents": sum(e["amount_cents"] for e in in_month if e["paid_by"] == m["id"]),
        }
        for m in members
    ]

    month_keys = sorted({e["date"][:7] for e in expenses})
    monthly_series = []
    for key in month_keys:
        monthly_series.append(
            {
                "key": key,
                "label": MONTH_LABELS[int(key[5:7])],
                "total_cents": sum(e["amount_cents"] for e in expenses if e["date"][:7] == key),
            }
        )

    balances = net_balances(members, expenses, payments)
    balance_rows = [
        {
            "member_id": m["id"],
            "name": m["name"],
            "is_active": m["is_active"],
            "balance_cents": balances[m["id"]],
        }
        for m in members
    ]

    return {
        "month": month,
        "totalMonthCents": sum(e["amount_cents"] for e in in_month),
        "byCategoryMonth": by_category_month,
        "byMemberMonth": by_member_month,
        "monthlySeries": monthly_series,
        "balances": balance_rows,
        "plan": settlement_plan(members, expenses, payments),
    }