#!/usr/bin/env bash
# Sync the canonical Datama AI Toolkit instructions from Datama's public CDN.
# Run this before packaging / publishing the Skill so that Claude's bundled
# instructions stay aligned with the "tronc commun" shared across AI kits.
#
# Usage:
#   scripts/sync-instructions.sh                 # sync every solution that is published
#   scripts/sync-instructions.sh compare explore # sync a specific subset
#
# Solutions whose instruction file is not yet published on GCS are skipped
# silently — keep the locally bundled copy as the source of truth until then.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DEST_DIR="$HERE/.."
BASE_URL="https://storage.googleapis.com/app2.datama.io/ai-datama-light/latest"

if [ "$#" -eq 0 ]; then
  SOLUTIONS=(compare explore)
else
  SOLUTIONS=("$@")
fi

for solution in "${SOLUTIONS[@]}"; do
  url="$BASE_URL/$solution/instruction-runner.ai-toolkit.md"
  dest="$DEST_DIR/${solution}-instructions.md"
  if curl -fsSL "$url" -o "$dest.tmp"; then
    mv "$dest.tmp" "$dest"
    echo "Synced $url -> $dest"
  else
    rm -f "$dest.tmp"
    echo "Skipped $solution (not published yet at $url) — keeping local copy"
  fi
done
