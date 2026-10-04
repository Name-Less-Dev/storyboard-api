import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registers ORM tables on Base.metadata)
from app import repository
from app.config import get_settings
from app.db import Base, engine, get_db
from app.dependencies import get_generator
from app.mappers import to_record, to_summary
from app.schemas import BriefCreate, BriefRecord, BriefResult, BriefSummary
from app.services.base import StoryboardGenerator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Fail fast on invalid settings (e.g. GENERATOR=llm without GEMINI_API_KEY).
    get_settings()
    get_generator()
    # Schema migrations (Alembic) will replace this later.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Storyboard API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/briefs", response_model=BriefRecord, status_code=status.HTTP_201_CREATED)
def create_brief(
    brief: BriefCreate,
    db: Session = Depends(get_db),
    generator: StoryboardGenerator = Depends(get_generator),
) -> BriefRecord:
    # Building BriefResult runs the duration-sum validator before anything is saved.
    try:
        result = BriefResult(brief=brief, storyboard=generator.generate(brief))
    except ValidationError as exc:
        # The generator is an upstream service: invalid output is a 502, not a 4xx/500.
        logger.error("Generated storyboard failed validation: %s", exc.errors())
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Generated storyboard failed validation",
        ) from exc
    row = repository.create_brief(db, result)
    return to_record(row)


@app.get("/briefs", response_model=list[BriefSummary])
def list_briefs(db: Session = Depends(get_db)) -> list[BriefSummary]:
    return [to_summary(row) for row in repository.list_briefs(db)]


@app.get("/briefs/{brief_id}", response_model=BriefRecord)
def get_brief(brief_id: int, db: Session = Depends(get_db)) -> BriefRecord:
    row = repository.get_brief(db, brief_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    return to_record(row)
