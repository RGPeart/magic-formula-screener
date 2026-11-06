"""Rank scraped stocks.

Final_Rank is the rank of a weighted sum of component ranks (lower is better):
Magic Formula x2, eight valuation ranks x1, two momentum ranks x0.5.
"""

import numpy as np
import pandas as pd

# column -> target value; rank is distance from the target (closer is better)
TARGET_RANKS = {
    "TrailingPE_Rank": ("Trailing P/E", 22.5),
    "PEGRatio_Rank": ("PEG Ratio", 0.5),
    "PriceSales_Rank": ("Price to Sales Ratio", 1.5),
    "PriceBook_Rank": ("Price to Book Ratio", 0.5),
    "EnterpriseRevenue_Rank": ("Enterprise to Revenue", 2.0),
    "EnterpriseEBITDA_Rank": ("Enterprise to EBITDA", 5.0),
}

# Combined_Rank weights; MagicFormula_Rank is the Earnings Yield + ROC composite.
WEIGHTS = {
    "MagicFormula_Rank": 2.0,
    "TrailingPE_Rank": 1.0,
    "PEGRatio_Rank": 1.0,
    "PriceSales_Rank": 1.0,
    "PriceBook_Rank": 1.0,
    "EnterpriseValue_Rank": 1.0,
    "EnterpriseRevenue_Rank": 1.0,
    "EnterpriseEBITDA_Rank": 1.0,
    "PriceFreeCashFlow_Rank": 1.0,
    "PriceMomentum_20Day_Rank": 0.5,
    "PriceMomentum_1Year_Rank": 0.5,
}


def _rank(series: pd.Series, ascending: bool) -> pd.Series:
    return series.rank(ascending=ascending, na_option="bottom")


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float)


def rank_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """Add rank columns and return the table sorted by ``Final_Rank`` (best first)."""
    out = df.copy()

    out["EarningsYield_Rank"] = _rank(_num(out["Earnings Yield"]), ascending=False)
    out["ROC_Rank"] = _rank(_num(out["Return On Capital"]), ascending=False)
    out["EY_ROC_Combined_Rank"] = out["EarningsYield_Rank"] + out["ROC_Rank"]
    out["MagicFormula_Rank"] = out["EY_ROC_Combined_Rank"].rank(method="first")

    # Column order matches the historical CSVs: valuation ranks in this order.
    for rank_col in WEIGHTS:
        if rank_col in TARGET_RANKS:
            source, target = TARGET_RANKS[rank_col]
            out[rank_col] = _rank(np.abs(_num(out[source]) - target), ascending=True)
        elif rank_col == "EnterpriseValue_Rank":
            out[rank_col] = _rank(_num(out["Enterprise Value"]), ascending=True)
        elif rank_col == "PriceFreeCashFlow_Rank":
            out[rank_col] = _rank(np.abs(_num(out["Price to Free Cash Flow"])), ascending=True)

    out["PriceMomentum_20Day_Rank"] = _rank(_num(out["Price Momentum (20 Days)"]), False)
    out["PriceMomentum_1Year_Rank"] = _rank(_num(out["Price Momentum (1 Year)"]), False)

    out["Combined_Rank"] = sum(out[col] * weight for col, weight in WEIGHTS.items())
    out["Final_Rank"] = out["Combined_Rank"].rank(method="first")
    return out.sort_values("Final_Rank")
