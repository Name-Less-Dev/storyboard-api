# storyboard-api

## Running

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (use `source .venv/bin/activate` on Linux/macOS)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs.
