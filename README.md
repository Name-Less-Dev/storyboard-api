# storyboard-api

## Running

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (use `source .venv/bin/activate` on Linux/macOS)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use an in-memory SQLite database and never touch `storyboard.db`.
