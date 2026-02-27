# Data source providers for the AI agent (Google Sheet, GA4, Big Query, Metabase, etc.)

from sources.base import SourceKind, BaseSourceProvider
from sources.google_sheet import GoogleSheetProvider

__all__ = [
    "SourceKind",
    "BaseSourceProvider",
    "GoogleSheetProvider",
    "detect_source",
    "fetch_data",
]

_REGISTRY: list[BaseSourceProvider] = [GoogleSheetProvider()]


def detect_source(url_or_message: str) -> str | None:
    """Detect which source type the URL or user message refers to."""
    text = (url_or_message or "").strip().lower()
    for provider in _REGISTRY:
        kind = provider.detect(text)
        if kind:
            return kind
    return None


def fetch_data(source_kind: str, url_or_id: str, **kwargs) -> list[dict]:
    """Fetch raw rows from the given source. Returns list of dicts (column name -> value)."""
    for provider in _REGISTRY:
        if provider.kind == source_kind:
            return provider.fetch(url_or_id, **kwargs)
    raise ValueError(f"Unknown source kind: {source_kind}")
