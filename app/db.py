from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    # SQLite ignores FOREIGN KEY constraints unless enabled per connection.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_engine(url: str, **kwargs: Any) -> Engine:
    """Create an engine with the settings shared by the app and the tests.

    SQLite-only tweaks (thread check off, foreign keys on) are applied only when
    the URL is SQLite; other databases (Postgres) get a plain engine.
    """
    is_sqlite = make_url(url).get_backend_name() == "sqlite"
    if is_sqlite:
        # FastAPI runs sync routes in a thread pool, so a connection may be used by
        # a different thread than the one that opened it.
        kwargs.setdefault("connect_args", {"check_same_thread": False})
    else:
        # Drop dead connections (e.g. after a database restart) instead of failing.
        kwargs.setdefault("pool_pre_ping", True)
    engine = create_engine(url, **kwargs)
    if is_sqlite:
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


engine = make_engine(get_settings().database_url)
SessionLocal = make_session_factory(engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
