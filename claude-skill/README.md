# Datama Compare — Claude Agent Skill

Adds Datama Compare to Claude. When a user asks Claude to analyze variance, decompose a KPI change, or compare two periods / segments, Claude produces an interactive Compare Artifact powered by the Datama Light runner.

## How it works

1. Claude reads the bundled `compare-instructions.md` and derives column metadata from the user's data.
2. Claude generates a valid Compare `configuration` (dimensions, metrics, steps, inputs, formula).
3. Claude emits a standalone HTML Artifact (built from `artifact-template.html`) that embeds the Datama runner in an iframe and passes `{ dataset, configuration, userLicenseKey? }` via `postMessage`.
4. The runner renders the interactive waterfall entirely in the user's browser.

## Security model

- **User data never leaves the user's Claude session.** The dataset is inlined in the Artifact HTML and posted to the iframe in the same browser tab.
- **Datama code never leaves Datama's origin.** The rendering engine is served from Datama's public CDN and runs inside the iframe, not inside the Artifact itself.
- **The only outbound request to Datama is optional license validation.** When `license.txt` is present in the project, the license key (and only the key) is forwarded to Datama for validation; no dataset is sent.

## Install (Claude.ai Projects)

1. Zip this folder.
2. In Claude.ai, open the target Project.
3. Upload the Skill to the Project's custom Skills.
4. (Optional, for paid tier) Add your Datama license key as a file named `license.txt` in the Project's knowledge.

Then ask Claude things like "compare Q1 vs Q2 revenue", "decompose the drop in conversion rate", or "what explains the delta in sessions between iOS and Android" with your data attached.

## Keeping the skill up to date

The canonical Compare specification lives on Datama's public CDN and is shared across all AI integrations (Datama AI kit for Streamlit, ChatGPT, Claude, …). Run the sync script to refresh the bundled copy:

```bash
./scripts/sync-instructions.sh
```

## Files

- `SKILL.md` — skill entry point (instructions Claude reads when triggered)
- `compare-instructions.md` — canonical Compare specification, synced from Datama CDN
- `artifact-template.html` — HTML template Claude adapts to produce the Artifact
- `scripts/sync-instructions.sh` — updater that pulls the latest canonical spec
