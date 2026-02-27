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

    def detect(self, url_or_message: str) -> str | None:
        text = (url_or_message or "").strip().lower()
        if "docs.google.com/spreadsheets" in text or "google sheet" in text:
            return self.kind
        if _extract_sheet_id(url_or_message):
            return self.kind
        return None

    def fetch(self, url_or_id: str, gid: int = 0, **kwargs) -> list[dict]:
        sheet_id = _extract_sheet_id(url_or_id)
        if not sheet_id:
            raise ValueError(
                "Could not extract Google Sheet ID from: " + str(url_or_id)[:80]
            )

        creds = _get_credentials()
        if creds is not None:
            return _fetch_via_gspread(sheet_id, creds)
        return _fetch_public_sheet_csv(sheet_id, gid)


def _get_credentials() -> "object | None":
    """Return service account credentials if configured, else None (use public CSV)."""
    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None) or {}
        creds_dict = secrets.get("gcp_service_account") or secrets.get(
            "google_credentials"
        )
        if creds_dict:
            from google.oauth2.service_account import Credentials

            return Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                    "https://www.googleapis.com/auth/drive.readonly",
                ],
            )
    except Exception:
        pass
    import os

    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if path and os.path.isfile(path):
        from google.oauth2.service_account import Credentials

        return Credentials.from_service_account_file(
            path,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ],
        )
    return None


def _fetch_via_gspread(sheet_id: str, credentials) -> list[dict]:
    import gspread

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)
    sheet = spreadsheet.sheet1
    rows = sheet.get_all_records()
    return [dict(r) for r in rows]
