"""Build iframe + postMessage HTML to embed the DataMaLight Compare runner."""

import json

from light_runner.urls import RUNNER_URL


def build_embed_html(dataset: list, conf: dict) -> str:
    """
    Build an HTML string that contains an iframe and a script that posts the payload
    to the iframe once it has loaded. The iframe loads RUNNER_URL.

    Only call this when a valid payload (dataset + conf) is available; otherwise
    the DataMaLight runner would have no data and could crash. If dataset or conf
    is missing/empty, returns a minimal placeholder div without instantiating Light.
    """
    if not dataset or not conf:
        return '<div id="light-runner-wrap" style="width:100%; min-height:80px; padding:12px; color:#666;">Aucune donnée à afficher.</div>'
    runner_url = RUNNER_URL

    # ----- END REMOVABLE -----

    return f"""<div id="light-runner-wrap" style="width:100%; min-height:550px;">
<iframe id="light-runner-iframe" src="{runner_url}" style="width:100%; height:550px; border:1px solid #ddd; border-radius:6px;" title="DataMaLight Compare"></iframe>
<script>
(function() {{
  var iframe = document.getElementById("light-runner-iframe");
  var payload = {json.dumps({"type": "datama-light-payload", "dataset": dataset, "configuration": conf})};
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
