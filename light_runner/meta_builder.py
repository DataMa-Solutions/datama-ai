"""
Build meta from a dataset (list of row dicts) in the same shape as
SourceMutator.getMetaData() so the toolkit runner receives metadata consistent with Light.

Ref: light/src/resources/mutators/SourceMutator.js getMetaData(source, order, sanitizer)
     light/src/resources/DataMaLight.js __getSourceMetadata() -> getMetaData(source, 'desc')
"""

import csv
import io
import re
from datetime import datetime
from typing import Any

GUESS_TYPE_SAMPLE = 100

# Date format detection: first match wins (mirrors DataMaDate.handledFormat)
DATE_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "YYYY-MM-DD"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{1,2}:\d{1,2}$"), "YYYY-MM-DD HH:mm:ss"),
    (re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"), "M/D/YYYY"),
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "DD-MM-YYYY"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "DD/MM/YYYY"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "YYYY/MM/DD"),
]


def _detect_date_format(value: str) -> str | None:
    s = (value or "").strip()
    for pattern, fmt in DATE_PATTERNS:
        if pattern.match(s):
            return fmt
    return None


def _get_type(sample: list[Any]) -> str:
    """Mirrors SourceMutator.getType(sample): 'int' | 'float' | 'date' | 'string' | 'boolean'."""
    usable = [v for v in sample if v is not None and v != ""]
    if not usable:
        return "string"

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
        has_float = any(
            isinstance(v, float) or (isinstance(v, str) and "." in str(v).replace(",", "."))
            for v in usable
        )
        return "float" if has_float else "int"

    if all(v is True or v is False or str(v).lower() in ("true", "false", "1", "0") for v in usable):
        return "boolean"

    if all(isinstance(v, str) for v in usable):
        if all(_detect_date_format(str(v)) for v in usable[:20]):
            return "date"
        return "string"

    return "string"


def _date_sort_key(v: Any) -> tuple[int, Any]:
    """
    Key for sorting date-like values.
    Always returns a tuple (priority, value) so Python never compares str vs datetime.
    """
    s = str(v).strip()
    # Try ISO date / datetime first
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        try:
            part = s.replace(" ", "T").split(".")[0].split("+")[0]
            dt = datetime.fromisoformat(part)
            return (0, dt.timestamp())
        except Exception:
            pass

    # Try DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})", s)
    if m:
        try:
            d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000 if y < 50 else 1900
            dt = datetime(y, mo, d)
            return (0, dt.timestamp())
        except Exception:
            pass

    # Fallback: treat as plain string after all parsed dates
    return (1, s)


def _normalize_unique(values: list[Any], col_type: str) -> list[Any]:
    """Normalize and dedupe unique values by type (mirrors getMetaData unique mapping)."""
    out = []
    seen = set()
    for v in values:
        if v is None or v == "":
            continue
        if col_type == "int":
            try:
                x = int(float(str(v).replace(",", ".")))
            except (ValueError, TypeError):
                x = v
        elif col_type == "float":
            try:
                x = float(str(v).replace(",", "."))
            except (ValueError, TypeError):
                x = v
        else:
            x = v if col_type == "date" else str(v)
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def get_meta_from_dataset(
    source: list[dict[str, Any]],
    order: str = "desc",
) -> dict[str, dict[str, Any]]:
    """
    Build meta from dataset (list of row dicts), compatible with DataMaLight settings.meta.
    Each column: name, type, unique (sorted), format (if date). order: 'asc' | 'desc'.
    """
    meta: dict[str, dict[str, Any]] = {}
    if not source:
        return meta

    columns = list(source[0].keys())
    for col in columns:
        values = [row.get(col) for row in source]
        unique_raw = list(dict.fromkeys(v for v in values if v is not None and v != ""))
        sample = unique_raw[:GUESS_TYPE_SAMPLE] if len(unique_raw) > GUESS_TYPE_SAMPLE else unique_raw
        col_type = _get_type(sample)

        unique = _normalize_unique(unique_raw, col_type)
        if col_type == "date":
            unique = sorted(unique, key=_date_sort_key)
        elif col_type in ("int", "float"):
            try:
                unique = sorted(unique, key=lambda x: (x is None, x if isinstance(x, (int, float)) else float("-inf")))
            except Exception:
                unique = sorted(unique, key=str)
        else:
            unique = sorted(unique, key=lambda x: (x is None, str(x)))
        if order == "desc":
            unique = list(reversed(unique))

        entry: dict[str, Any] = {"name": col, "type": col_type, "unique": unique}
        if col_type == "date" and unique:
            fmt = next((_detect_date_format(str(v)) for v in unique[:20] if _detect_date_format(str(v))), None)
            if fmt:
                entry["format"] = fmt
        meta[col] = entry

    return meta


def meta_to_csv(
    meta: dict[str, dict[str, Any]],
    max_unique_per_col: int = 50,
    sep: str = "|",
) -> str:
    """Export meta to CSV for LLM context (column, type, format, n_unique, unique_values)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["column", "type", "format", "n_unique", "unique_values"])
    for col, info in meta.items():
        u = info.get("unique") or []
        n = len(u)
        sample = u[:max_unique_per_col]
        vals = sep.join(str(v) for v in sample) if sample else ""
        if n > max_unique_per_col:
            vals += f" ... (+{n - max_unique_per_col} more)"
        w.writerow([col, info.get("type", ""), info.get("format") or "", n, vals])
    return out.getvalue().strip()
