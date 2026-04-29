# Datama — Claude Agent Skill

Adds Datama Compare and Datama Explore to Claude. When a user asks Claude to analyze variance, decompose a KPI change, compare two periods / segments, break down a metric across dimensions, or slice a dataset, Claude produces an interactive Datama Artifact powered by the Datama Light runner.

## How it works

1. Claude picks the solution (`compare` or `explore`) from the user request.
2. Claude reads the matching `*-instructions.md` and derives column metadata from the user's data.
3. Claude generates a valid `configuration` (dimensions, metrics, steps, inputs) for that solution.
4. Claude emits a standalone HTML Artifact (built from `artifact-template.html`) that loads `https://cdn.jsdelivr.net/npm/@datama/light@0.3.0/dist/{solution}.umd.js` and calls `DataMaLight.render(...)` directly.
5. The runner renders the interactive visualization entirely in the user's browser.

## Security model

- **User data never leaves the user's Claude session.** The dataset is inlined in the Artifact HTML and consumed in-page by `DataMaLight.render`.
- **Datama code is fetched from a public CDN** (jsdelivr) and runs inside the Artifact sandbox.
- **The only outbound request to Datama is optional license validation.** When `license.txt` is present in the project, the license key (and only the key) is forwarded to Datama for validation; no dataset is sent.

## Install (Claude.ai Projects)

1. Zip this folder from its parent directory:
   ```bash
   rm -f claude-skill.zip datama-skill.zip && zip -r datama-skill.zip claude-skill
   ```
2. In Claude.ai, open the target Project.
3. Upload the Skill to the Project's custom Skills.
4. (Optional, for paid tier) Add your Datama license key as a file named `license.txt` in the Project's knowledge.

Then ask Claude things like:
- **Compare**: "compare Q1 vs Q2 revenue", "decompose the drop in conversion rate", "what explains the delta in sessions between iOS and Android".
- **Explore**: "break down revenue by country and device", "plot conversion across channels", "show the funnel by source".

## Keeping the skill up to date

The canonical specifications live on Datama's public CDN and are shared across all AI integrations (Datama AI kit for Streamlit, ChatGPT, Claude, …). Run the sync script to refresh the bundled copies:

```bash
./scripts/sync-instructions.sh                 # sync every published solution
./scripts/sync-instructions.sh compare         # or a specific subset
```

Note: until `explore/instruction-runner.ai-toolkit.md` is published on GCS, the script will keep the local `explore-instructions.md` in place.

## Files

- `SKILL.md` — skill entry point (instructions Claude reads when triggered)
- `compare-instructions.md` — canonical Compare specification
- `explore-instructions.md` — canonical Explore specification (minimal v1, enriched on demand)
- `artifact-template.html` — HTML template Claude adapts to produce the Artifact (uses `__SOLUTION__` placeholder)
- `scripts/sync-instructions.sh` — updater that pulls the latest canonical specs from GCS
