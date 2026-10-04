# storyboard-api

## Running

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (use `source .venv/bin/activate` on Linux/macOS)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## Choosing the generator

Storyboards come from one of two generators, selected by the `GENERATOR` setting:

| `GENERATOR` | What it does | Needs a key? |
|---|---|---|
| `fake` (default) | Deterministic template: 3 scenes, no network | No |
| `llm` | Google Gemini via the `google-genai` SDK, structured JSON output | Yes |

The default is `fake`, so the API runs out of the box with no key and no network.

To use Gemini:

1. Create a free API key in Google AI Studio: https://aistudio.google.com/apikey
2. Copy `.env.example` to `.env` and fill it in:
   ```bash
   cp .env.example .env
   ```
   ```dotenv
   GENERATOR=llm
   GEMINI_API_KEY=<your key>
   GEMINI_MODEL=gemini-3.5-flash-lite
   LLM_TIMEOUT_SECONDS=20
   ```
3. Restart the server. With `GENERATOR=llm` and no `GEMINI_API_KEY`, startup fails
   with a clear error.

`.env` is git-ignored; never commit it. Environment variables override `.env`.

If the model's output fails validation (bad JSON, scene durations that don't add up),
the generator retries once with the error in the prompt; if it fails again the API
answers `502`. Rate limits (429), timeouts and network errors answer `503`. Nothing is
saved in either case.

> **Free tier caveats.** Gemini free-tier limits (requests per minute/day, available
> models) vary and change over time, so expect occasional `503`s under load. Free-tier
> prompts may be used by Google to improve its products: **do not send confidential
> data from real campaigns** (unreleased products, client names, budgets) on the free tier.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use an in-memory SQLite database and never touch `storyboard.db`.
