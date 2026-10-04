import os
from collections.abc import Iterator

# Set before the app is imported (env vars take precedence over .env): no test may
# need an API key or the network, and the app engine never points at a real database.
os.environ["GENERATOR"] = "fake"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers ORM tables on Base.metadata)
from app.db import Base, get_db, make_engine, make_session_factory
from app.dependencies import get_generator
from app.main import app
from app.schemas import BriefCreate, BriefResult
from app.services.storyboard import FakeGenerator


@pytest.fixture
def db_session() -> Iterator[Session]:
    # In-memory SQLite with a single shared connection (StaticPool), built with the
    # same factory as the app so foreign keys are enforced here too.
    engine = make_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = make_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_generator] = FakeGenerator
    # Not used as a context manager on purpose: that would run the app lifespan,
    # which creates tables on the real storyboard.db engine.
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def make_brief(**overrides) -> BriefCreate:
    data = {
        "product_name": "Brew Box",
        "audience": "remote workers",
        "tone": "casual",
        "duration_seconds": 30,
    }
    return BriefCreate(**(data | overrides))


def make_result(**overrides) -> BriefResult:
    brief = make_brief(**overrides)
    return BriefResult(brief=brief, storyboard=FakeGenerator().generate(brief))
