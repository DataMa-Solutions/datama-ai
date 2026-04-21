---
name: Datama Compare
description: Generates an interactive Datama Compare visualization (variance decomposition / waterfall) as an HTML Artifact. Use when the user wants to understand why a KPI changed between two periods or segments, decompose variance (mix / price / volume / rate effects), compare groups, or build a waterfall chart. Typical triggers include "why did sessions drop", "compare Q1 vs Q2", "decompose revenue change", "analyze variance on X", "what explains the delta in Y".
---

# Datama Compare Skill

Produces a **Claude Artifact** that renders the Datama Compare visualization — an interactive variance decomposition / waterfall — by embedding the public Datama Light runner in an iframe and pushing the dataset and configuration to it via `postMessage`.

All rendering happens in the user's browser. The user's data never leaves the Claude session. The only outbound call to Datama is an optional license validation that sends the license key (no dataset).

## Workflow

When this skill is triggered, proceed in order:

1. **Get the dataset.** The dataset is a tabular structure (list of row objects) from whatever source the user has made available: a connector you can call (Google Sheets, BigQuery, …), an uploaded CSV / XLSX file, or data pasted in the conversation. If the raw data is larger than ~20 000 rows or would blow the Artifact size limit, aggregate it along the requested dimensions *before* continuing.

2. **Read the license key if present.** Look in the project's attached files / knowledge for a file named exactly `license.txt`. If it exists, read its content, trim whitespace, and keep it as `LICENSE_KEY`. If not present, proceed without — the runner falls back to the free tier.

3. **Derive column metadata** from the dataset: for each column, determine its name, its inferred type (`dimension` for strings/dates, `metric` for numerics), and a few distinct values for text columns. This is the input the Compare instructions expect.

4. **Build the Compare `configuration`** by strictly following `compare-instructions.md` (bundled next to this file). That file is the canonical Datama specification — do not deviate from it, do not invent keys. The configuration must contain exactly: `dimensions`, `metrics`, `steps`, `inputs`, and `configuration`.

5. **Emit the Artifact.** Produce a single Artifact of type `text/html` using the exact pattern in `artifact-template.html`. Replace the three placeholders:
   - `__DATASET__` → the dataset as a JSON array
   - `__CONFIGURATION__` → the `configuration` object as JSON
   - `__LICENSE_KEY__` → the license key as a JSON string, or `null` if none

   Keep the iframe `src` unchanged. Do not add external scripts. Do not reimplement Compare logic yourself.

## Rules

- **Never** change the iframe `src`. The runner must load from `https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest/compare/runner.ai-toolkit.html`.
- **Never** rebuild the visualization in plain JS or React — always go through the iframe runner.
- **Never** send dataset rows to any URL. Only the iframe receives the data (via `postMessage` on the same page), and the runner keeps it in the browser.
- The Artifact must be valid standalone HTML (no external resources beyond the iframe).
- If the dataset doesn't fit the schema in `compare-instructions.md`, normalize column names and types first — do not fabricate missing columns.
- If data or configuration cannot be produced (missing metrics, unclear comparison axis), ask the user a clarifying question *before* emitting the Artifact — an empty Artifact is worse than no Artifact.

## Files

- `compare-instructions.md` — canonical Datama Compare specification (data schema, configuration schema, market-equation rules). This is the source of truth, kept in sync with Datama's public CDN via `scripts/sync-instructions.sh`.
- `artifact-template.html` — exact HTML template to emit as the Artifact.

## Reference

- Runner URL: `https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest/compare/runner.ai-toolkit.html`
- `postMessage` contract: `{ type: "datama-light-payload", dataset, configuration, userLicenseKey? }`
