from typing import Literal, Protocol

from app.schemas import BriefCreate, Storyboard

GeneratorErrorKind = Literal["invalid_output", "unavailable"]


class GeneratorError(Exception):
    """Raised by a generator when it cannot produce a valid storyboard.

    kind="invalid_output": the generator answered, but its output failed validation.
    kind="unavailable": the generator could not be reached (rate limit, timeout, network).
    """

    def __init__(self, kind: GeneratorErrorKind, message: str = "") -> None:
        super().__init__(message or kind)
        self.kind = kind


class StoryboardGenerator(Protocol):
    def generate(self, brief: BriefCreate) -> Storyboard: ...
