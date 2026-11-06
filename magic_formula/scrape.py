"""Fetch fundamentals and price momentum for each ticker via yfinance."""

import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import yfinance as yf

MIN_MARKET_CAP = 200_000_000
EXCLUDED_SECTORS = frozenset({"Utilities", "Financial Services"})

COLUMNS = [
    "Company Name", "Ticker", "Market Cap", "Price",
    "Earnings Yield", "Return On Capital",
    "Trailing P/E", "PEG Ratio", "Price to Sales Ratio", "Price to Book Ratio",
    "Enterprise Value", "Enterprise to Revenue", "Enterprise to EBITDA",
    "Price to Free Cash Flow",
    "Price Momentum (20 Days)", "Price Momentum (1 Year)",
]  # fmt: skip


@dataclass
class ScrapeStats:
    """Why tickers were kept or dropped; printed at the end of a run."""

    counts: Counter = field(default_factory=Counter)

    def add(self, outcome: str) -> None:
        self.counts[outcome] += 1

    def summary(self) -> str:
        c = self.counts
        total = sum(c.values())
        return (
            f"analysed {total}: kept {c['kept']}, under ${MIN_MARKET_CAP // 1_000_000}M "
            f"market cap {c['small_cap']}, utilities/financials {c['excluded_sector']}, "
            f"errors {c['error']}"
        )


def price_momentum(close: pd.Series) -> float | None:
    """Percent change from the first to the last close, or None if unavailable."""
    close = close.dropna()
    if len(close) < 2 or close.iloc[0] == 0:
        return None
    return float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)


def momentum_windows(today: datetime | None = None) -> tuple[str, str, str]:
    """Return (start_1year, start_20days, end) as ``YYYY-MM-DD`` using business-day offsets."""
    today = today or datetime.today()
    fmt = "%Y-%m-%d"
    end = (today - pd.tseries.offsets.BDay(1)).strftime(fmt)
    start_20 = (today - pd.tseries.offsets.BDay(20)).strftime(fmt)
    start_1y = (today - pd.tseries.offsets.BDay(300)).strftime(fmt)
    return start_1y, start_20, end


def compute_row(info: dict, ebit: float, current_assets: float, current_liabilities: float,
                net_ppe: float, mom_20d: float | None, mom_1y: float | None,
                ticker: str) -> dict:  # fmt: skip
    """Assemble one output row from raw yfinance values (pure, unit-tested)."""
    market_cap = info.get("marketCap")
    enterprise_value = info.get("enterpriseValue")
    free_cash_flow = info.get("freeCashflow")
    invested_capital = net_ppe + current_assets - current_liabilities
    return {
        "Company Name": info.get("longName"),
        "Ticker": ticker,
        "Market Cap": market_cap,
        "Price": info.get("previousClose"),
        "Earnings Yield": ebit / enterprise_value * 100 if enterprise_value else None,
        "Return On Capital": ebit / invested_capital * 100 if invested_capital else None,
        "Trailing P/E": info.get("trailingPE"),
        "PEG Ratio": info.get("trailingPegRatio"),
        "Price to Sales Ratio": info.get("priceToSalesTrailing12Months"),
        "Price to Book Ratio": info.get("priceToBook"),
        "Enterprise Value": enterprise_value,
        "Enterprise to Revenue": info.get("enterpriseToRevenue"),
        "Enterprise to EBITDA": info.get("enterpriseToEbitda"),
        "Price to Free Cash Flow": market_cap / free_cash_flow if free_cash_flow else None,
        "Price Momentum (20 Days)": mom_20d,
        "Price Momentum (1 Year)": mom_1y,
    }


def fetch_stock(ticker: str, start_1y: str, start_20: str, end: str,
                stats: ScrapeStats) -> dict | None:  # fmt: skip
    """Return one row for ``ticker`` or None if it is filtered out or fails."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_1y, end=end)
        if hist.empty:
            raise ValueError("no price history")
        info = stock.info

        market_cap = info.get("marketCap")
        if market_cap is None or market_cap < MIN_MARKET_CAP:
            stats.add("small_cap")
            return None
        if info.get("sector") in EXCLUDED_SECTORS:
            stats.add("excluded_sector")
            return None

        income = stock.income_stmt.iloc[:, 0]
        balance = stock.balance_sheet.iloc[:, 0]
        close = hist["Close"]
        recent = close[close.index >= pd.Timestamp(start_20, tz=close.index.tz)]

        row = compute_row(
            info,
            ebit=income["EBIT"],
            current_assets=balance["Current Assets"],
            current_liabilities=balance["Current Liabilities"],
            net_ppe=balance["Net PPE"],
            mom_20d=price_momentum(recent),
            mom_1y=price_momentum(close),
            ticker=ticker,
        )
        stats.add("kept")
        return row
    except Exception as exc:  # yfinance raises many unrelated types for missing data
        print(f"  skip {ticker}: {exc}")
        stats.add("error")
        time.sleep(1)
        return None


def scrape(tickers: list[str], pause: float = 0.0) -> tuple[pd.DataFrame, ScrapeStats]:
    """Scrape every ticker and return the raw (unranked) table plus drop statistics."""
    start_1y, start_20, end = momentum_windows()
    stats = ScrapeStats()
    rows = []
    for i, ticker in enumerate(tickers, 1):
        row = fetch_stock(ticker, start_1y, start_20, end, stats)
        if row:
            rows.append(row)
        if i % 250 == 0:
            print(f"  {i}/{len(tickers)} tickers processed")
        if pause:
            time.sleep(pause)
    return pd.DataFrame(rows, columns=COLUMNS), stats
