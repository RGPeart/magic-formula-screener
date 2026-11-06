import pytest

from magic_formula import tickers


def test_parse_sec_payload():
    payload = {
        "0": {"cik_str": 1, "ticker": "AAPL", "title": "Apple"},
        "1": {"cik_str": 2, "ticker": "MSFT", "title": "Microsoft"},
        "2": {"cik_str": 3, "ticker": "", "title": "Blank"},
    }
    assert tickers.parse_sec_payload(payload) == ["AAPL", "MSFT"]


def test_normalize_dedupes_and_uppercases():
    assert tickers.normalize([" msft", "AAPL", "aapl", "", "  "]) == ["AAPL", "MSFT"]


def test_read_ticker_file(tmp_path):
    f = tmp_path / "t.txt"
    f.write_text("# my list\nAAPL, MSFT\nNVDA  # comment\n\nBRK.B\n")
    assert tickers.read_ticker_file(f) == ["AAPL", "MSFT", "NVDA", "BRK.B"]


def test_sec_headers_require_user_agent(monkeypatch):
    monkeypatch.delenv(tickers.USER_AGENT_ENV, raising=False)
    with pytest.raises(tickers.MissingUserAgentError):
        tickers.sec_headers()


def test_sec_headers_from_env(monkeypatch):
    monkeypatch.setenv(tickers.USER_AGENT_ENV, "Jane Doe jane@example.com")
    assert tickers.sec_headers()["User-Agent"] == "Jane Doe jane@example.com"


def test_fetch_sec_tickers_sends_user_agent(monkeypatch):
    seen = {}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"0": {"ticker": "AAPL"}}

    def fake_get(url, headers, timeout):
        seen.update(url=url, headers=headers)
        return Resp()

    monkeypatch.setattr(tickers.requests, "get", fake_get)
    assert tickers.fetch_sec_tickers("Jane Doe jane@example.com") == ["AAPL"]
    assert seen["url"] == tickers.SEC_TICKERS_URL
    assert seen["headers"]["User-Agent"] == "Jane Doe jane@example.com"
