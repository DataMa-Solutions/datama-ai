## Datama AI

Technical documentation for the `datama-ai` project.

This project is a small **Streamlit** application that runs a Datama AI locally. It integrates with **OpenAI** and **Datama Light** to build and execute analytical workflows based on user data.

The main entrypoint is `app.py`. The `run.sh` script is a thin wrapper that manages the Python virtual environment and starts Streamlit.

---

## Prerequisites

- **Python 3.10+** (recommended)
- OpenAI API key exposed as an environment variable or via a `.env` file

---

## Project layout

- `app.py` – main Streamlit application.
- `run.sh` – shell script to manage the virtual environment and run Streamlit.
- `requirements.txt` – Python dependencies (Streamlit, OpenAI, gspread, google-auth, python-dotenv, etc.).
- `light_runner/` – integration with the **Datama Light runner** (iframe, GCS URLs, remote prompts).
- `sources/` – data source configuration.
- `prompts/` – LLM prompt configuration.

---

## Installation

From the `datama-ai` directory:

Create and activate a virtual environment (optional if you rely on `run.sh`, which will create `.venv` automatically if missing):

```bash
python3 -m venv .venv
. .venv/bin/activate
```

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

---

## Configuration

The application expects your OpenAI key (and any other required secrets) to be available as environment variables or via a `.env` file at the project root.

Example `.env`:

```bash
OPENAI_API_KEY=sk-...
```

Make sure any external data sources (e.g. Google Sheets) referenced by your configuration are reachable and properly authorized.

---

## Running the application

Preferred way (uses `run.sh`):

```bash
./run.sh
```

`run.sh` will:

- create `.venv` if it does not exist,
- install dependencies from `requirements.txt` when the venv is created,
- activate `.venv`,
- start Streamlit with `app.py`.

### Port handling

- You can override or complement this with explicit Streamlit flags:

  ```bash
  ./run.sh --server.port 8503 --server.address 0.0.0.0
  ```

`run.sh` forwards any extra arguments to `streamlit run app.py`.

### Manual run

You can bypass `run.sh` and run Streamlit directly (after activating your venv):

```bash
streamlit run app.py
```

---

## Troubleshooting

- **`run.sh` fails during dependency installation**

  Check that `python3` and `pip` are available:

  ```bash
  python3 --version
  python3 -m pip --version
  ```

- **Streamlit does not start / port already in use**

  Try a different port:

  ```bash
  ./run.sh --server.port 8503
  ```

- **OpenAI API key errors**

  Ensure `OPENAI_API_KEY` is correctly set in your environment (or `.env`) before starting the app.

