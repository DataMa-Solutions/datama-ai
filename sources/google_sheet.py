"""Google Sheets data source provider."""

import csv
import io
import re
import urllib.request
from sources.base import BaseSourceProvider, SourceKind


def _extract_sheet_id(url_or_id: str) -> str | None:
    """Extract spreadsheet ID from URL or return as-is if it looks like a raw ID."""
    url_or_id = (url_or_id or "").strip()
    if re.match(r"^[a-zA-Z0-9_-]{40,}$", url_or_id):
        return url_or_id
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", url_or_id)
    return match.group(1) if match else None


def _extract_gid(url_or_id: str) -> int:
    """Extract sheet gid from URL fragment or query (#gid=0, &gid=0, ?gid=0). Default 0."""
    url_or_id = (url_or_id or "").strip()
    match = re.search(r"[?#&]gid=(\d+)", url_or_id)
    return int(match.group(1)) if match else 0


def _fetch_public_sheet_csv(sheet_id: str, gid: int = 0) -> list[dict]:
    """Fetch public sheet as CSV (no auth). Sheet must be shared as 'Anyone with the link can view'."""
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "DataMa-AI-Agent/1.0"})
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


class GoogleSheetProvider(BaseSourceProvider):
    """Fetch data from a Google Sheet (public CSV export or via gspread + service account)."""

    @property
    def kind(self) -> str:
        return SourceKind.GOOGLE_SHEET

    def fetch(self, url_or_id: str) -> list[dict]:
        sheet_id = _extract_sheet_id(url_or_id)
        if not sheet_id:
            raise ValueError(
                "Could not extract Google Sheet ID from: " + str(url_or_id)[:80]
            )
        gid = _extract_gid(url_or_id)
        return _fetch_public_sheet_csv(sheet_id, gid)
