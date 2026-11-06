# magic-formula-screener

A stock screener that combines Joel Greenblatt's **Magic Formula** (from *The Little Book That Still Beats the Market*) with valuation and momentum signals, plus a backtest of its monthly picks against the S&P 500.

> **Disclaimer:** this is a personal research project, for education only. It is not investment advice, and nothing here is a recommendation to buy or sell any security. Data comes from Yahoo Finance through `yfinance` and may be wrong, delayed or missing. Past results do not predict future returns.

## What it does

1. **Universe**: downloads the SEC's public ticker list (about 10K symbols).
2. **Scrape**: pulls fundamentals and price history per ticker with [yfinance](https://github.com/ranaroussi/yfinance). Drops companies under $200M market cap and the Utilities and Financial Services sectors.
3. **Rank**: orders what is left by `Final_Rank`, the rank of a weighted sum of component ranks (lower is better):

   | Component | Weight |
   |-----------|--------|
   | Magic Formula (earnings yield rank + return-on-capital rank, re-ranked) | 2.0 |
   | Trailing P/E, PEG, price/sales, price/book, enterprise value, EV/revenue, EV/EBITDA, price/free cash flow | 1.0 each |
   | 20-day and 1-year price momentum | 0.5 each |

   Most valuation ranks score distance from a target value (P/E 22.5, PEG 0.5, P/S 1.5, P/B 0.5, EV/Revenue 2, EV/EBITDA 5). See [`magic_formula/ranking.py`](magic_formula/ranking.py).
4. **Snapshot**: writes the **top 100** rows to `Results/stocks_YYYY-MM-DD.csv`. A GitHub Actions workflow does this on the 1st of every month.

## Quickstart

Python 3.11 or newer.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Try it on a handful of tickers (a few seconds)
python -m magic_formula run --tickers MSFT HPQ CROX EPAM YELP --results-dir /tmp/try

# Full run over the SEC universe (a couple of hours)
export SEC_USER_AGENT="Your Name your@email.com"   # the SEC requires scrapers to identify themselves
python -m magic_formula run
```

Options: `--tickers-file FILE`, `--extra-tickers-file FILE` (added to the SEC list), `--limit N`, `--top N`, `--results-dir DIR`. `python -m magic_formula trim` shrinks existing snapshots in place.

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `Magic_Formula_Investing_Project.ipynb` | Walkthrough of scrape, rank and save on a small sample |
| `Backtesting.ipynb` | Loads every snapshot, takes the top 10, and compares equal-weight 1, 3, 6 and 12-month returns with SPY (bar charts, heatmap, compounded $10K curve) |
| `Screener_Dashboard.ipynb` | Dash app to re-rank the latest snapshot by any mix of rank columns, filtered by market cap, price or name |

Notebooks are committed without outputs (`nbstripout`). The backtest has no transaction costs, equal weights, survivorship bias (delisted tickers drop out), and only about three dozen snapshots, so treat its numbers as illustrative.

Result of the backtest on the shipped snapshots (top 10 by `Final_Rank`, equal weight, run 2026-11-06; 14 of 123 picked tickers had no price history and were skipped):

| Hold | Snapshots | Avg portfolio | Avg SPY | Avg edge | Beat SPY |
|------|-----------|---------------|---------|----------|----------|
| 1M | 35 | +1.38% | +1.19% | +0.19% | 51% |
| 3M | 33 | +4.11% | +3.85% | +0.26% | 55% |
| 6M | 29 | +9.27% | +9.44% | -0.17% | 48% |
| 12M | 23 | +19.70% | +18.13% | +1.56% | 48% |

In short: roughly market-like, with no reliable edge so far. Overlapping windows and survivorship bias mean even that is generous.

## Data

`Results/` holds monthly snapshots of derived metrics (ratios and ranks) for the top 100 stocks, from March 2024. Each row keeps the rank values computed against the whole screened universe, so a row's `Final_Rank` is only comparable within its own snapshot. Underlying data is from Yahoo Finance for personal and educational use; check [Yahoo's terms](https://policies.yahoo.com/us/en/yahoo/terms/index.htm) before reusing it.

## Development

```bash
pytest          # unit tests, no network
ruff check . && ruff format --check .
nbstripout *.ipynb   # clear notebook outputs before committing
```

`tests/test_ranking.py` checks the ranking against the original notebook's formulas on random data with missing values.

## License

[MIT](LICENSE)
