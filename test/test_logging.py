import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.main import app, engine


def test_log_level_from_environment(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert Settings(_env_file=None).log_level == "DEBUG"


def test_request_logs_do_not_include_query_parameters(client, caplog):
    with caplog.at_level(logging.DEBUG, logger="taskflow"):
        response = client.get("/health", params={"token": "private-value"})

    assert response.status_code == 200
    assert "GET /health -> 200" in caplog.messages
    assert "private-value" not in caplog.text


def test_conflict_emits_warning(client, caplog):
    data = {"name": "Проверка логов"}
    assert client.post("/v1/labels", json=data).status_code == 201
    assert client.post("/v1/labels", json=data).status_code == 409
    assert (
        "taskflow",
        logging.WARNING,
        "Database constraint conflict: labels",
    ) in caplog.record_tuples


def test_startup_database_failure_emits_critical(monkeypatch, caplog):
    def unavailable():
        raise OperationalError(None, None, ConnectionError())

    monkeypatch.setattr(engine, "connect", unavailable)
    with pytest.raises(OperationalError), TestClient(app):
        pass

    assert (
        "taskflow",
        logging.CRITICAL,
        "API startup failed: PostgreSQL is unavailable",
    ) in caplog.record_tuples
