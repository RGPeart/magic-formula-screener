# ruff: noqa: E501
import numpy as np
import pandas as pd

from magic_formula.ranking import WEIGHTS, rank_stocks


def reference_rank(stocks_df: pd.DataFrame) -> pd.DataFrame:
    """The original notebook's ranking cell, kept verbatim as an independent oracle."""
    stocks_df = stocks_df.copy()
    stocks_df["EarningsYield_Rank"] = stocks_df["Earnings Yield"].rank(ascending=False, na_option="bottom")
    stocks_df["ROC_Rank"] = stocks_df["Return On Capital"].rank(ascending=False, na_option="bottom")
    stocks_df["EY_ROC_Combined_Rank"] = stocks_df["Earnings Yield"].rank(
        ascending=False, na_option="bottom"
    ) + stocks_df["Return On Capital"].rank(ascending=False, na_option="bottom")
    stocks_df["MagicFormula_Rank"] = stocks_df["EY_ROC_Combined_Rank"].rank(method="first")
    stocks_df["TrailingPE_Rank"] = np.abs(np.subtract(22.5, stocks_df["Trailing P/E"].astype(float))).rank(
        ascending=True, na_option="bottom"
    )
    stocks_df["PEGRatio_Rank"] = np.abs(np.subtract(0.5, stocks_df["PEG Ratio"].astype(float))).rank(
        ascending=True, na_option="bottom"
    )
    stocks_df["PriceSales_Rank"] = (
        np.abs(np.subtract(1.5, stocks_df["Price to Sales Ratio"].astype(float)))
        .abs()
        .rank(ascending=True, na_option="bottom")
    )
    stocks_df["PriceBook_Rank"] = np.abs(
        np.subtract(0.5, stocks_df["Price to Book Ratio"].astype(float))
    ).rank(ascending=True, na_option="bottom")
    stocks_df["EnterpriseValue_Rank"] = stocks_df["Enterprise Value"].rank(ascending=True, na_option="bottom")
    stocks_df["EnterpriseRevenue_Rank"] = np.abs(
        np.subtract(2, stocks_df["Enterprise to Revenue"].astype(float))
    ).rank(ascending=True, na_option="bottom")
    stocks_df["EnterpriseEBITDA_Rank"] = np.abs(
        np.subtract(5, stocks_df["Enterprise to EBITDA"].astype(float))
    ).rank(ascending=True, na_option="bottom")
    stocks_df["PriceFreeCashFlow_Rank"] = np.abs(stocks_df["Price to Free Cash Flow"].astype(float)).rank(
        ascending=True, na_option="bottom"
    )
    stocks_df["PriceMomentum_20Day_Rank"] = stocks_df["Price Momentum (20 Days)"].rank(
        ascending=False, na_option="bottom"
    )
    stocks_df["PriceMomentum_1Year_Rank"] = stocks_df["Price Momentum (1 Year)"].rank(
        ascending=False, na_option="bottom"
    )
    stocks_df["Combined_Rank"] = (
        (stocks_df["MagicFormula_Rank"] * 2.0)
        + stocks_df["TrailingPE_Rank"]
        + stocks_df["PEGRatio_Rank"]
        + stocks_df["PriceSales_Rank"]
        + stocks_df["PriceBook_Rank"]
        + stocks_df["EnterpriseValue_Rank"]
        + stocks_df["EnterpriseRevenue_Rank"]
        + stocks_df["EnterpriseEBITDA_Rank"]
        + stocks_df["PriceFreeCashFlow_Rank"]
        + (stocks_df["PriceMomentum_20Day_Rank"] * 0.5)
        + (stocks_df["PriceMomentum_1Year_Rank"] * 0.5)
    )
    stocks_df["Final_Rank"] = stocks_df["Combined_Rank"].rank(method="first")
    return stocks_df.sort_values(by="Final_Rank", ascending=True)


def test_matches_original_notebook_logic(raw_table):
    expected = reference_rank(raw_table)
    actual = rank_stocks(raw_table)
    pd.testing.assert_frame_equal(actual, expected, check_dtype=False)


def test_final_rank_is_a_permutation(raw_table):
    ranked = rank_stocks(raw_table)
    assert sorted(ranked["Final_Rank"]) == list(range(1, len(raw_table) + 1))
    assert ranked["Final_Rank"].is_monotonic_increasing


def test_input_is_not_mutated(raw_table):
    before = raw_table.copy()
    rank_stocks(raw_table)
    pd.testing.assert_frame_equal(raw_table, before)


def test_higher_earnings_yield_and_roc_ranks_first(raw_table):
    ranked = rank_stocks(raw_table)
    best = ranked.sort_values("EY_ROC_Combined_Rank").iloc[0]
    assert best["MagicFormula_Rank"] == 1


def test_missing_values_rank_last(raw_table):
    ranked = rank_stocks(raw_table)
    missing = ranked[ranked["PEG Ratio"].isna()]["PEGRatio_Rank"]
    present = ranked[ranked["PEG Ratio"].notna()]["PEGRatio_Rank"]
    assert missing.min() > present.max()


def test_target_rank_prefers_values_near_target():
    df = pd.DataFrame({"Trailing P/E": [22.5, 10.0, 60.0]})
    from magic_formula.ranking import _num, _rank

    ranks = _rank(abs(_num(df["Trailing P/E"]) - 22.5), ascending=True)
    assert list(ranks) == [1.0, 2.0, 3.0]


def test_weights_sum():
    assert WEIGHTS["MagicFormula_Rank"] == 2.0
    assert sum(WEIGHTS.values()) == 2.0 + 8 * 1.0 + 2 * 0.5
