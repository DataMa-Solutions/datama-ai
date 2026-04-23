---
name: Datama Compare
description: Generates an interactive Datama Compare visualization (variance decomposition / waterfall) as an HTML Artifact. Use when the user wants to understand why a KPI changed between two periods or segments, decompose variance (mix / price / volume / rate effects), compare groups, or build a waterfall chart. Typical triggers include "why did sessions drop", "compare Q1 vs Q2", "decompose revenue change", "analyze variance on X", "what explains the delta in Y".
---

# Datama Compare Skill

Produces a **Claude Artifact** that renders the Datama Compare visualization — an interactive variance decomposition / waterfall — by loading the public Datama Light UMD bundle from a CDN (jsdelivr) and calling `DataMaLight.render(container, {source, configuration, license})` directly in the Artifact page.

All rendering happens in the user's browser. The user's data never leaves the Claude session. The only outbound calls from the Artifact are:
- the static JS/CSS fetch from `cdn.jsdelivr.net/npm/@datama/light` (the library code),
- optional license validation, which sends the JWT license key only (no dataset).

## Workflow

When this skill is triggered, proceed in order:

1. **Get the dataset.** The dataset is a tabular structure (list of row objects) from whatever source the user has made available: a connector you can call (Google Sheets, BigQuery, …), an uploaded CSV / XLSX file, or data pasted in the conversation. If the raw data is larger than ~20 000 rows or would blow the Artifact size limit, aggregate it along the requested dimensions *before* continuing.

   **Demo mode — no data provided.** If the user is clearly trying out the skill with no dataset available (phrasings like "try it", "test the skill", "show me a demo", "essaie", "un exemple", or the skill is triggered with no attached data and no data in the conversation), **do not ask for data**. Instead, synthesize a small realistic dataset yourself (~8–15 rows) and proceed straight through steps 2–5. The synthetic dataset must:
   - have **one comparison dimension** with exactly 2 distinct values (e.g. `period` = `Q1` / `Q2`, or `platform` = `iOS` / `Android`),
   - optionally have 1 extra breakdown dimension (e.g. `country`) with 3–5 distinct values,
   - expose **2–4 numeric metrics that form a business equation** compatible with the market-equation logic in `compare-instructions.md` — for example `quantity`, `revenue` with `revenue = quantity × price`,
   - produce a **non-trivial delta** between the two comparison values (don't make the two sides identical — the waterfall needs something to decompose).

   Announce in one short sentence that you're using a synthetic demo dataset, then emit the Artifact. Do not dump the dataset as a table in chat — it belongs in the Artifact.

2. **Read the license key if present.** Look in the project's attached files / knowledge for a file named exactly `license.txt`. If it exists, read its content, trim whitespace, and keep it as `LICENSE_KEY` (it is a JWT string). If not present, proceed without — the bundle falls back to the free tier.

3. **Derive column metadata** from the dataset: for each column, determine its name, its inferred type (`dimension` for strings/dates, `metric` for numerics), and a few distinct values for text columns. This is the input the Compare instructions expect.

4. **Build the Compare `configuration`** by strictly following `compare-instructions.md` (bundled next to this file). That file is the canonical Datama specification — do not deviate from it, do not invent keys. The configuration must contain exactly: `dimensions`, `metrics`, `steps`, `inputs`, and `configuration`.

5. **Emit the Artifact — do not just show the HTML.** The final reply must contain a real Claude Artifact of type `text/html` that renders in the Artifact panel. Do **not** paste the HTML into a fenced code block for the user to read, do **not** describe what the Artifact would look like, do **not** save it to a file and stop. The deliverable *is* the rendered visualization — if the user sees code instead of a waterfall, the skill has failed. Use the exact pattern in `artifact-template.html` and replace the three placeholders:
   - `__DATASET__` → the dataset as a JSON array
   - `__CONFIGURATION__` → the `configuration` object as JSON
   - `__LICENSE_KEY__` → the license key as a JSON string (quoted), or `null` if none

   Keep the `<link>` and `<script>` tags that point to `https://cdn.jsdelivr.net/npm/@datama/light@0.2.0/...` unchanged. Do not add external scripts beyond those. Do not reimplement Compare logic yourself. After emitting the Artifact, keep any accompanying chat text to one or two sentences — the Artifact speaks for itself.

## Rules

- **Never** change the CDN URLs. They must resolve to `https://cdn.jsdelivr.net/npm/@datama/light@0.2.0/dist/compare.umd.js` and `https://cdn.jsdelivr.net/npm/@datama/light@0.2.0/dist/compare.css`. The version is pinned to force cache invalidation — jsdelivr caches the "latest" pointer for up to 12h, so an unpinned URL can serve a stale build. jsdelivr is explicitly allowlisted by the Claude Artifact sandbox CSP. The `unpkg` mirror — `https://unpkg.com/@datama/light@0.2.0/dist/compare.umd.js` — serves the same file but is blocked in the inline Artifact iframe (it only works when the Artifact is popped out to a standalone window), so do not use it.
- **Never** rebuild the visualization in plain JS or React — always go through `window.DataMaLight.render`.
- **Never** send dataset rows to any URL. The bundle consumes the dataset in-page (passed as the `source` argument to `render`) and keeps it in the browser.
- The Artifact must be valid standalone HTML (the only external resources are the two CDN files above).
- If the dataset doesn't fit the schema in `compare-instructions.md`, normalize column names and types first — do not fabricate missing columns.
- If data or configuration cannot be produced (missing metrics, unclear comparison axis), ask the user a clarifying question *before* emitting the Artifact — an empty Artifact is worse than no Artifact.

## Files

- `compare-instructions.md` — canonical Datama Compare specification (data schema, configuration schema, market-equation rules). This is the source of truth, kept in sync with Datama's public CDN via `scripts/sync-instructions.sh`.
- `artifact-template.html` — exact HTML template to emit as the Artifact.

## Reference

- CDN bundle: `https://cdn.jsdelivr.net/npm/@datama/light@0.2.0/dist/compare.umd.js` (UMD, d3 included).
- CDN styles: `https://cdn.jsdelivr.net/npm/@datama/light@0.2.0/dist/compare.css`.
- Runtime API: `window.DataMaLight.render(containerOrSelector, { source, configuration, license })` — returns a `Promise<DataMaLight>`.
- The unpkg mirror (`https://unpkg.com/@datama/light@0.2.0/...`) serves the same file but is blocked in Claude's inline Artifact sandbox; do not reference it.
