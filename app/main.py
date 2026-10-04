from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registers ORM tables on Base.metadata)
from app import repository
from app.db import Base, engine, get_db
from app.mappers import to_record, to_summary
from app.schemas import BriefCreate, BriefRecord, BriefResult, BriefSummary
from app.services.storyboard import generate_storyboard


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Schema migrations (Alembic) will replace this later.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Storyboard API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/briefs", response_model=BriefRecord, status_code=status.HTTP_201_CREATED)
def create_brief(brief: BriefCreate, db: Session = Depends(get_db)) -> BriefRecord:
    # Building BriefResult runs the duration-sum validator before anything is saved.
    result = BriefResult(brief=brief, storyboard=generate_storyboard(brief))
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
