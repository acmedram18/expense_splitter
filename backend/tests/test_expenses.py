VALID_EXPENSE = {
    "description": "Supermercado",
    "amount_cents": 9000,
    "paid_by": 1,
    "date": "2026-09-01",
    "category_id": 3,
    "notes": "",
    "split_mode": "equal",
    "shares": [
        {"member_id": 1, "share_cents": 3000},
        {"member_id": 2, "share_cents": 3000},
        {"member_id": 3, "share_cents": 3000},
    ],
}


def test_create_expense(client):
    res = client.post("/api/expenses", json=VALID_EXPENSE)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == 1
    assert body["description"] == "Supermercado"
    assert body["amount_cents"] == 9000
    assert body["category_id"] == 3
    assert len(body["shares"]) == 3


def test_list_expenses(client):
    client.post("/api/expenses", json=VALID_EXPENSE)
    res = client.get("/api/expenses")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_create_expense_blank_description(client):
    payload = {**VALID_EXPENSE, "description": "   "}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_non_positive_amount(client):
    payload = {**VALID_EXPENSE, "amount_cents": 0}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_shares_must_sum_to_amount(client):
    bad_shares = [
        {"member_id": 1, "share_cents": 3000},
        {"member_id": 2, "share_cents": 3000},
        {"member_id": 3, "share_cents": 2500},
    ]
    payload = {**VALID_EXPENSE, "shares": bad_shares}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_empty_shares(client):
    payload = {**VALID_EXPENSE, "shares": []}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_negative_share(client):
    bad_shares = [
        {"member_id": 1, "share_cents": -1},
        {"member_id": 2, "share_cents": 3000},
        {"member_id": 3, "share_cents": 6001},
    ]
    payload = {**VALID_EXPENSE, "shares": bad_shares}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_unknown_share_member(client):
    bad_shares = [
        {"member_id": 1, "share_cents": 3000},
        {"member_id": 2, "share_cents": 3000},
        {"member_id": 999, "share_cents": 3000},
    ]
    payload = {**VALID_EXPENSE, "shares": bad_shares}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_unknown_payer(client):
    payload = {**VALID_EXPENSE, "paid_by": 999}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_create_expense_invalid_date(client):
    payload = {**VALID_EXPENSE, "date": "09/01/2026"}
    assert client.post("/api/expenses", json=payload).status_code == 422


def test_update_expense(client):
    created = client.post("/api/expenses", json=VALID_EXPENSE).json()
    payload = {
        **VALID_EXPENSE,
        "description": "Cena afuera",
        "amount_cents": 12000,
        "shares": [
            {"member_id": 1, "share_cents": 6000},
            {"member_id": 2, "share_cents": 6000},
        ],
    }
    res = client.put(f"/api/expenses/{created['id']}", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["description"] == "Cena afuera"
    assert body["amount_cents"] == 12000
    assert len(body["shares"]) == 2


def test_update_expense_not_found(client):
    assert client.put("/api/expenses/999", json=VALID_EXPENSE).status_code == 404


def test_update_expense_validates(client):
    created = client.post("/api/expenses", json=VALID_EXPENSE).json()
    payload = {**VALID_EXPENSE, "amount_cents": 0}
    assert client.put(f"/api/expenses/{created['id']}", json=payload).status_code == 422


def test_delete_expense(client):
    created = client.post("/api/expenses", json=VALID_EXPENSE).json()
    res = client.delete(f"/api/expenses/{created['id']}")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert client.get("/api/expenses").json() == []


def test_delete_expense_not_found(client):
    assert client.delete("/api/expenses/999").status_code == 404