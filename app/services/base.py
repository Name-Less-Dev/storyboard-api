from typing import Protocol

from app.schemas import BriefCreate, Storyboard


class StoryboardGenerator(Protocol):
    def generate(self, brief: BriefCreate) -> Storyboard: ...
