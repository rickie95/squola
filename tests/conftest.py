from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from squola import database
from squola.main import app
from squola.models import Base


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    test_engine = database.get_engine(f"sqlite:///{db_path}")
    test_session_factory = database.create_session_factory(test_engine)

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", test_session_factory)

    Base.metadata.create_all(bind=test_engine)
    with TestClient(app) as test_client:
        yield test_client
    test_engine.dispose()

