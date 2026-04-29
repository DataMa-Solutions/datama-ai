---
name: Datama
description: Generates an interactive Datama visualization (Compare or Explore) as an HTML Artifact. Compare = variance decomposition / waterfall — when the user wants to understand why a KPI changed between two periods or segments, decompose variance (mix / price / volume / rate effects), or compare groups. Explore = breakdown / slicing — when the user wants to plot a metric across one or two dimensions, see how a KPI is distributed, or slice and dice without a binary comparison. Typical Compare triggers include "why did sessions drop", "compare Q1 vs Q2", "decompose revenue change", "what explains the delta in Y". Typical Explore triggers include "break down revenue by country", "plot conversion by device and channel", "show distribution of X across Y", "explore the funnel".
---

# Datama Skill

Produces a **Claude Artifact** that renders a Datama visualization — either **Compare** (variance decomposition / waterfall) or **Explore** (breakdown / slicing) — by loading the public Datama Light UMD bundle from a CDN (jsdelivr) and calling `DataMaLight.render(container, {source, configuration, license})` directly in the Artifact page.

All rendering happens in the user's browser. The user's data never leaves the Claude session. The only outbound calls from the Artifact are:
- the static JS/CSS fetch from `cdn.jsdelivr.net/npm/@datama/light` (the library code),
- optional license validation, which sends the JWT license key only (no dataset).

## Workflow

When this skill is triggered, proceed in order:

1. **Get the dataset.** The dataset is a tabular structure (list of row objects) from whatever source the user has made available: a connector you can call (Google Sheets, BigQuery, …), an uploaded CSV / XLSX file, or data pasted in the conversation. If the raw data is larger than ~20 000 rows or would blow the Artifact size limit, aggregate it along the requested dimensions *before* continuing.

   **Demo mode — no data provided.** If the user is clearly trying out the skill with no dataset available (phrasings like "try it", "test the skill", "show me a demo", "essaie", "un exemple", or the skill is triggered with no attached data and no data in the conversation), **do not ask for data**. Instead, synthesize a small realistic dataset yourself (~8–15 rows). The synthetic dataset must:
   - have **2–4 numeric metrics** that form a business equation compatible with the market-equation logic;
   - for **Compare-style demos**, include exactly one comparison dimension with 2 distinct values and produce a non-trivial delta;
   - for **Explore-style demos**, include 2 dimensions with 2–5 distinct values each (e.g. `country` × `device`), and an optional binary comparison dimension for context.

   Announce in one short sentence that you're using a synthetic demo dataset, then **proceed straight through steps 2–6 and emit the Artifact in the same response**. Do not dump the dataset as a table in chat. Do not stop after the announcement — the user only sees value once the visualization renders, so a "demo" reply without an Artifact is a failed reply.

2. **Pick the solution.** Read the user request and decide which Datama solution to produce: `compare` or `explore`. Use the routing rules in the instruction file you load in step 4 (the `solution` field rules at the end of `compare-instructions.md` apply globally — `compare` > `explore` and fallback to `compare` when ambiguous).

   For `detect` and `assess`, this skill does **not** yet ship a configuration spec — fall back to `compare` and tell the user, in one short sentence, that those two solutions are coming soon.

3. **Read the license key if present.** Look in the project's attached files / knowledge for a file named exactly `license.txt`. If it exists, read its content, trim whitespace, and keep it as `LICENSE_KEY` (it is a JWT string). If not present, proceed without — the bundle falls back to the free tier.

4. **Derive column metadata** from the dataset: for each column, determine its name, its inferred type (`dimension` for strings/dates, `metric` for numerics), and a few distinct values for text columns. This is the input the instruction files expect.

5. **Build the `configuration`** by following the instruction file matching the solution chosen at step 2:
   - `solution = compare` → use `compare-instructions.md`
   - `solution = explore` → use `explore-instructions.md`

   Those files are the canonical Datama specification — do not deviate from them, do not invent keys. The configuration must contain exactly: `dimensions`, `metrics`, `steps`, `inputs`, and `configuration`. The `inputs` shape differs between the two solutions; honor the file you loaded.

6. **Emit the Artifact — do not just show the HTML.** The final reply must contain a real Claude Artifact of type `text/html` that renders in the Artifact panel. Do **not** paste the HTML into a fenced code block for the user to read, do **not** describe what the Artifact would look like, do **not** save it to a file and stop. The deliverable *is* the rendered visualization. Use the exact pattern in `artifact-template.html` and replace the four placeholders:
   - `__SOLUTION__` → the lowercase solution name, exactly `compare` or `explore`
   - `__DATASET__` → the dataset as a JSON array
   - `__CONFIGURATION__` → the `configuration` object as JSON
   - `__LICENSE_KEY__` → the license key as a JSON string (quoted), or `null` if none

   Keep the `<link>` and `<script>` tags pointing to `https://cdn.jsdelivr.net/npm/@datama/light@0.3.0/...` unchanged except for the `__SOLUTION__` substitution (`compare.umd.js` / `compare.css` or `explore.umd.js` / `explore.css`). Do not add external scripts beyond those. Do not reimplement Datama logic yourself. After emitting the Artifact, keep any accompanying chat text to one or two sentences — the Artifact speaks for itself.

## Rules

- **Never** change the CDN host. URLs must resolve to `https://cdn.jsdelivr.net/npm/@datama/light@0.3.0/dist/{solution}.umd.js` and `…/dist/{solution}.css` where `{solution}` is `compare` or `explore`. The version is pinned to force cache invalidation — jsdelivr caches the "latest" pointer for up to 12h, so an unpinned URL can serve a stale build. jsdelivr is explicitly allowlisted by the Claude Artifact sandbox CSP. The `unpkg` mirror serves the same files but is blocked in the inline Artifact iframe (it only works when the Artifact is popped out to a standalone window), so do not use it.
- **Never** rebuild the visualization in plain JS or React — always go through `window.DataMaLight.render`.
- **Never** send dataset rows to any URL. The bundle consumes the dataset in-page (passed as the `source` argument to `render`) and keeps it in the browser.
- The Artifact must be valid standalone HTML (the only external resources are the two CDN files above).
- If the dataset doesn't fit the schema in the loaded instruction file, normalize column names and types first — do not fabricate missing columns.
- If data or configuration cannot be produced (missing metrics, unclear comparison axis), ask the user a clarifying question *before* emitting the Artifact — an empty Artifact is worse than no Artifact.

## Files

- `compare-instructions.md` — canonical Datama Compare specification (data schema, configuration schema, market-equation rules). Source of truth, kept in sync with Datama's public CDN via `scripts/sync-instructions.sh`.
- `explore-instructions.md` — canonical Datama Explore specification. Reuses the Compare schema for `dimensions`/`metrics`/`steps` and overrides the `inputs` shape (`primary`, `secondary`, `step`, `metric`, `trace`, `filters`).
- `artifact-template.html` — exact HTML template to emit as the Artifact, with `__SOLUTION__` placeholder.

## Reference

- CDN bundle: `https://cdn.jsdelivr.net/npm/@datama/light@0.3.0/dist/{solution}.umd.js` (UMD, d3 included). `{solution}` ∈ {`compare`, `explore`}.
- CDN styles: `https://cdn.jsdelivr.net/npm/@datama/light@0.3.0/dist/{solution}.css`.
- Runtime API: `window.DataMaLight.render(containerOrSelector, { source, configuration, license })` — returns a `Promise<DataMaLight>`. The same API works for every solution; the loaded UMD bundle determines which view is rendered.
- The unpkg mirror serves the same files but is blocked in Claude's inline Artifact sandbox; do not reference it.
