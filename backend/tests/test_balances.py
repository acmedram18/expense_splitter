EXPENSE_ANA = {
    "description": "Supermercado",
    "amount_cents": 9000,
    "paid_by": 1,
    "date": "2026-09-10",
    "category_id": 3,
    "split_mode": "equal",
    "shares": [
        {"member_id": 1, "share_cents": 3000},
        {"member_id": 2, "share_cents": 3000},
        {"member_id": 3, "share_cents": 3000},
    ],
}


def test_balances_endpoint(client):
    client.post("/api/expenses", json=EXPENSE_ANA)
    res = client.get("/api/balances")
    assert res.status_code == 200
    body = res.json()
    by_id = {b["member_id"]: b for b in body}
    assert by_id[1]["balance_cents"] == 6000
    assert by_id[2]["balance_cents"] == -3000
    assert by_id[3]["balance_cents"] == -3000
    assert all(b["name"] for b in body)
    assert all(b["is_active"] for b in body)


def test_balances_reflect_payments(client):
    client.post("/api/expenses", json=EXPENSE_ANA)
    client.post(
        "/api/payments",
        json={"from_member_id": 2, "to_member_id": 1, "amount_cents": 3000},
    )
    body = client.get("/api/balances").json()
    by_id = {b["member_id"]: b for b in body}
    assert by_id[1]["balance_cents"] == 3000
    assert by_id[2]["balance_cents"] == 0
    assert by_id[3]["balance_cents"] == -3000


def test_settlement_plan_endpoint(client):
    client.post("/api/expenses", json=EXPENSE_ANA)
    res = client.get("/api/settlement-plan")
    assert res.status_code == 200
    plan = res.json()
    assert plan == [
        {"from_member_id": 2, "from_name": "Luis", "to_member_id": 1, "to_name": "Ana", "amount_cents": 3000},
        {"from_member_id": 3, "from_name": "Marta", "to_member_id": 1, "to_name": "Ana", "amount_cents": 3000},
    ]


def test_settlement_plan_empty(client):
    assert client.get("/api/settlement-plan").json() == []