"""
Build meta object from a dataset (list of row dicts) in the same shape as
DataMaLight SourceMutator.getMetaData() so the Compare runner receives
metadata consistent with the Light front-end.

Ref: light/src/resources/mutators/SourceMutator.js getMetaData(source, order, sanitizer)
     light/src/resources/DataMaLight.js __getSourceMetadata() -> getMetaData(source, 'desc')
"""

import csv
import io
import re
from datetime import datetime
from typing import Any

# Sample size for type inference (mirrors DATAMA_GUESS_TYPE_SAMPLE)
GUESS_TYPE_SAMPLE = 100

# Date format detection: try in order; first match wins (mirrors DataMaDate.handledFormat)
DATE_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "YYYY-MM-DD"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{1,2}:\d{1,2}$"), "YYYY-MM-DD HH:mm:ss"),
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "DD-MM-YYYY"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "DD/MM/YYYY"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "YYYY/MM/DD"),
]


def _detect_date_format(value: str) -> str | None:
    """Detect date format from a string; returns format string or None."""
    s = (value or "").strip()
    for pattern, fmt in DATE_PATTERNS:
        if pattern.match(s):
            return fmt
    return None


def _infer_type(sample: list[Any]) -> str:
    """
    Infer column type from a sample of values.
    Mirrors SourceMutator.getType(sample).
    Returns: 'int' | 'float' | 'date' | 'string' | 'boolean' | 'unknown'
    """
    usable = [v for v in sample if v is not None and v != ""]
    if not usable:
        return "string"

    # Boolean
    if all(v is True or v is False or str(v).lower() in ("true", "false", "1", "0") for v in usable):
        return "boolean"

    # Numeric
    def is_numeric(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return True
        s = str(v).strip().replace(",", ".")
        if not s or s in ("-", "+"):
            return False
        try:
            float(s)
            return True
        except ValueError:
            return False

    if all(is_numeric(v) for v in usable):
        if any(
            isinstance(v, float) or (isinstance(v, str) and "." in str(v).replace(",", "."))
            for v in usable
        ):
            return "float"
        return "int"

    # Date (string that looks like date)
    if all(isinstance(v, str) for v in usable):
        date_formats = [_detect_date_format(v) for v in usable[:20]]
        if all(f for f in date_formats):
            return "date"

    return "string"


def _parse_unique_for_type(unique_raw: list[Any], col_type: str) -> list[Any]:
    """Normalize unique values for storage (ints, floats, strings)."""
    out = []
    for v in unique_raw:
        if v is None or v == "":
            continue
        if col_type == "int":
            try:
                out.append(int(float(str(v).replace(",", "."))))
            except (ValueError, TypeError):
                out.append(v)
        elif col_type == "float":
            try:
                out.append(float(str(v).replace(",", ".")))
            except (ValueError, TypeError):
                out.append(v)
        elif col_type == "string":
            out.append(str(v))
        else:
            out.append(v)
    return out


def _date_sort_key(v: Any) -> datetime | str:
    """Key for sorting date-like values; falls back to string."""
    s = str(v).strip()
    # ISO date or datetime
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        try:
            part = s.replace(" ", "T").split(".")[0].split("+")[0]
            return datetime.fromisoformat(part)
        except Exception:
            pass
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", s)
    if m:
        try:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000 if y < 50 else 1900
            return datetime(y, mo, d)
        except Exception:
            pass
    return s


def _sort_unique(unique: list[Any], col_type: str) -> list[Any]:
    """Sort unique values; for dates, sort by parsed date."""
    if col_type == "date":
        try:
            return sorted(unique, key=_date_sort_key)
        except Exception:
            return sorted(unique, key=str)
    if col_type in ("int", "float"):
        try:
            return sorted(unique, key=lambda x: (x is None, x if isinstance(x, (int, float)) else float("-inf")))
        except Exception:
            return sorted(unique, key=str)
    return sorted(unique, key=lambda x: (x is None, str(x)))


def get_meta_from_dataset(
    source: list[dict[str, Any]],
    order: str = "desc",
) -> dict[str, dict[str, Any]]:
    """
    Build a meta object from a dataset (list of row dicts), compatible with
    DataMaLight settings.meta.

    Each column gets:
      - name: column name
      - type: 'int' | 'float' | 'date' | 'string' | 'boolean' | 'unknown'
      - unique: sorted list of unique values (for date, sorted by date)
      - format: (only for type 'date') e.g. 'YYYY-MM-DD'

    order: 'asc' | 'desc' — order of unique values (default 'desc' to match Light).
    """
    meta: dict[str, dict[str, Any]] = {}
    if not source:
        return meta

    columns = list(source[0].keys())
    for col in columns:
        values = [row.get(col) for row in source]
        unique_raw = list(dict.fromkeys(v for v in values if v is not None and v != ""))
        sample = unique_raw[:GUESS_TYPE_SAMPLE] if len(unique_raw) > GUESS_TYPE_SAMPLE else unique_raw
        col_type = _infer_type(sample)

        unique = _parse_unique_for_type(unique_raw, col_type)
        unique = list(dict.fromkeys(unique))  # preserve order, dedupe
        unique = _sort_unique(unique, col_type)
        if order == "desc":
            unique = list(reversed(unique))

        entry = {
            "name": col,
            "type": col_type,
            "unique": unique,
        }
        if col_type == "date" and unique:
            formats = [_detect_date_format(str(v)) for v in unique[:20]]
            detected = next((f for f in formats if f), None)
            if detected:
                entry["format"] = detected
            else:
                entry["format"] = "YYYY-MM-DD"
        meta[col] = entry

    return meta


def meta_to_csv(
    meta: dict[str, dict[str, Any]],
    max_unique_per_col: int = 50,
    sep: str = "|",
) -> str:
    """
    Export meta to a compact CSV string for LLM context (saves tokens vs JSON).
    One row per column: name, type, format, n_unique, unique_values (sep-separated, truncated).
    """
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["column", "type", "format", "n_unique", "unique_values"])
    for col, info in meta.items():
        unique = info.get("unique") or []
        n = len(unique)
        sample = unique[:max_unique_per_col]
        values_str = sep.join(str(v) for v in sample) if sample else ""
        if n > max_unique_per_col:
            values_str += f" ... (+{n - max_unique_per_col} more)"
        fmt = info.get("format") or ""
        writer.writerow([col, info.get("type", ""), fmt, n, values_str])
    return out.getvalue().strip()
