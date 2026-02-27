"""Base abstraction for data source providers."""

from abc import ABC, abstractmethod


class SourceKind:
    """Known source types (extensible for GA4, Big Query, Metabase, etc.)."""
    GOOGLE_SHEET = "google_sheet"
    GA4 = "ga4"
    BIGQUERY = "bigquery"
    METABASE = "metabase"


class BaseSourceProvider(ABC):
    """Protocol for a data source provider."""

    @property
    @abstractmethod
    def kind(self) -> str:
        """Source type identifier (e.g. 'google_sheet')."""
        ...

    def detect(self, url_or_message: str) -> str | None:
        """
        Detect if the given URL or user message refers to this source.
        Returns self.kind if it matches, None otherwise.
        """
        return None

    @abstractmethod
    def fetch(self, url_or_id: str, **kwargs) -> list[dict]:
        """
        Fetch data from the source. Returns a list of row dicts (column name -> value).
        """
        ...
