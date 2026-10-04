from fastapi import FastAPI

from app.schemas import BriefCreate, BriefResult
from app.services.storyboard import generate_storyboard

app = FastAPI(title="Storyboard API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/briefs", response_model=BriefResult)
def create_brief(brief: BriefCreate) -> BriefResult:
    # 200 for now since nothing is persisted; becomes 201 once briefs are stored.
    storyboard = generate_storyboard(brief)
    return BriefResult(brief=brief, storyboard=storyboard)
