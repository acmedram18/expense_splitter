from expense_splitter.logic import net_balances, settlement_plan

MEMBERS = [
    {"id": 1, "name": "Ana", "is_active": True},
    {"id": 2, "name": "Luis", "is_active": True},
    {"id": 3, "name": "Marta", "is_active": True},
]


def expense(eid, paid_by, amount, shares, date="2026-09-01"):
    return {
        "id": eid,
        "description": "x",
        "amount_cents": amount,
        "paid_by": paid_by,
        "date": date,
        "category_id": 3,
        "notes": "",
        "split_mode": "custom",
        "shares": [{"member_id": m, "share_cents": c} for m, c in shares],
    }


def payment(pid, frm, to, amount, date="2026-09-02"):
    return {
        "id": pid,
        "from_member_id": frm,
        "to_member_id": to,
        "amount_cents": amount,
        "date": date,
    }


def test_net_balances_empty():
    assert net_balances(MEMBERS, [], []) == {1: 0, 2: 0, 3: 0}


def test_net_balances_equal_split():
    # Ana paid 9000 split equally -> Ana owns 3000 of it, receives 6000.
    bal = net_balances(
        MEMBERS,
        [expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)])],
        [],
    )
    assert bal == {1: 6000, 2: -3000, 3: -3000}


def test_net_balances_percent_split():
    # Luis paid 10000, keeps 40%, Ana gets 60% of it.
    bal = net_balances(
        MEMBERS,
        [expense(1, 2, 10000, [(2, 4000), (1, 6000)])],
        [],
    )
    assert bal == {1: -6000, 2: 6000, 3: 0}


def test_net_balances_custom_payer_zero_share():
    # Marta pays 5000 entirely on Ana's behalf.
    bal = net_balances(
        MEMBERS,
        [expense(1, 3, 5000, [(1, 5000)])],
        [],
    )
    assert bal == {1: -5000, 2: 0, 3: 5000}


def test_net_balances_payment_shifts_debt():
    bal = net_balances(
        MEMBERS,
        [expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)])],
        [payment(1, 2, 1, 3000)],
    )
    assert bal == {1: 3000, 2: 0, 3: -3000}


def test_settlement_plan_single_creditor():
    plan = settlement_plan(
        MEMBERS,
        [expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)])],
        [],
    )
    assert plan == [
        {"from_member_id": 2, "from_name": "Luis", "to_member_id": 1, "to_name": "Ana", "amount_cents": 3000},
        {"from_member_id": 3, "from_name": "Marta", "to_member_id": 1, "to_name": "Ana", "amount_cents": 3000},
    ]


def test_settlement_plan_multiple_creditors_and_chain():
    # Ana owes 5000 (paid for her), Luis owes 3000. Marta is owed 4800,
    # Ana is owed 3200 by... build a two-creditor, two-debtor scenario:
    bal = net_balances(
        MEMBERS,
        [
            expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)]),
            expense(2, 3, 10000, [(3, 2000), (1, 8000)]),
        ],
        [],
    )
    # Ana crediting: 6000, debiting 8000 -> -2000. Luis: -3000. Marta: +8000 applied
    # (10000 - 2000) minus owed 3000 -> +5000.
    assert bal == {1: -2000, 2: -3000, 3: 5000}
    plan = settlement_plan(MEMBERS, [
        expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)]),
        expense(2, 3, 10000, [(3, 2000), (1, 8000)]),
    ], [])
    assert sum(p["amount_cents"] for p in plan) == 5000
    assert plan == [
        {"from_member_id": 1, "from_name": "Ana", "to_member_id": 3, "to_name": "Marta", "amount_cents": 2000},
        {"from_member_id": 2, "from_name": "Luis", "to_member_id": 3, "to_name": "Marta", "amount_cents": 3000},
    ]


def test_settlement_plan_empty_when_everyone_settled():
    assert settlement_plan(MEMBERS, [], []) == []
    plan = settlement_plan(
        MEMBERS,
        [
            expense(1, 1, 9000, [(1, 3000), (2, 3000), (3, 3000)]),
            expense(2, 2, 9000, [(1, 3000), (2, 3000), (3, 3000)]),
            expense(3, 3, 9000, [(1, 3000), (2, 3000), (3, 3000)]),
        ],
        [],
    )
    assert plan == []