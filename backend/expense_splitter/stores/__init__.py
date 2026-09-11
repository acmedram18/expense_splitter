"""Store implementations and the factory that selects one.

The app default is the SQLAlchemy store on a local SQLite file. Set
``ENTRENOS_STORE=mock`` to use the in-memory mock (tests/dev only) and
``ENTRENOS_DB_URL`` to point SQLAlchemy at another engine.
"""

import os
from pathlib import Path

from .base import Store
from .memory import MockStore
from .seed import demo_seed, empty_seed
from .sql import SqlStore

_MOCK_DB_PATH = str(Path(__file__).resolve().parent.parent / "db_mock.json")
_SQLITE_DB_PATH = str(Path(__file__).resolve().parent.parent / "db.sqlite3")

__all__ = [
    "MockStore",
    "Store",
    "SqlStore",
    "build_store",
    "demo_seed",
    "empty_seed",
]


def build_store() -> Store:
    """Build the configured store. Defaults to SQLAlchemy on SQLite."""
    kind = os.environ.get("ENTRENOS_STORE", "sql")
    if kind == "mock":
        return MockStore(persist_path=_MOCK_DB_PATH)
    url = os.environ.get("ENTRENOS_DB_URL") or f"sqlite:///{_SQLITE_DB_PATH}"
    return SqlStore(url=url)