import pytest

from app.services.storyboard import FakeGenerator
from tests.conftest import make_brief


@pytest.mark.parametrize("duration_seconds", range(15, 121))
def test_scene_durations_sum_to_brief_duration_and_are_numbered(duration_seconds):
    storyboard = FakeGenerator().generate(make_brief(duration_seconds=duration_seconds))

    total = sum(scene.duration_seconds for scene in storyboard.scenes)
    assert total == duration_seconds, f"scenes sum to {total}s for a {duration_seconds}s brief"
    assert [scene.order for scene in storyboard.scenes] == [1, 2, 3]


def test_same_brief_generates_identical_storyboard():
    brief = make_brief(tone="emotional", duration_seconds=47)

    assert FakeGenerator().generate(brief) == FakeGenerator().generate(brief)
