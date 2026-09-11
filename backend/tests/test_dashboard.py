def test_dashboard_aggregates(client):
    client.post(
        "/api/expenses",
        json={
            "description": "Supermercado",
            "amount_cents": 3000,
            "paid_by": 1,
            "date": "2026-09-10",
            "category_id": 3,
            "split_mode": "equal",
            "shares": [
                {"member_id": 1, "share_cents": 1000},
                {"member_id": 2, "share_cents": 1000},
                {"member_id": 3, "share_cents": 1000},
            ],
        },
    )
    client.post(
        "/api/expenses",
        json={
            "description": "Luz y agua",
            "amount_cents": 5000,
            "paid_by": 3,
            "date": "2026-08-19",
            "category_id": 2,
            "split_mode": "equal",
            "shares": [
                {"member_id": 1, "share_cents": 1000},
                {"member_id": 2, "share_cents": 1000},
                {"member_id": 3, "share_cents": 3000},
            ],
        },
    )

    res = client.get("/api/dashboard", params={"month": "2026-09"})
    assert res.status_code == 200
    body = res.json()

    assert body["month"] == "2026-09"
    assert body["totalMonthCents"] == 3000

    cats = {c["category_id"]: c for c in body["byCategoryMonth"]}
    assert cats == {3: {"category_id": 3, "name": "Supermercado", "total_cents": 3000}}

    by_member = {m["member_id"]: m for m in body["byMemberMonth"]}
    assert by_member[1]["total_cents"] == 3000
    assert by_member[2]["total_cents"] == 0
    assert by_member[3]["total_cents"] == 0

    series = body["monthlySeries"]
    assert [s["key"] for s in series] == ["2026-08", "2026-09"]
    assert series[1] == {"key": "2026-09", "label": "sep", "total_cents": 3000}

    by_id = {b["member_id"]: b for b in body["balances"]}
    assert by_id[1]["balance_cents"] == 1000
    assert by_id[2]["balance_cents"] == -2000
    assert by_id[3]["balance_cents"] == 1000

    plan = body["plan"]
    assert sum(p["amount_cents"] for p in plan) == 2000


def test_dashboard_with_no_expenses(client):
    body = client.get("/api/dashboard", params={"month": "2026-09"}).json()
    assert body["totalMonthCents"] == 0
    assert body["byCategoryMonth"] == []
    assert body["byMemberMonth"] == [
        {"member_id": 1, "name": "Ana", "total_cents": 0},
        {"member_id": 2, "name": "Luis", "total_cents": 0},
        {"member_id": 3, "name": "Marta", "total_cents": 0},
    ]
    assert body["monthlySeries"] == []
    assert body["balances"] == [
        {"member_id": 1, "name": "Ana", "is_active": True, "balance_cents": 0},
        {"member_id": 2, "name": "Luis", "is_active": True, "balance_cents": 0},
        {"member_id": 3, "name": "Marta", "is_active": True, "balance_cents": 0},
    ]


def test_dashboard_invalid_month(client):
    assert client.get("/api/dashboard", params={"month": "septiembre"}).status_code == 422
    assert client.get("/api/dashboard", params={"month": "2026-9"}).status_code == 422