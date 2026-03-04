"""Validation of DataMaLight Compare payload (conf + dataset)."""


def validate_compare_payload(payload: dict) -> list[str]:
    """
    Validate that the payload has the shape expected by DataMaCompareSettingsAPI.load.
    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["Payload must be a JSON object."]

    dimensions = payload.get("dimensions")
    metrics = payload.get("metrics")
    steps = payload.get("steps")
    meta = payload.get("meta")
    inputs = payload.get("inputs")
    dataset = payload.get("dataset")

    if not isinstance(dimensions, list) or not all(isinstance(d, str) for d in dimensions):
        errors.append("'dimensions' must be an array of strings.")
    if not isinstance(metrics, list) or not all(isinstance(m, str) for m in metrics):
        errors.append("'metrics' must be an array of strings.")
    if not isinstance(steps, list):
        errors.append("'steps' must be an array.")
    else:
        for i, s in enumerate(steps):
            if not isinstance(s, dict):
                errors.append(f"'steps[{i}]' must be an object.")
            else:
                if "numerator" not in s or "denominator" not in s:
                    errors.append(f"'steps[{i}]' must have 'numerator' and 'denominator'.")
                if "name" not in s:
                    errors.append(f"'steps[{i}]' must have 'name'.")

    if not isinstance(meta, dict):
        errors.append("'meta' must be an object keyed by column name.")
    else:
        for col, val in meta.items():
            if not isinstance(val, dict):
                errors.append(f"'meta.{col}' must be an object.")
            else:
                if "type" not in val:
                    errors.append(f"'meta.{col}' must have 'type'.")
                if "unique" not in val or not isinstance(val["unique"], list):
                    errors.append(f"'meta.{col}' must have 'unique' (array).")

    if not isinstance(inputs, dict):
        errors.append("'inputs' must be an object.")
    else:
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

    if not isinstance(dataset, list):
        errors.append("'dataset' must be an array of row objects.")
    else:
        all_cols = set()
        for row in dataset:
            if not isinstance(row, dict):
                errors.append("Each dataset row must be an object.")
                break
            all_cols.update(row.keys())
        if dimensions is not None and metrics is not None:
            expected = set(dimensions) | set(metrics)
            # Allow extra columns in the dataset that are not referenced in dimensions/metrics.
            # We only require that all declared dimensions/metrics actually exist in the dataset.
            if all_cols and not all_cols.issuperset(expected):
                errors.append("Dataset must contain all dimensions and metrics.")

    return errors
