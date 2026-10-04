import json
from types import SimpleNamespace

import httpx
import pytest
from google.genai import errors

from app.schemas import Storyboard
from app.services.base import GeneratorError
from app.services.gemini import STORYBOARD_JSON_SCHEMA, SYSTEM_INSTRUCTION, GeminiGenerator
from tests.conftest import make_brief

MODEL = "test-model"


class FakeModels:
    """Stands in for client.models: replays queued outcomes, records every call."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


def make_generator(*outcomes) -> tuple[GeminiGenerator, FakeModels]:
    models = FakeModels(outcomes)
    generator = GeminiGenerator(
        api_key="test-key",
        model=MODEL,
        timeout_seconds=20,
        client=SimpleNamespace(models=models),
    )
    return generator, models


def storyboard_json(*durations: int) -> str:
    return json.dumps(
        {
            "scenes": [
                {"order": i, "duration_seconds": d, "visual": f"visual {i}", "narration": f"line {i}"}
                for i, d in enumerate(durations, start=1)
            ]
        }
    )


def test_valid_json_returns_storyboard():
    generator, models = make_generator(storyboard_json(5, 10, 10, 5))

    storyboard = generator.generate(make_brief(duration_seconds=30))

    assert isinstance(storyboard, Storyboard)
    assert [scene.duration_seconds for scene in storyboard.scenes] == [5, 10, 10, 5]
    assert len(models.calls) == 1


def test_request_asks_for_structured_json_output():
    generator, models = make_generator(storyboard_json(10, 10, 10))

    generator.generate(make_brief(product_name="Café Bom", duration_seconds=30))

    call = models.calls[0]
    assert call["model"] == MODEL
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_json_schema == STORYBOARD_JSON_SCHEMA
    assert call["config"].system_instruction == SYSTEM_INSTRUCTION
    assert "Café Bom" in call["contents"]


@pytest.mark.parametrize(
    "first_answer",
    [storyboard_json(6, 6, 7), "not json at all"],
    ids=["wrong_sum", "malformed_json"],
)
def test_invalid_first_answer_is_retried_once_with_the_error(first_answer):
    generator, models = make_generator(first_answer, storyboard_json(6, 7, 7))

    storyboard = generator.generate(make_brief(duration_seconds=20))

    assert sum(scene.duration_seconds for scene in storyboard.scenes) == 20
    assert len(models.calls) == 2
    retry_prompt = models.calls[1]["contents"]
    assert "rejected by validation" in retry_prompt
    assert retry_prompt.startswith(models.calls[0]["contents"])


def test_retry_prompt_includes_the_sum_error():
    generator, models = make_generator(storyboard_json(6, 6, 7), storyboard_json(6, 7, 7))

    generator.generate(make_brief(duration_seconds=20))

    assert "sum to 19s, expected 20s" in models.calls[1]["contents"]


def test_invalid_output_twice_raises_invalid_output():
    generator, models = make_generator(storyboard_json(6, 6, 7), storyboard_json(6, 6, 7))

    with pytest.raises(GeneratorError) as exc_info:
        generator.generate(make_brief(duration_seconds=20))

    assert exc_info.value.kind == "invalid_output"
    assert len(models.calls) == 2


def test_empty_response_text_counts_as_invalid_output():
    generator, models = make_generator(None, None)

    with pytest.raises(GeneratorError) as exc_info:
        generator.generate(make_brief(duration_seconds=20))

    assert exc_info.value.kind == "invalid_output"
    assert len(models.calls) == 2


@pytest.mark.parametrize(
    "error",
    [
        errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}}),
        errors.ServerError(503, {"error": {"code": 503, "status": "UNAVAILABLE"}}),
        httpx.ReadTimeout("timed out"),
        httpx.ConnectError("connection refused"),
    ],
    ids=["rate_limit_429", "server_503", "timeout", "network"],
)
def test_upstream_failure_raises_unavailable_without_retry(error):
    generator, models = make_generator(error)

    with pytest.raises(GeneratorError) as exc_info:
        generator.generate(make_brief(duration_seconds=20))

    assert exc_info.value.kind == "unavailable"
    assert len(models.calls) == 1


def test_logs_model_and_latency_but_never_the_api_key(caplog):
    generator, _ = make_generator(storyboard_json(10, 10, 10))

    with caplog.at_level("INFO", logger="app.services.gemini"):
        generator.generate(make_brief(duration_seconds=30))

    assert f"model={MODEL}" in caplog.text
    assert "latency_ms=" in caplog.text
    assert "test-key" not in caplog.text
