def test_list_members_seeded(client):
    res = client.get("/api/members")
    assert res.status_code == 200
    body = res.json()
    assert [m["name"] for m in body] == ["Ana", "Luis", "Marta"]
    assert all(m["is_active"] for m in body)


def test_create_member(client):
    res = client.post("/api/members", json={"name": "Sara"})
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == 4
    assert body["name"] == "Sara"
    assert body["is_active"] is True

    listed = client.get("/api/members").json()
    assert len(listed) == 4


def test_create_member_blank_name(client):
    res = client.post("/api/members", json={"name": "   "})
    assert res.status_code == 422


def test_update_member_name(client):
    res = client.patch("/api/members/1", json={"name": "Anita"})
    assert res.status_code == 200
    assert res.json()["name"] == "Anita"


def test_update_member_is_active(client):
    res = client.patch("/api/members/1", json={"is_active": False})
    assert res.status_code == 200
    assert res.json()["is_active"] is False


def test_update_member_not_found(client):
    assert client.patch("/api/members/999", json={"name": "x"}).status_code == 404


def test_update_member_blank_name(client):
    assert client.patch("/api/members/1", json={"name": " "}).status_code == 422


def test_delete_member(client):
    created = client.post("/api/members", json={"name": "Sara"}).json()
    res = client.delete(f"/api/members/{created['id']}")
    assert res.status_code == 200
    assert res.json() == {"ok": True}
    names = [m["name"] for m in client.get("/api/members").json()]
    assert "Sara" not in names


def test_delete_member_not_found(client):
    assert client.delete("/api/members/999").status_code == 404


def test_delete_member_in_use_return_409(client):
    client.post(
        "/api/expenses",
        json={
            "description": "Alquiler",
            "amount_cents": 9000,
            "paid_by": 1,
            "date": "2026-09-01",
            "category_id": 1,
            "split_mode": "equal",
            "shares": [
                {"member_id": 1, "share_cents": 3000},
                {"member_id": 2, "share_cents": 3000},
                {"member_id": 3, "share_cents": 3000},
            ],
        },
    )
    res = client.delete("/api/members/1")
    assert res.status_code == 409