# Data source providers for the AI agent (Google Sheet, GA4, Big Query, Metabase, etc.)

from sources.base import SourceKind, BaseSourceProvider
from sources.google_sheet import GoogleSheetProvider

__all__ = [
    "SourceKind",
    "BaseSourceProvider",
    "GoogleSheetProvider",
    "fetch_data",
]

_REGISTRY: list[BaseSourceProvider] = [GoogleSheetProvider()]


def fetch_data(source_kind: str, url_or_id: str) -> list[dict]:
    """Fetch raw rows from the given source. Returns list of dicts (column name -> value)."""
    for provider in _REGISTRY:
        if provider.kind == source_kind:
            return provider.fetch(url_or_id)
    raise ValueError(f"Unknown source kind: {source_kind}")
