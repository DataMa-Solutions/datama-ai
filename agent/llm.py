"""LLM client for the agent (OpenAI or configurable provider)."""

import json
import os


def get_client():
    """Return configured OpenAI client (or compatible)."""
    try:
        import openai
    except ImportError as e:
        raise RuntimeError(
            "LLM support requires: pip install openai. "
            "Set OPENAI_API_KEY in env or in Streamlit secrets."
        ) from e
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st

            secrets = getattr(st, "secrets", None) or {}
            api_key = secrets.get("OPENAI_API_KEY") or secrets.get("openai", {}).get(
                "api_key"
            )
        except Exception:
            pass
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set (env or Streamlit secrets).")
    return openai.OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_message: str, model: str | None = None) -> str:
    """
    Call the LLM with system and user messages. Returns the assistant reply text.
    """
    client = get_client()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=user_message,
        temperature=0.2,
    )
    print(response)
    return (response.output_text or "").strip()


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
