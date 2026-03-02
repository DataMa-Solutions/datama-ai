"""Agent orchestration: detect source, fetch data, build conf + dataset via LLM, validate."""

import json
from urllib.request import urlopen

from agent.llm import call_llm, parse_json_from_response
from agent.validator import validate_compare_payload
from light_runner.urls import INSTRUCTION_URL
from sources import detect_source, fetch_data


def _load_prompt() -> str:
    """Load the agent system prompt from INSTRUCTION_URL."""
    try:
        with urlopen(INSTRUCTION_URL, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return ""


def run(message: str, history: list[dict] | None = None) -> dict:
    """
    Run the agent: detect source from message, fetch data, ask LLM to build
    dataset + conf for DataMaLight Compare, validate, and return a result for the chat.

    Returns:
        {
            "message": str,       # Assistant text to show
            "payload": dict | None  # If success: { "dataset", "conf" } for iframe/runner
            "error": str | None    # If failure: error message
        }
    """
    history = history or []
    message = (message or "").strip()
    if not message:
        return {
            "message": "Please send a Google Sheet URL (or paste the URL of a public spreadsheet) and, if you like, a short instruction (e.g. compare January vs February).",
            "payload": None,
            "error": None,
        }

    # 1) Detect source and extract URL
    source_kind = detect_source(message)
    if not source_kind:
        return {
            "message": "I could not detect a supported data source from your message. For now, please provide a **Google Sheet** URL (e.g. `https://docs.google.com/spreadsheets/d/...`). Later we will support GA4, Big Query, Metabase.",
            "payload": None,
            "error": None,
        }

    url_or_id = message
    for word in message.split():
        if "http" in word or "docs.google.com" in word or len(word) > 40:
            url_or_id = word.strip()
            break

    # 2) Fetch raw data
    try:
        raw_rows = fetch_data(source_kind, url_or_id)
    except Exception as e:
        return {
            "message": f"Failed to fetch data from the source: {e!s}. Check that the sheet is public (Anyone with the link can view) or that credentials are set.",
            "payload": None,
            "error": str(e),
        }

    if not raw_rows:
        return {
            "message": "The sheet appears to be empty or has no data rows.",
            "payload": None,
            "error": None,
        }

    # 3) Load prompt and build user message for LLM
    instructions = _load_prompt()
    if not instructions:
        return {
            "message": f"Agent misconfiguration: could not load instructions from {INSTRUCTION_URL}.",
            "payload": None,
            "error": "Missing prompt file",
        }

    data_preview = json.dumps(raw_rows[:80], indent=2)
    if len(raw_rows) > 80:
        data_preview += f"\n... and {len(raw_rows) - 80} more rows."

    user_content = f"""The user provided this data source and message:
Message: {message}

Raw data (sample rows). Use this to infer column names, dimensions (categorical/date columns), metrics (numeric columns), and build meta (type and unique values per column). Do NOT include a "dataset" key in your output; we already have the data.
{data_preview}

Build a JSON object with keys: dimensions, metrics, steps, meta, inputs, configuration, smart. Output only this single JSON object (no markdown, no explanation). Ensure inputs.context is one of dimensions; inputs.start and inputs.end are arrays (indices into meta[context].unique if relative, or values). Steps must reference only metric names from metrics."""

    # 4) Call LLM
    try:
        response_text = call_llm(instructions, user_content)
    except Exception as e:
        return {
            "message": f"LLM call failed: {e!s}. Check OPENAI_API_KEY.",
            "payload": None,
            "error": str(e),
        }

    # 5) Parse JSON
    payload = parse_json_from_response(response_text)
    if not payload:
        return {
            "message": "I could not parse a valid JSON payload from the model. Please try again or simplify the sheet.",
            "payload": None,
            "error": "JSON parse failed",
        }

    # 6) Attach our fetched dataset (we did not ask LLM to return it)
    payload["dataset"] = raw_rows

    # 7) Validate
    validation_errors = validate_compare_payload(payload)
    if validation_errors:
        return {
            "message": "The generated configuration has issues:\n- "
            + "\n- ".join(validation_errors),
            "payload": None,
            "error": "; ".join(validation_errors),
        }

    # 8) Normalize for Light: ensure conf has all keys Light expects
    dataset = payload.get("dataset", [])
    conf = {
        "dimensions": payload.get("dimensions", []),
        "metrics": payload.get("metrics", []),
        "steps": payload.get("steps", []),
        "meta": payload.get("meta", {}),
        "inputs": payload.get("inputs", {}),
        "configuration": payload.get("configuration", {}),
        "smart": payload.get("smart", {"allow": False}),
    }

    return {
        "message": "Here is your DataMaLight Compare view. The configuration and dataset were generated from your sheet.",
        "payload": {"dataset": dataset, "conf": conf},
        "error": None,
    }
