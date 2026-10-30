import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]

# Берём настройки подключения, но меняем название базы.
env = dotenv_values(ROOT / ".env")
database_url = make_url(env["DATABASE_URL"])
test_url = database_url.set(database="taskflow_test")

os.environ["DATABASE_URL"] = test_url.render_as_string(
    hide_password=False
)

# Импортируем приложение после выбора тестовой базы.
from app.database import engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    assert engine.url.database == "taskflow_test"

    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(ROOT / "alembic"),
    )
    command.upgrade(config, "head")

    yield

    engine.dispose()


@pytest.fixture()
def client(prepare_database):
    with engine.connect() as connection:
        transaction = connection.begin()

        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as session:

            def override_get_db():
                yield session

            app.dependency_overrides[get_db] = override_get_db

            try:
                with TestClient(app) as test_client:
                    yield test_client
            finally:
                app.dependency_overrides.pop(get_db, None)

        transaction.rollback()