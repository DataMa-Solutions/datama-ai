"""Validation of DataMaLight payloads (conf + dataset)."""


def _validate_base_payload(payload: dict) -> tuple[list[str], dict]:
    """
    Validate common payload structure shared by Compare and Explore.

    Returns:
        (errors, parts) where parts contains:
        - dimensions, metrics, steps, inputs, dataset
        - step_names (set[str]) extracted from steps
        - metric_candidates (set[str]) = metrics ∪ step_names
    """
    if not isinstance(payload, dict):
        return (["Payload must be a JSON object."], {})

    errors: list[str] = []

    dimensions = payload.get("dimensions")
    metrics = payload.get("metrics")
    steps = payload.get("steps")
    inputs = payload.get("inputs")
    dataset = payload.get("dataset")

    if not isinstance(dimensions, list) or not all(isinstance(d, str) for d in dimensions):
        errors.append("'dimensions' must be an array of strings.")
    if not isinstance(metrics, list) or not all(isinstance(m, str) for m in metrics):
        errors.append("'metrics' must be an array of strings.")

    step_names: set[str] = set()
    if not isinstance(steps, list):
        errors.append("'steps' must be an array.")
    else:
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"'steps[{i}]' must be an object.")
                continue
            if "numerator" not in step or "denominator" not in step:
                errors.append(f"'steps[{i}]' must have 'numerator' and 'denominator'.")
            if "name" not in step:
                errors.append(f"'steps[{i}]' must have 'name'.")
            else:
                name = step.get("name")
                if isinstance(name, str) and name:
                    step_names.add(name)

    if not isinstance(inputs, dict):
        errors.append("'inputs' must be an object.")

    if not isinstance(dataset, list):
        errors.append("'dataset' must be an array of row objects.")
    else:
        all_cols: set[str] = set()
        for row in dataset:
            if not isinstance(row, dict):
                errors.append("Each dataset row must be an object.")
                break
            all_cols.update(row.keys())
        if isinstance(dimensions, list) and isinstance(metrics, list):
            expected = set(dimensions) | set(metrics)
            # Allow extra columns in the dataset that are not referenced in dimensions/metrics.
            # We only require that all declared dimensions/metrics actually exist in the dataset.
            if all_cols and not all_cols.issuperset(expected):
                errors.append("Dataset must contain all dimensions and metrics.")

    metric_candidates = set(metrics) if isinstance(metrics, list) else set()
    metric_candidates |= step_names

    return (
        errors,
        {
            "dimensions": dimensions,
            "metrics": metrics,
            "steps": steps,
            "inputs": inputs,
            "dataset": dataset,
            "step_names": step_names,
            "metric_candidates": metric_candidates,
        },
    )


def validate_compare_payload(payload: dict) -> list[str]:
    """
    Validate that the payload has the shape expected by DataMaCompareSettingsAPI.load.
    Returns a list of error messages (empty if valid).
    """
    errors, parts = _validate_base_payload(payload)
    if errors:
        return errors

    dimensions = parts["dimensions"]
    metrics = parts["metrics"]
    inputs = parts["inputs"]

    if isinstance(inputs, dict):
        if "formula" not in inputs:
            errors.append("'inputs' must have 'formula'.")
        if "context" not in inputs:
            errors.append("'inputs' must have 'context'.")
        elif dimensions and inputs.get("context") not in dimensions:
            errors.append("'inputs.context' must be one of dimensions.")
        if "start" not in inputs or not isinstance(inputs.get("start"), list):
            errors.append("'inputs' must have 'start' (array).")
        if "end" not in inputs or not isinstance(inputs.get("end"), list):
            errors.append("'inputs' must have 'end' (array).")
        if "relative" not in inputs:
            errors.append("'inputs' must have 'relative' (boolean).")
        if "metricForClustering" not in inputs and metrics:
            errors.append("'inputs' must have 'metricForClustering'.")

    return errors


def validate_explore_payload(payload: dict) -> list[str]:
    """
    Validate Explore payload shape expected by the toolkit explore runner.
    Returns a list of error messages (empty if valid).
    """
    errors, parts = _validate_base_payload(payload)
    if errors:
        return errors

    dimensions = parts["dimensions"]
    inputs = parts["inputs"]
    step_names = parts["step_names"]
    metric_candidates = parts["metric_candidates"]

    if isinstance(inputs, dict):
        for required_key in ("primary", "secondary", "step", "metric", "trace", "filters"):
            if required_key not in inputs:
                errors.append(f"'inputs' must have '{required_key}'.")
        if "context" in inputs and inputs.get("context") not in ("", None):
            if dimensions and inputs.get("context") not in dimensions:
                errors.append("'inputs.context' must be one of dimensions when set.")
        if dimensions and "primary" in inputs and inputs.get("primary") not in dimensions:
            errors.append("'inputs.primary' must be one of dimensions.")
        if "secondary" in inputs:
            valid_secondary = set(dimensions or []) | {"", "Comparison Dimension"}
            if inputs.get("secondary") not in valid_secondary:
                errors.append(
                    "'inputs.secondary' must be one of dimensions, "
                    "'Comparison Dimension', or ''."
                )
        if "step" in inputs and isinstance(inputs.get("step"), str):
            if step_names and inputs.get("step") not in step_names:
                errors.append("'inputs.step' must match one of steps[].name.")
        if "metric" in inputs and isinstance(inputs.get("metric"), str):
            if metric_candidates and inputs.get("metric") not in metric_candidates:
                errors.append("'inputs.metric' must match one of metrics or steps[].name.")
        if "trace" in inputs and inputs.get("trace") != "default":
            errors.append("'inputs.trace' must be 'default'.")
        if "filters" in inputs and not isinstance(inputs.get("filters"), dict):
            errors.append("'inputs.filters' must be an object.")

    return errors


def validate_payload_for_solution(payload: dict, solution: str) -> list[str]:
    """Validate payload using the schema expected by the selected solution."""
    normalized_solution = (solution or "compare").strip().lower()
    if normalized_solution == "explore":
        return validate_explore_payload(payload)
    return validate_compare_payload(payload)
