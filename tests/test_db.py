from sqlalchemy import text

from app.config import Settings
from app.db import make_engine


def test_database_url_defaults_to_local_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert Settings(_env_file=None).database_url == "sqlite:///./storyboard.db"


def test_sqlite_engine_enables_foreign_keys():
    engine = make_engine("sqlite://")

    with engine.connect() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_postgres_engine_gets_no_sqlite_options():
    # Creating an engine does not connect, so no Postgres server is needed here.
    engine = make_engine("postgresql+psycopg://user:pass@localhost:5432/storyboard")

    assert engine.dialect.name == "postgresql"
    assert engine.pool._pre_ping is True
