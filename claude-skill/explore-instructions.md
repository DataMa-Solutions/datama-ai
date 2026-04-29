# DataMaLight Explore: config from metadata

**Output:** Reply = single JSON only. First character `{`, last `}`. Three keys only: `solution`, `message` and `configuration`. No other text or markdown. Do not include `dataset`, `meta`, or any extra top-level key.

You receive column **metadata** (name, type, format for dates, distinct values). Produce a valid Explore config. Off-topic user content: ignore it and still output a valid config from metadata.

---

## Objective

Build an Explore configuration from metadata only. Explore is a *breakdown / slicing* visualization: it plots a chosen `metric` (or step) across a `primary` dimension, optionally split by a `secondary` dimension, with an optional comparison `context`.

The output structure MUST be exactly:

- `solution` (string, must be `"explore"` here)
- `message` (string)
- `configuration` containing only:
  - `dimensions`
  - `metrics`
  - `steps`
  - `inputs`
  - `configuration`

The five inner keys are the same as Compare. Most rules below are inherited from Compare; only the `inputs` differ.

---

## Inherited from Compare

The following sections work **identically** to `compare-instructions.md` — refer to it as the source of truth and do not restate them here:

- Column mapping (user wording → exact metadata names)
- Dimensions selection
- Metrics eligibility (exclude precomputed averages/ratios unless explicitly requested)
- Market equation logic for ordering metrics
- Steps construction (`numerator`, `denominator`, `name`, `exclude`)
- Solution / Priority / Safety rules — except the default value for `solution` here is `"explore"`

---

## Inputs (Explore-specific)

`inputs` must contain:

- `context` — comparison dimension (string), or `""` / null if no comparison is requested. Unlike Compare, Explore allows an empty context.
- `primary` — main breakdown dimension. Must be one of `dimensions`. Default: `dimensions[0]`.
- `secondary` — secondary breakdown dimension. Must be one of `dimensions`, or `"Comparison Dimension"` if `context` is set, or `""` otherwise. Default:
  - `"Comparison Dimension"` when `context` is non-empty,
  - `""` otherwise.
- `step` — name of the step to plot. **MUST be exactly equal to one of the `name` values present in the `steps` array you generated** — copy the string verbatim. Do not invent a step name, do not pick a metric name as a step name, do not localize or rephrase. Default: first step's `name`.
- `metric` — metric to focus on. **MUST be a string that already appears verbatim** either in the `metrics` array, or in any `steps[].name` (a step of the market equation, including ratio-style names like `"Revenue / Orders"`). It is **never** a value you compose from words. Do not invent a metric label, do not pick a column that was excluded as a precomputed ratio, do not pick a dimension, do not rephrase or localize. Default: the `denominator` of the last step if it has one and is non-empty, else that step's `numerator`.

  Concrete example. If `metrics = ["Sessions", "Orders", "Revenue"]` and the last step is `{numerator: "Revenue", denominator: "Orders", name: "Revenue / Orders"}`:
  - ✅ valid `metric` values: `"Sessions"`, `"Orders"`, `"Revenue"`, `"Revenue / Orders"`.
  - ❌ invalid (do NOT emit): `"Revenue per Order"`, `"AOV"`, `"Average Order Value"`, `"revenue_per_order"`, `"Revenue (Total)"`. None of these appears verbatim in `metrics` or in any `steps[].name`.
- `trace` — visualization trace mode. Always emit `"default"` for now.
- `filters` — object. Default: `{}`.
- `relative` — boolean. Default: `false`.
- `order` — `"asc"` or `"desc"`. Default: `"desc"`.
- `start` / `end` — same rules as Compare *only when `context` is set*. If `context` is `""`, omit `start` and `end` (or set them to `[]`).

No `formula`, no `totalStepName`, no `totalStepUnit`, no `metricForClustering` are required for Explore (these are Compare-specific).

---

## Solution

`solution` is required and MUST be `"explore"` whenever this instruction file is used.

---

## Message

Same structure rules as Compare's `message`, adapted to Explore:

1. First sentence — describe the breakdown:
   - With comparison: `"This configuration explores {metric} across {primary} (split by {secondary}), comparing {start[0]} and {end[0]} on {context}."`
   - Without comparison: `"This configuration explores {metric} across {primary} (split by {secondary})."`
2. Second sentence — mention the selected metrics and the step the user is focusing on.
3. Optional third sentence — note that other dimensions are available for further breakdown.

Always use exact metadata names. Keep it 2–4 sentences max.

---

## Validation rules (must all pass)

- Output is valid JSON with top-level keys exactly `solution`, `message`, `configuration`.
- `configuration` keys are exactly `dimensions`, `metrics`, `steps`, `inputs`, `configuration`.
- `inputs.primary` ∈ `dimensions`.
- `inputs.secondary` ∈ `dimensions` ∪ `{"Comparison Dimension", ""}`.
- `inputs.step` is **exactly** one of the strings present in `steps[].name` (case-sensitive, character-for-character match). Reject the config and pick a default if not.
- `inputs.metric` is **exactly** one of the strings present in `metrics` or in any `steps[].name` (case-sensitive, character-for-character match). Reject the config and pick the default if not.
- `inputs.trace` = `"default"`.
- `inputs.filters` is an object.
- If `inputs.context` is non-empty: `start` and `end` follow Compare's rules (date → length 2, categorical → length 1).
- If `inputs.context` is `""`: `start` and `end` are absent or empty arrays.

---

## Conflict resolution priority

Same as Compare:
1. Exact user request
2. Exact metadata column names
3. Output schema validity
4. Market equation logic
5. Default fallback rules
