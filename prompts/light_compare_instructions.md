# DataMaLight Compare: configuration and market equation

You are building inputs for **DataMaLight Compare**, which produces a waterfall comparison view. The solution expects a **dataset** (array of row objects), **dimensions**, **metrics**, **market equation steps**, **meta** (column metadata), and **inputs** (comparison definition).

## 1. Dataset

- **Format**: Array of objects. Each object is one row; keys are column names.
- Columns must be split into **dimensions** (e.g. date, category, region) and **metrics** (numeric KPIs).
- Date columns: use ISO-like strings (e.g. `"2025-01-01"`) or a format Light can parse as date.
- Metric columns: numbers (integer or float). Use consistent decimal separator (e.g. dot).

Example row:
```json
{ "Date": "2025-01-01", "Country": "France", "Channel": "Organic", "Sessions": 1200, "Revenue": 4500.5 }
```

## 2. Dimensions and metrics

- **dimensions**: Array of column names that define breakdowns (e.g. `["Date", "Country", "Channel"]`). At least one dimension with more than one distinct value is required for comparison.
- **metrics**: Array of numeric column names (e.g. `["Sessions", "Revenue"]`). Order matters for the default market equation (first metric per previous, etc.).

## 3. Market equation (steps and formula)

The market equation decomposes the main KPI into a product (or sum) of ratios or terms.

- **steps**: Array of step objects. Each step has:
  - `numerator` (string): metric name for the numerator.
  - `denominator` (string): metric name for the denominator, or `""` for the first step (or for sum-style).
  - `name` (string): display name (e.g. `"Revenue"` or `"Revenue per Session"`).
  - `focus` (string): optional filter focus.
  - `exclude` (array): optional list of exclusions.
  - `unit` (string, optional): unit label.

Default pattern for a product of ratios: step i has numerator = metrics[i], denominator = metrics[i-1] (or "" for i=0). Name can be e.g. "Metric per PreviousMetric".

- **formula**: String that references steps by index, e.g. `"[1]*[2]*[3]"` for a product of three steps, or `"[1]+[2]"` for a sum. Step indices are 1-based.

## 4. Compare inputs

- **inputs**: Object that defines what to compare.
  - **formula** (string): same as above, e.g. `"[1]*[2]*[3]"`.
  - **context** (string): dimension name used for the comparison (e.g. `"Date"` or `"Country"`). Must be one of `dimensions`.
  - **start** (array): for the context dimension, the segment(s) to treat as "start" (e.g. indices into `meta[context].unique` if relative, or actual values). For a single context, use an array of one element for start and one for end, or two arrays for multiple comparisons.
  - **end** (array): segment(s) for "end" (same structure as start).
  - **relative** (boolean): if true, start/end are indices (0-based) into `meta[context].unique`; if false, they are actual values from that array.
  - **order** (string): `"desc"` or `"asc"` for ordering.
  - **totalStepName** (string, optional): display name for the total step.
  - **totalStepUnit** (string, optional): unit for the total step.
  - **metricForClustering** (string): metric name used for clustering (often the last metric).

Typical default: context = first dimension with more than one unique value; start = last period (index length-1), end = previous period (e.g. index 0 or middle); relative = true; order = "desc".

## Output format

Produce a single JSON object with keys:

- **dataset**: array of row objects (same column names as dimensions + metrics).
- **dimensions**: array of strings.
- **metrics**: array of strings.
- **steps**: array of step objects (numerator, denominator, name, focus, exclude, unit?).
- **meta**: object keyed by column name, each `{ type, unique }`.
- **inputs**: object with formula, context, start, end, relative, order, totalStepName?, totalStepUnit?, metricForClustering.

Ensure: every column in dataset is in either dimensions or metrics; meta has an entry for each; inputs.context is in dimensions; inputs.start and inputs.end align with meta[inputs.context].unique (by index if relative, by value otherwise); steps reference only metric names that exist in metrics.
