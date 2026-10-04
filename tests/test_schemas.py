import pytest
from pydantic import ValidationError

from app.schemas import BriefResult, Scene, Storyboard
from tests.conftest import make_brief


def scene(order: int, duration_seconds: int = 5) -> Scene:
    return Scene(
        order=order, duration_seconds=duration_seconds, visual="visual", narration="narration"
    )


def test_brief_create_accepts_valid_brief():
    brief = make_brief()

    assert brief.product_name == "Brew Box"
    assert brief.tone == "casual"
    assert brief.duration_seconds == 30


@pytest.mark.parametrize("duration_seconds", [14, 121, -5])
def test_brief_create_rejects_duration_outside_15_to_120(duration_seconds):
    with pytest.raises(ValidationError, match="duration_seconds"):
        make_brief(duration_seconds=duration_seconds)


def test_brief_create_rejects_unknown_tone():
    with pytest.raises(ValidationError, match="tone"):
        make_brief(tone="banana")


def test_brief_create_rejects_too_short_product_name():
    with pytest.raises(ValidationError, match="product_name"):
        make_brief(product_name="X")


def test_storyboard_rejects_gap_in_scene_numbering():
    with pytest.raises(ValidationError, match="numbered sequentially"):
        Storyboard(scenes=[scene(1), scene(3)])


def test_storyboard_rejects_repeated_scene_number():
    with pytest.raises(ValidationError, match="numbered sequentially"):
        Storyboard(scenes=[scene(1), scene(1)])


def test_brief_result_rejects_scene_durations_not_matching_brief():
    brief = make_brief(duration_seconds=20)
    storyboard = Storyboard(scenes=[scene(1, 6), scene(2, 6), scene(3, 7)])  # 19s

    with pytest.raises(ValidationError, match="sum to 19s, expected 20s"):
        BriefResult(brief=brief, storyboard=storyboard)
