from datetime import date

import pandas as pd

from magic_formula.ranking import rank_stocks
from magic_formula.snapshot import TOP_N, snapshot_path, trim, trim_existing, write_snapshot


def test_trim_keeps_best_rows(raw_table):
    ranked = rank_stocks(raw_table)
    top = trim(ranked, 10)
    assert len(top) == 10
    assert list(top["Final_Rank"]) == list(range(1, 11))


def test_trim_shorter_than_limit_unchanged(raw_table):
    assert len(trim(rank_stocks(raw_table), 500)) == len(raw_table)


def test_write_snapshot_is_readable_by_notebooks(tmp_path, raw_table):
    path = write_snapshot(rank_stocks(raw_table), tmp_path, top_n=20, on=date(2026, 1, 2))
    assert path == tmp_path / "stocks_2026-01-02.csv"
    loaded = pd.read_csv(path, index_col=0)  # how Backtesting.ipynb loads snapshots
    assert len(loaded) == 20
    assert {"Ticker", "Final_Rank", "Market Cap", "Price"} <= set(loaded.columns)
    assert loaded["Final_Rank"].min() == 1


def test_default_top_n_is_100():
    assert TOP_N == 100


def test_trim_existing_rewrites_only_oversized(tmp_path, raw_table):
    ranked = rank_stocks(raw_table)
    big, small = tmp_path / "stocks_2026-01-01.csv", tmp_path / "stocks_2026-02-01.csv"
    ranked.to_csv(big)
    ranked.head(5).to_csv(small)
    changed = trim_existing(tmp_path, top_n=10)
    assert changed == [big]
    assert len(pd.read_csv(big, index_col=0)) == 10
    assert len(pd.read_csv(small, index_col=0)) == 5


def test_snapshot_path_defaults_to_today(tmp_path):
    assert snapshot_path(tmp_path).name == f"stocks_{date.today()}.csv"
