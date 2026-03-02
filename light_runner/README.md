# Light Runner (iframe integration)

The Compare visualization is rendered by **DataMaLight** in the browser. This app embeds it via an **iframe** that loads the runner page and sends the payload via `postMessage`.

## URLs (`light_runner/urls.py`)

Both URLs are defined in `light_runner/urls.py` and re-exported by `light_runner` for use elsewhere.

### Runner URL

The runner HTML is loaded from GCS:

- **RUNNER_URL**: `https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest/compare/runner.ai-toolkit.html`

Used by `build_embed_html()` to set the iframe `src`. The runner listens for `postMessage` and renders the visualization.

### Instruction URL (prompt)

The LLM system prompt is loaded from GCS:

- **INSTRUCTION_URL**: `https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest/compare/instruction-runner.ai-toolkit.md`

`agent/runner.py` fetches this URL at runtime via `_load_prompt()` and passes it as the system prompt to the LLM. The prompt describes how to build the JSON payload (dimensions, metrics, steps, meta, inputs, configuration, smart) from the user's data. If the fetch fails, the agent returns an error; there is no local fallback.

## Payload

When the agent returns a payload (dataset + conf), the chat renders an iframe with `build_embed_html(dataset, conf)` that loads `RUNNER_URL` and sends `{ type: 'datama-light-payload', dataset, configuration, userLicenseKey }` via `postMessage`. The runner instantiates DataMaLight Compare with that data.
