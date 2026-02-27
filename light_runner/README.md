# Light Runner (iframe integration)

The Compare visualization is rendered by **DataMaLight** in the browser. This app does not bundle Light; it embeds it via an **iframe** that points to a runner page served by the Light dev server.

## Setup

1. **Start the Light dev server** (from the `light` repo):
   ```bash
   cd /path/to/light
   npm run serve compare
   ```
   This serves the Light app (and the runner page) at `http://localhost:8089` by default.

2. **Configure the runner URL** in the Streamlit app:
   - Environment: `LIGHT_RUNNER_URL=http://localhost:8089/src/utility/runner.compare.html`
   - Or in Streamlit secrets: `LIGHT_RUNNER_URL: "http://localhost:8089/src/utility/runner.compare.html"`

3. When the agent returns a payload (dataset + conf), the chat will render an iframe that loads this URL and sends the payload via `postMessage`. The runner page (in the Light repo) listens for it and runs DataMaLight Compare.

## Runner page location

The actual runner page is in the **light** repo:

- `light/src/utility/runner.compare.html`

It listens for `postMessage` with `{ type: 'datama-light-payload', dataset, conf }` and instantiates DataMaLight with that data.
