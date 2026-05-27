"""AI toolkit URLs deployed by light deploy-tools workflow."""

BASE_URL = "https://storage.googleapis.com/app2.datama.io/artificial-intelligence/tools/"

RUNNER_URL = BASE_URL + "runner.html"
INSTRUCTION_COMPARE_URL = BASE_URL + "compare/compare-instructions.md"
INSTRUCTION_EXPLORE_URL = BASE_URL + "explore/explore-instructions.md"

# Backward-compatible alias used by the current config step.
INSTRUCTION_URL = INSTRUCTION_COMPARE_URL
