import json
import logging
import time

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.schemas import BriefCreate, BriefResult, Storyboard
from app.services.base import GeneratorError

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """\
You are a creative director who writes storyboards for short video ads.

Rules:
- Write every "visual" and "narration" in the SAME language as the brief
  (product name and audience).
- Produce between 3 and 6 scenes, with "order" numbered 1..N in sequence,
  no gaps and no repeats.
- Each scene's "duration_seconds" is a positive integer, and the sum over all
  scenes must be EXACTLY the brief's duration_seconds.
- Match the brief's tone (casual, professional, emotional or urgent) in both
  the visuals and the narration.
- "visual" describes what is on screen; "narration" is the voice-over line.
Answer only with JSON that matches the given schema.
"""

STORYBOARD_JSON_SCHEMA = Storyboard.model_json_schema()

MAX_ATTEMPTS = 2  # first call + one retry with the validation error as feedback


class GeminiGenerator:
    """Storyboard generator backed by the Gemini API (google-genai SDK)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        client: genai.Client | None = None,
    ) -> None:
        self.model = model
        # Retries are disabled in the SDK: rate limits and timeouts surface
        # immediately as "unavailable" instead of multiplying the latency.
        self._client = client or genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(timeout_seconds * 1000),  # SDK expects milliseconds
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    def generate(self, brief: BriefCreate) -> Storyboard:
        prompt = _build_prompt(brief)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            text = self._call(prompt, attempt)
            try:
                candidate = Storyboard.model_validate_json(text)
                # Reuse the BriefResult validator for the duration-sum rule.
                BriefResult(brief=brief, storyboard=candidate)
                return candidate
            except ValidationError as exc:
                logger.warning(
                    "Gemini output failed validation (model=%s, attempt=%d/%d): %s",
                    self.model, attempt, MAX_ATTEMPTS, _summarize(exc),
                )
                prompt = _build_prompt(brief, previous_error=_summarize(exc))
        raise GeneratorError("invalid_output", "Gemini output failed validation twice")

    def _call(self, prompt: str, attempt: int) -> str:
        started = time.perf_counter()
        outcome = "ok"
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_json_schema=STORYBOARD_JSON_SCHEMA,
                ),
            )
        except errors.APIError as exc:
            outcome = f"api_error_{exc.code}"
            if exc.code == 429 or exc.code >= 500:
                raise GeneratorError("unavailable", f"Gemini API returned {exc.code}") from exc
            raise
        except httpx.TransportError as exc:  # timeouts, connection and network errors
            outcome = type(exc).__name__
            raise GeneratorError("unavailable", f"Gemini request failed: {outcome}") from exc
        finally:
            logger.info(
                "Gemini call model=%s attempt=%d outcome=%s latency_ms=%.0f",
                self.model, attempt, outcome, (time.perf_counter() - started) * 1000,
            )
        # text is None when the model returns no text (e.g. a blocked response);
        # treat it as invalid output so it goes through the retry path.
        return response.text or ""


def _build_prompt(brief: BriefCreate, previous_error: str | None = None) -> str:
    prompt = "Write a storyboard for this brief:\n" + json.dumps(
        brief.model_dump(), ensure_ascii=False, indent=2
    )
    if previous_error:
        prompt += (
            "\n\nYour previous answer was rejected by validation with this error:\n"
            f"{previous_error}\n"
            "Fix it and answer again, following every rule."
        )
    return prompt


def _summarize(exc: ValidationError) -> str:
    return "; ".join(err["msg"] for err in exc.errors(include_url=False))
