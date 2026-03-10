"""LLM client for the agent (OpenAI or configurable provider)."""

import json
import os
from datetime import date
from urllib.request import urlopen

import openai
from openai.types.responses import Response
from sources import fetch_data

from light_runner.meta_builder import get_meta_from_dataset, meta_to_csv
from light_runner.urls import INSTRUCTION_URL


def fetch_datas(source_kind: str, url: str) -> tuple[str, list[dict]]:
    """
    Fetch data from the given source. source_kind must match a SourceKind (e.g. google_sheet, ga4).
    Returns (meta_csv, rows) on success, or raises on failure.
    """
    url = (url or "").strip()
    if not url:
        raise ValueError("URL is required.")
    source_kind = (source_kind or "").strip()
    if not source_kind:
        raise ValueError("source_kind is required (e.g. google_sheet).")
    rows = fetch_data(source_kind, url)
    if not rows:
        raise ValueError("The sheet appears to be empty or has no data rows.")
    meta = get_meta_from_dataset(rows, order="desc")
    return meta, rows


def get_client():
    """Return configured OpenAI client (or compatible)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set.")
    return openai.OpenAI(api_key=api_key)


def get_tools():
    return [
        {
            "type": "function",
            "name": "fetch_datas",
            "description": "Fetch data from a supported source using its URL. Use source_kind to select the provider: google_sheet, ga4, bigquery, metabase (see SourceKind). Use when the user provides a spreadsheet or data source link. Returns row count, column names, and a short preview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_kind": {
                        "type": "string",
                        "description": "Determines which provider is used to fetch the data.",
                        "enum": ["google_sheet"],
                    },
                    "url": {
                        "type": "string",
                        "description": "Full URL of the data source (e.g. https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit for Google Sheet). Must be public or shared with link when applicable.",
                    },
                },
                "required": ["source_kind", "url"],
            },
        }
    ]


def _load_instruction_url() -> str:
    """Load instructions from INSTRUCTION_URL."""
    try:
        with urlopen(INSTRUCTION_URL, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return ""


def _last_user_content(input_messages: list[dict]) -> str:
    """Extract the last user message content from a list of messages."""
    for item in reversed(input_messages):
        role = (
            item.get("role") if isinstance(item, dict) else getattr(item, "role", None)
        )
        content = (
            item.get("content")
            if isinstance(item, dict)
            else getattr(item, "content", "")
        )
        if role == "user":
            return content if isinstance(content, str) else ""
    return ""


def call_llm(
    *,
    instructions: str,
    input_messages: str | list[dict],
    use_tools: bool = False,
    model: str | None = None,
) -> tuple[str, list | None]:
    """
    Single LLM entry point: instructions, input (string or list of messages), and use_tools.

    - If use_tools is False: call the API without tools, return (assistant_text, None).
    - If use_tools is True: pass the fetch_datas tool. If the response is a tool call
      (fetch_datas), execute it, append the result to the conversation, then recall
      call_llm with instructions from INSTRUCTION_URL (config step, no tools) and
      return (config_json_text, raw_rows). If the response is not a tool call,
      return (assistant_text, None).
    """
    client = get_client()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    input_param = input_messages

    kwargs = {
        "model": model,
        "instructions": instructions,
        "input": input_param,
        "temperature": 0.2,
    }
    if use_tools:
        kwargs["tools"] = get_tools()

    response: Response = client.responses.create(**kwargs)

    # No tool call: return text and no raw_rows
    output_list = response.output or []
    function_call_item = None
    for item in output_list:
        if item.type != "function_call":
            continue
        function_call_item = item
        break

    if function_call_item is None:
        text = (response.output_text or "").strip()
        return (text, None)

    meta_csv = None
    if function_call_item.name == "fetch_datas":
        meta, dataset = fetch_datas(**(json.loads(function_call_item.arguments)))

    meta_csv = meta_to_csv(meta, max_unique_per_col=50)

    if meta_csv is None:
        raise RuntimeError("Error: Meta CSV is None.")

    # Build updated messages: previous input + assistant output (with tool call) + tool output
    messages = list(input_param)
    output_list.append(
        {
            "type": "function_call_output",
            "call_id": function_call_item.call_id,
            "output": str(meta_csv),
        }
    )
    messages.extend(output_list)
    today_str = date.today().strftime("%Y-%m-%d")

    # Reload instructions from INSTRUCTION_URL and build config user message (meta + prompt)
    config_instructions = _load_instruction_url() + f"""
        Today is {today_str}.

        Metadata (meta) for the dataset is below in a CSV block. One row per column: column, type, format, n_unique, unique_values (pipe-separated, truncated). Use this to choose dimensions (categorical/date columns), metrics (numeric columns), and build the Compare config. Do NOT include "dataset" or "meta" in your output; we already have the data and meta.
        ```csv
        {meta_csv}
        ```
        """

    config_text, _ = call_llm(
        instructions=config_instructions,
        input_messages=messages,
        use_tools=False,
        model=model,
    )
    return (config_text, dataset)


def parse_json_from_response(text: str) -> dict | None:
    """Extract a single JSON object from the model response (handles markdown code blocks)."""
    text = (text or "").strip()
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None
