# Light Runner (iframe integration)

Datama visualizations are rendered by **DataMaLight** in the browser. This app embeds them via an **iframe** that loads the toolkit runner page and sends the payload via `postMessage`.

## URLs (`light_runner/urls.py`)

Both URLs are defined in `light_runner/urls.py` and re-exported by `light_runner` for use elsewhere.

### Runner URL

The runner HTML is loaded from GCS:

- **RUNNER_URL**: `https://storage.googleapis.com/app2.datama.io/artificial-intelligence/tools/runner.html`

Used by `build_embed_html()` to set the iframe `src`. The runner listens for `postMessage`, reads `solution` (`compare` or `explore`), then renders the corresponding Datama view.

### Instruction URLs (prompts)

The LLM configuration prompts are loaded from GCS:

- **INSTRUCTION_COMPARE_URL**: `https://storage.googleapis.com/app2.datama.io/artificial-intelligence/tools/compare/compare-instructions.md`
- **INSTRUCTION_EXPLORE_URL**: `https://storage.googleapis.com/app2.datama.io/artificial-intelligence/tools/explore/explore-instructions.md`

`agent/llm.py` selects the instruction URL from the target solution (`compare` or `explore`) and applies the corresponding input schema.

## Payload

When the agent returns a payload (`dataset` + `conf` + `solution`), the chat renders an iframe with `build_embed_html(dataset, conf, solution)` that loads `RUNNER_URL` and sends `{ type: 'datama-light-payload', solution, dataset, configuration, userLicenseKey }` via `postMessage`. The runner loads the corresponding jsdelivr bundle and calls `DataMaLight.render(...)`.
