import pytest
from fastapi.testclient import TestClient

from expense_splitter.main import app, get_store
from expense_splitter.stores import MockStore, SqlStore, empty_seed


@pytest.fixture(params=["mock", "sql"], ids=["mock", "sql"])
def store(request, tmp_path):
    if request.param == "mock":
        return MockStore(empty_seed())
    return SqlStore(url=f"sqlite:///{tmp_path / 'test.db'}", seed=empty_seed())


@pytest.fixture
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()