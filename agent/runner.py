"""Agent orchestration: LLM with tools; build config + dataset for Datama, else chat."""

import json
from agent.llm import call_llm
from agent.prompts import ROUTER_SYSTEM_PROMPT
from agent.validator import validate_payload_for_solution


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
                content = json.dumps(
                    {
                        "message": content,
                        "solution": payload.get("solution", "compare"),
                        "configuration": {
                            "dimensions": conf.get("dimensions", []),
                            "metrics": conf.get("metrics", []),
                            "steps": conf.get("steps", []),
                            "inputs": conf.get("inputs", {}),
                            "configuration": conf.get("configuration", {}),
                        },
                    }
                )
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": new_message})
    return messages


def run(message: str, history: list[dict] | None = None) -> dict:
    """
    Run the agent: accept any prompt, use history for context. The LLM decides whether
    to answer directly or to call prepare_datama_context. If that tool is used, call_llm handles
    the tool and solution-specific config step; we then validate and return payload.

    Returns:
        {
            "message": str,       # Assistant text to show
            "payload": dict | None  # If success: { "dataset", "conf", "solution" } for iframe/runner
            "error": str | None    # If failure: error message
        }
    """
    history = history or []
    message = (message or "").strip()
    if not message:
        return {
            "message": "Posez une question ou donnez une URL de feuille pour afficher une vue Datama.",
            "payload": None,
            "error": None,
        }

    input_messages = _history_to_input_messages(history, message)

    try:
        response_text, raw_rows = call_llm(
            instructions=ROUTER_SYSTEM_PROMPT,
            input_messages=input_messages,
            use_tools=True,
        )
    except Exception as e:
        return {
            "message": f"LLM call failed: {e}. Check OPENAI_API_KEY.",
            "payload": None,
            "error": str(e),
        }

    # Parse response: always at least { "message": "..." }; with tool, also { "configuration": {...} }
    raw = (response_text or "").strip()
    try:
        obj = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        obj = None

    # No tool was used: use message from object or fallback to raw text
    if raw_rows is None:
        message = (obj.get("message") if isinstance(obj, dict) else None) or raw or ""
        return {
            "message": message,
            "payload": None,
            "error": None,
        }

    # Tool path was used: expect { "message", "configuration" } (and often "solution")
    if not raw_rows:
        return {
            "message": "The sheet appears to be empty or has no data rows.",
            "payload": None,
            "error": None,
        }
    if not isinstance(obj, dict) or "configuration" not in obj:
        return {
            "message": "I could not parse a valid response from the model (expected JSON with message and configuration). Please try again.",
            "payload": None,
            "error": "JSON parse failed",
        }

    conf_obj = obj["configuration"]
    if not isinstance(conf_obj, dict):
        return {
            "message": "Invalid configuration from the model.",
            "payload": None,
            "error": "configuration must be an object",
        }

    solution = "compare"
    if isinstance(obj, dict):
        raw_solution = str(obj.get("solution", "compare")).strip().lower()
        if raw_solution in ("compare", "explore"):
            solution = raw_solution

    metrics = conf_obj.get("metrics")
    inputs = conf_obj.get("inputs") or {}
    if solution == "compare" and metrics and "metricForClustering" not in inputs:
        inputs = {**inputs, "metricForClustering": metrics[-1]}
        conf_obj = {**conf_obj, "inputs": inputs}

    payload_for_validate = {**conf_obj, "dataset": raw_rows}
    validation_errors = validate_payload_for_solution(payload_for_validate, solution)
    if validation_errors:
        return {
            "message": "The generated configuration has issues:\n- "
            + "\n- ".join(validation_errors),
            "payload": None,
            "error": "; ".join(validation_errors),
        }

    conf = {
        "dimensions": conf_obj.get("dimensions", []),
        "metrics": conf_obj.get("metrics", []),
        "steps": conf_obj.get("steps", []),
        "inputs": conf_obj.get("inputs", {}),
        "configuration": conf_obj.get("configuration", {}),
    }

    return {
        "message": obj.get("message"),
        "payload": {"dataset": raw_rows, "conf": conf, "solution": solution},
        "error": None,
    }
