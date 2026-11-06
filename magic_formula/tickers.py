"""Ticker universe: the SEC's public company ticker list, plus optional extra tickers."""

import os
import re
from pathlib import Path

import requests

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
USER_AGENT_ENV = "SEC_USER_AGENT"


class MissingUserAgentError(RuntimeError):
    """Raised when SEC_USER_AGENT is unset; the SEC rejects anonymous clients."""


def sec_headers(user_agent: str | None = None) -> dict[str, str]:
    """Build request headers for sec.gov.

    The SEC asks automated clients to identify themselves with a contact, e.g.
    ``SEC_USER_AGENT="Jane Doe jane@example.com"``. It is read from the
    environment so no personal details live in the repository.
    """
    agent = (user_agent or os.getenv(USER_AGENT_ENV, "")).strip()
    if not agent:
        raise MissingUserAgentError(
            f"Set {USER_AGENT_ENV} to 'Your Name your@email.com' "
            "(required by the SEC fair-access policy), or pass --tickers / --tickers-file."
        )
    return {"User-Agent": agent, "Accept": "application/json"}


def parse_sec_payload(payload: dict) -> list[str]:
    """Extract ticker symbols from the ``company_tickers.json`` structure."""
    return [row["ticker"] for row in payload.values() if row.get("ticker")]


def fetch_sec_tickers(user_agent: str | None = None, timeout: int = 30) -> list[str]:
    resp = requests.get(SEC_TICKERS_URL, headers=sec_headers(user_agent), timeout=timeout)
    resp.raise_for_status()
    return parse_sec_payload(resp.json())


def read_ticker_file(path: str | Path) -> list[str]:
    """Read tickers from a text file: one per line or comma separated, ``#`` comments allowed."""
    tickers: list[str] = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0]
        tickers.extend(t for t in re.split(r"[,\s]+", line) if t)
    return tickers


def normalize(tickers: list[str]) -> list[str]:
    """Upper-case, strip, de-duplicate and sort."""
    return sorted({t.strip().upper() for t in tickers if t and t.strip()})
