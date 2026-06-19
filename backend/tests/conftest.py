import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["MLFLOW_TRACKING_URI"] = "file:///tmp/mlruns"
os.environ["USE_REAL_DATASET"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_cache
from app.database import SessionLocal, init_db
from app.main import app


class FakeCache:
    def __init__(self) -> None:
        self.store = {}

    def get_json(self, key):
        return self.store.get(key)

    def set_json(self, key, value, ttl_seconds=3600):
        self.store[key] = value

    def get_or_set(self, key, factory, ttl_seconds=3600):
        if key not in self.store:
            self.store[key] = factory()
        return self.store[key]


@pytest.fixture(scope="session", autouse=True)
def database():
    init_db()


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def fake_cache():
    return FakeCache()


@pytest.fixture()
def client(fake_cache):
    app.dependency_overrides[get_cache] = lambda: fake_cache
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
