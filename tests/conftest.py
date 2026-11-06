import numpy as np
import pandas as pd
import pytest

from magic_formula.scrape import COLUMNS


@pytest.fixture
def raw_table() -> pd.DataFrame:
    """Random scraped-style table with missing values sprinkled in."""
    rng = np.random.default_rng(42)
    n = 60
    df = pd.DataFrame(
        {
            "Company Name": [f"Company {i}" for i in range(n)],
            "Ticker": [f"T{i:03d}" for i in range(n)],
            "Market Cap": rng.integers(2e8, 5e10, n),
            "Price": rng.uniform(2, 300, n).round(2),
            "Earnings Yield": rng.normal(6, 8, n),
            "Return On Capital": rng.normal(20, 40, n),
            "Trailing P/E": rng.uniform(2, 60, n),
            "PEG Ratio": rng.uniform(0.1, 4, n),
            "Price to Sales Ratio": rng.uniform(0.2, 12, n),
            "Price to Book Ratio": rng.uniform(0.2, 10, n),
            "Enterprise Value": rng.integers(2e8, 6e10, n),
            "Enterprise to Revenue": rng.uniform(0.2, 12, n),
            "Enterprise to EBITDA": rng.uniform(-5, 30, n),
            "Price to Free Cash Flow": rng.normal(15, 30, n),
            "Price Momentum (20 Days)": rng.normal(1, 8, n),
            "Price Momentum (1 Year)": rng.normal(10, 40, n),
        }
    )[COLUMNS]
    for col in ["Trailing P/E", "PEG Ratio", "Price to Free Cash Flow", "Return On Capital"]:
        df.loc[rng.choice(n, 6, replace=False), col] = np.nan
    return df
