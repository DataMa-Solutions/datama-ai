"""Agent orchestration: LLM with tools; if fetch_datas used, build conf + dataset for Light, else chat."""

import json
from agent.llm import call_llm, parse_json_from_response
from agent.validator import validate_compare_payload

_ROUTER_SYSTEM_PROMPT = """\
You are a helpful data-analysis assistant for DataMa Compare.

## When to call the fetch_datas tool

1. **New data source URL in the LATEST user message**
   The user's most recent message contains a spreadsheet / data-source URL
   (e.g. Google Sheets, BigQuery, GA4…).
   → Call fetch_datas with that URL.

2. **User asks to regenerate / modify the graph with different options**
   The user says something like "regenerate with only these metrics",
   "change the dimensions", "redo the graph but filter on …", etc.
   There is NO new URL, but a previous URL exists in the conversation history.
   → Call fetch_datas with the most recent URL found in earlier user messages.

## When NOT to call the tool

3. **User asks about the current graph / data**
   Questions such as "what are the metrics?", "which dimensions are used?",
   "explain the last graph", etc.
   The conversation already contains the dataset configuration
   (look for `[DataMa Configuration]` blocks in assistant messages).
   → Answer directly using that configuration. Do NOT re-fetch.

4. **General / unrelated question**
   The message has nothing to do with fetching data (greetings, general
   knowledge, help request…).
   → Answer normally without calling any tool.

## Important rules
- NEVER call fetch_datas just because a URL appears in an older message.
  Only call it when rule 1 or 2 applies.
- When answering about the current dataset (rule 3), refer to the
  `[DataMa Configuration]` block present in the conversation: it contains
  dimensions, metrics, steps, inputs, and configuration.
- Always reply in the same language the user writes in.
"""


def _history_to_input_messages(history: list[dict], new_message: str) -> list[dict]:
    """Build API input list from chat history and the new user message."""
    messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role not in ("user", "assistant", "system"):
            continue

        if role == "assistant":
            payload = msg.get("payload") or {}
            conf = payload.get("conf")
            if conf is not None:
                conf_block = (
                    "\n\n[DataMa Configuration]\n"
                    f"dimensions: {json.dumps(conf.get('dimensions', []))}\n"
                    f"metrics: {json.dumps(conf.get('metrics', []))}\n"
                    f"steps: {json.dumps(conf.get('steps', []))}\n"
                    f"inputs: {json.dumps(conf.get('inputs', {}))}\n"
                    f"configuration: {json.dumps(conf.get('configuration', {}))}\n"
                    "[/DataMa Configuration]"
                )
                content += conf_block

        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": new_message})
    return messages


def run(message: str, history: list[dict] | None = None) -> dict:
    """
    Run the agent: accept any prompt, use history for context. The LLM decides whether
    to answer directly or to call fetch_datas. If fetch_datas is used, call_llm handles
    the tool and the config step (INSTRUCTION_URL); we then validate and return payload.

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
            "message": "Posez une question ou donnez une URL de feuille pour afficher une vue Compare.",
            "payload": None,
            "error": None,
        }

    input_messages = _history_to_input_messages(history, message)

    try:
        response_text, raw_rows = call_llm(
            instructions=_ROUTER_SYSTEM_PROMPT,
            input_messages=input_messages,
            use_tools=True,
        )
    except Exception as e:
        return {
            "message": f"LLM call failed: {e}. Check OPENAI_API_KEY.",
            "payload": None,
            "error": str(e),
        }

    # No tool was used: return assistant text only
    if raw_rows is None:
        return {
            "message": response_text or "",
            "payload": None,
            "error": None,
        }

    # fetch_datas was used: response_text is the config JSON from INSTRUCTION_URL step
    if not raw_rows:
        return {
            "message": "The sheet appears to be empty or has no data rows.",
            "payload": None,
            "error": None,
        }
    payload = parse_json_from_response(response_text)
    if not payload:
        return {
            "message": "I could not parse a valid JSON payload from the model. Please try again or simplify the sheet.",
            "payload": None,
            "error": "JSON parse failed",
        }

    metrics = payload.get("metrics")
    inputs = payload.get("inputs") or {}
    if metrics and "metricForClustering" not in inputs:
        inputs["metricForClustering"] = metrics[-1]
        payload["inputs"] = inputs

    payload["dataset"] = raw_rows
    validation_errors = validate_compare_payload(payload)
    if validation_errors:
        return {
            "message": "The generated configuration has issues:\n- "
            + "\n- ".join(validation_errors),
            "payload": None,
            "error": "; ".join(validation_errors),
        }

    conf = {
        "dimensions": payload.get("dimensions", []),
        "metrics": payload.get("metrics", []),
        "steps": payload.get("steps", []),
        "inputs": payload.get("inputs", {}),
        "configuration": payload.get("configuration", {}),
    }
    dataset = payload.get("dataset", [])

    return {
        "message": "Here is your Compare view.",
        "payload": {"dataset": dataset, "conf": conf},
        "error": None,
    }
