from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Tone = Literal["casual", "professional", "emotional", "urgent"]


class BriefCreate(BaseModel):
    product_name: str = Field(min_length=2, max_length=80)
    audience: str = Field(min_length=2, max_length=120)
    tone: Tone
    duration_seconds: int = Field(ge=15, le=120)


class Scene(BaseModel):
    order: int = Field(ge=1)
    duration_seconds: int = Field(ge=1)
    visual: str
    narration: str


class Storyboard(BaseModel):
    scenes: list[Scene] = Field(min_length=1)

    @model_validator(mode="after")
    def check_scene_order(self) -> "Storyboard":
        orders = [scene.order for scene in self.scenes]
        expected = list(range(1, len(self.scenes) + 1))
        if orders != expected:
            raise ValueError(
                f"scenes must be numbered sequentially 1..{len(self.scenes)}, got {orders}"
            )
        return self


class BriefResult(BaseModel):
    brief: BriefCreate
    storyboard: Storyboard

    @model_validator(mode="after")
    def check_total_duration(self) -> "BriefResult":
        total = sum(scene.duration_seconds for scene in self.storyboard.scenes)
        if total != self.brief.duration_seconds:
            raise ValueError(
                f"scene durations sum to {total}s, expected {self.brief.duration_seconds}s"
            )
        return self


class BriefSummary(BaseModel):
    id: int
    product_name: str
    tone: Tone
    duration_seconds: int
    created_at: datetime


class BriefRecord(BaseModel):
    id: int
    created_at: datetime
    brief: BriefCreate
    storyboard: Storyboard
