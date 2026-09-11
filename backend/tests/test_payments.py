def test_create_payment(client):
    res = client.post(
        "/api/payments",
        json={
            "from_member_id": 2,
            "to_member_id": 1,
            "amount_cents": 5000,
            "date": "2026-09-05",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["from_member_id"] == 2
    assert body["to_member_id"] == 1
    assert body["amount_cents"] == 5000
    assert body["date"] == "2026-09-05"


def test_create_payment_defaults_to_today(client):
    from datetime import date as _date

    res = client.post(
        "/api/payments",
        json={"from_member_id": 2, "to_member_id": 1, "amount_cents": 5000},
    )
    assert res.status_code == 201
    assert res.json()["date"] == _date.today().isoformat()


def test_create_payment_cannot_pay_self(client):
    res = client.post(
        "/api/payments",
        json={"from_member_id": 1, "to_member_id": 1, "amount_cents": 5000},
    )
    assert res.status_code == 422


def test_create_payment_amount_must_be_positive(client):
    res = client.post(
        "/api/payments",
        json={"from_member_id": 2, "to_member_id": 1, "amount_cents": 0},
    )
    assert res.status_code == 422


def test_create_payment_unknown_member(client):
    res = client.post(
        "/api/payments",
        json={"from_member_id": 999, "to_member_id": 1, "amount_cents": 5000},
    )
    assert res.status_code == 422


def test_create_payment_invalid_date(client):
    res = client.post(
        "/api/payments",
        json={
            "from_member_id": 2,
            "to_member_id": 1,
            "amount_cents": 5000,
            "date": "not-a-date",
        },
    )
    assert res.status_code == 422


def test_list_payments(client):
    client.post(
        "/api/payments",
        json={"from_member_id": 2, "to_member_id": 1, "amount_cents": 5000},
    )
    client.post(
        "/api/payments",
        json={"from_member_id": 3, "to_member_id": 1, "amount_cents": 4000},
    )
    res = client.get("/api/payments")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_delete_payment(client):
    created = client.post(
        "/api/payments",
        json={"from_member_id": 2, "to_member_id": 1, "amount_cents": 5000},
    ).json()
    res = client.delete(f"/api/payments/{created['id']}")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    assert client.get("/api/payments").json() == []


def test_delete_payment_not_found(client):
    assert client.delete("/api/payments/999").status_code == 404