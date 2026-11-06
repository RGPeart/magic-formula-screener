import pandas as pd
import pytest

from magic_formula import scrape


def test_price_momentum():
    assert scrape.price_momentum(pd.Series([100.0, 110.0, 120.0])) == pytest.approx(20.0)


@pytest.mark.parametrize("series", [[], [5.0], [0.0, 3.0]])
def test_price_momentum_unavailable(series):
    assert scrape.price_momentum(pd.Series(series, dtype=float)) is None


def test_momentum_windows_are_ordered():
    start_1y, start_20, end = scrape.momentum_windows(pd.Timestamp("2026-11-06").to_pydatetime())
    assert start_1y < start_20 < end


INFO = {
    "longName": "Acme Corp", "marketCap": 1_000_000_000, "previousClose": 12.5,
    "enterpriseValue": 2_000_000_000, "freeCashflow": 50_000_000, "trailingPE": 15.0,
    "trailingPegRatio": 1.2, "priceToSalesTrailing12Months": 1.1, "priceToBook": 2.0,
    "enterpriseToRevenue": 2.1, "enterpriseToEbitda": 7.0, "sector": "Technology",
}  # fmt: skip


def test_compute_row_magic_formula_math():
    row = scrape.compute_row(INFO, ebit=200_000_000, current_assets=500_000_000,
                             current_liabilities=300_000_000, net_ppe=300_000_000,
                             mom_20d=1.5, mom_1y=10.0, ticker="ACME")  # fmt: skip
    assert row["Earnings Yield"] == pytest.approx(10.0)  # 200M / 2B
    assert row["Return On Capital"] == pytest.approx(40.0)  # 200M / (300+500-300)M
    assert row["Price to Free Cash Flow"] == pytest.approx(20.0)  # 1B / 50M
    assert list(row) == scrape.COLUMNS


def test_compute_row_missing_free_cash_flow():
    info = {**INFO, "freeCashflow": None}
    row = scrape.compute_row(info, 1, 1, 1, 1, None, None, "X")
    assert row["Price to Free Cash Flow"] is None


class FakeTicker:
    """Stands in for yfinance.Ticker; no network."""

    info: dict = INFO

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, start, end):
        idx = pd.bdate_range("2025-10-01", "2026-11-05")
        return pd.DataFrame({"Close": range(1, len(idx) + 1)}, index=idx)

    @property
    def income_stmt(self):
        return pd.DataFrame({"2025": {"EBIT": 200_000_000.0}})

    @property
    def balance_sheet(self):
        return pd.DataFrame({"2025": {"Current Assets": 5e8, "Current Liabilities": 3e8, "Net PPE": 3e8}})


def _fetch(monkeypatch, info):
    class T(FakeTicker):
        pass

    T.info = info
    monkeypatch.setattr(scrape.yf, "Ticker", T)
    stats = scrape.ScrapeStats()
    row = scrape.fetch_stock("ACME", "2025-10-01", "2026-10-08", "2026-11-05", stats)
    return row, stats


def test_fetch_stock_keeps_good_ticker(monkeypatch):
    row, stats = _fetch(monkeypatch, INFO)
    assert row["Ticker"] == "ACME" and stats.counts["kept"] == 1
    assert row["Price Momentum (20 Days)"] < row["Price Momentum (1 Year)"]


def test_fetch_stock_drops_small_cap(monkeypatch):
    row, stats = _fetch(monkeypatch, {**INFO, "marketCap": 50_000_000})
    assert row is None and stats.counts["small_cap"] == 1


@pytest.mark.parametrize("sector", ["Utilities", "Financial Services"])
def test_fetch_stock_drops_excluded_sectors(monkeypatch, sector):
    row, stats = _fetch(monkeypatch, {**INFO, "sector": sector})
    assert row is None and stats.counts["excluded_sector"] == 1


def test_fetch_stock_counts_errors(monkeypatch):
    monkeypatch.setattr(scrape.time, "sleep", lambda s: None)

    def boom(symbol):
        raise RuntimeError("network down")

    monkeypatch.setattr(scrape.yf, "Ticker", boom)
    stats = scrape.ScrapeStats()
    assert scrape.fetch_stock("ACME", "a", "b", "c", stats) is None
    assert stats.counts["error"] == 1
