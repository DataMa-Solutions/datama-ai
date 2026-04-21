#!/usr/bin/env bash
# Sync the canonical Compare instruction from Datama's public CDN.
# Run this before packaging / publishing the Skill so that Claude's bundled
# instructions stay aligned with the "tronc commun" shared across AI kits.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HERE/../compare-instructions.md"
URL="https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest/compare/instruction-runner.ai-toolkit.md"
curl -fsSL "$URL" -o "$DEST"
echo "Synced $URL -> $DEST"
