"""Build iframe + postMessage HTML to embed the DataMaLight Compare runner."""

import json

from light_runner.urls import RUNNER_URL


def build_embed_html(dataset: list, conf: dict) -> str:
    """
    Build an HTML string that contains an iframe and a script that posts the payload
    to the iframe once it has loaded. The iframe loads RUNNER_URL.
    """
    runner_url = RUNNER_URL

    # ----- REMOVABLE: button to fetch RUNNER_URL (delete this block to remove) -----
    fetch_button_block = f"""
<div id="light-runner-fetch-block" style="margin-bottom:8px;">
  <button type="button" id="light-runner-fetch-btn" style="padding:6px 12px; font-size:14px; cursor:pointer; border:1px solid #ccc; border-radius:4px; background:#f5f5f5;">Fetch runner</button>
</div>
<script>
function initFetchBtn() {{
  var btn = document.getElementById("light-runner-fetch-btn");
  var iframe = document.getElementById("light-runner-iframe");
  if (btn && iframe) {{
    btn.addEventListener("click", function() {{
      iframe.src = {json.dumps(runner_url)};
    }});
  }}
}}
if (document.readyState === "loading") {{
  document.addEventListener("DOMContentLoaded", initFetchBtn);
}} else {{
  initFetchBtn();
}}
</script>
"""
    # ----- END REMOVABLE -----

    return f"""<div id="light-runner-wrap" style="width:100%; min-height:550px;">
{fetch_button_block}
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
