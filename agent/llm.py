"""LLM client for the agent (OpenAI or configurable provider)."""

import json
import os
from datetime import date
from urllib.request import urlopen
from agent.tools import get_tools

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


def _load_instruction_url() -> str:
    """Load instructions from INSTRUCTION_URL."""
    try:
        with urlopen(INSTRUCTION_URL, timeout=10) as resp:
            return resp.read().decode("utf-8")
    except Exception:
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
    config_instructions = _load_instruction_url() + f"Today is {today_str}." ""

    config_text, _ = call_llm(
        instructions=config_instructions,
        input_messages=messages,
        use_tools=False,
        model=model,
    )
    return (config_text, dataset)
