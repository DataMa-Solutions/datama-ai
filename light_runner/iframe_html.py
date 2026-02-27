"""Build iframe + postMessage HTML to embed the DataMaLight Compare runner."""

import json
import os


def get_runner_url() -> str:
    """Return the Light runner page URL (from env or Streamlit secrets)."""
    url = os.environ.get("LIGHT_RUNNER_URL", "").strip()
    if url:
        return url
    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None) or {}
        url = secrets.get("LIGHT_RUNNER_URL", "")
        if isinstance(url, str) and url.strip():
            return url.strip()
    except Exception:
        pass
    return "http://localhost:5500/light/src/utility/runner.compare.html"


def build_embed_html(runner_url: str, dataset: list, conf: dict) -> str:
    """
    Build an HTML string that contains an iframe and a script that posts the payload
    to the iframe once it has loaded. The runner page must be served from runner_url.
    """
    return f"""<div id="light-runner-wrap" style="width:100%; min-height:420px;">
<iframe id="light-runner-iframe" src="{runner_url}" style="width:100%; height:420px; border:1px solid #ddd; border-radius:6px;" title="DataMaLight Compare"></iframe>
<script>
(function() {{
  var iframe = document.getElementById("light-runner-iframe");
  var payload = {json.dumps({"type": "datama-light-payload", "dataset": dataset, "configuration": conf, "userLicenseKey": 'a2c2d6c'})};
  function send() {{
    try {{
      iframe.contentWindow.postMessage(payload, "*");
    }} catch (e) {{}}
  }}
  iframe.addEventListener("load", send);
  if (iframe.contentWindow) send();
}})();
</script>
</div>"""
