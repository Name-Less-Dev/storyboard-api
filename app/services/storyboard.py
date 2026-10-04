from app.schemas import BriefCreate, Scene, Storyboard

SCENE_COUNT = 3


def _split_duration(total: int, parts: int) -> list[int]:
    """Split total into equal parts; the last part absorbs the remainder."""
    base = total // parts
    durations = [base] * parts
    durations[-1] += total - base * parts
    return durations


class FakeGenerator:
    """Deterministic storyboard generator (no randomness, no network)."""

    def generate(self, brief: BriefCreate) -> Storyboard:
        opening, development, call_to_action = _split_duration(
            brief.duration_seconds, SCENE_COUNT
        )
        product, audience, tone = brief.product_name, brief.audience, brief.tone

        scenes = [
            Scene(
                order=1,
                duration_seconds=opening,
                visual=f"Opening shot introducing {product} with a {tone} look and feel.",
                narration=f"Hey {audience}, meet {product}.",
            ),
            Scene(
                order=2,
                duration_seconds=development,
                visual=f"{product} in use, showing how it fits the daily life of {audience}.",
                narration=f"See how {product} makes a difference for {audience}.",
            ),
            Scene(
                order=3,
                duration_seconds=call_to_action,
                visual=f"Close-up of {product} with logo and call-to-action on screen.",
                narration=f"Try {product} today.",
            ),
        ]
        return Storyboard(scenes=scenes)
