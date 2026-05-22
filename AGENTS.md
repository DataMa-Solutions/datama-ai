# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is a single-process Python/Streamlit app ("Datama AI") — a conversational analytics chat that uses OpenAI to produce waterfall visualizations via Datama Light. No database, no Docker, no build step.

### Running the app

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

Or use `./run.sh` which manages a `.venv` automatically.

### Required environment variable

- `OPENAI_API_KEY` — must be set (via `.env` or environment) for the chat/agent flow to work. Without it, the app starts but all LLM calls return an error.
- `OPENAI_MODEL` (optional) — defaults to `gpt-4o-mini`.

### Testing notes

- There is no automated test suite in this repo. Validation is manual: start the app, submit a prompt with a public Google Sheet URL, and verify the waterfall chart renders.
- Non-API components can be validated with a Python import check:
  ```bash
  python3 -c "from agent import run; from light_runner.iframe_html import build_embed_html; from app_header import render_app_header; print('OK')"
  ```
- The full flow requires outbound HTTPS access to: OpenAI API, `docs.google.com` (Sheet export), and `storage.googleapis.com` (Datama GCS bucket).

### Lint

No linter configuration is committed. You may run `ruff check .` or `flake8` if installed, but they are not part of the project's workflow.
