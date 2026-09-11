import pytest
from fastapi.testclient import TestClient

from expense_splitter.main import app, get_store
from expense_splitter.store import MockStore, empty_seed


@pytest.fixture
def store():
    return MockStore(empty_seed())


@pytest.fixture
def client(store):
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()