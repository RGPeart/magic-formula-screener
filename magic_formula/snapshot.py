"""Write and trim dated ``Results/stocks_YYYY-MM-DD.csv`` snapshots.

Only the top ``TOP_N`` rows by ``Final_Rank`` are published. Rank columns keep the values
computed against the full scraped universe, so a trimmed row's rank is still meaningful.
"""

from datetime import date
from pathlib import Path

import pandas as pd

TOP_N = 100


def trim(df: pd.DataFrame, top_n: int = TOP_N) -> pd.DataFrame:
    return df.sort_values("Final_Rank").head(top_n)


def snapshot_path(results_dir: str | Path, on: date | None = None) -> Path:
    return Path(results_dir) / f"stocks_{on or date.today()}.csv"


def write_snapshot(df: pd.DataFrame, results_dir: str | Path = "Results",
                   top_n: int = TOP_N, on: date | None = None) -> Path:  # fmt: skip
    """Write the top ``top_n`` rows. The index is kept: the notebooks read ``index_col=0``."""
    path = snapshot_path(results_dir, on)
    path.parent.mkdir(parents=True, exist_ok=True)
    trim(df, top_n).to_csv(path)
    return path


def trim_existing(results_dir: str | Path = "Results", top_n: int = TOP_N) -> list[Path]:
    """Rewrite every ``stocks_*.csv`` in place, keeping the top ``top_n`` rows."""
    changed = []
    for path in sorted(Path(results_dir).glob("stocks_*.csv")):
        df = pd.read_csv(path, index_col=0)
        if len(df) > top_n:
            trim(df, top_n).to_csv(path)
            changed.append(path)
    return changed
