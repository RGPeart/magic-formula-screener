import pandas as pd

from magic_formula import cli, tickers
from magic_formula.scrape import ScrapeStats


def test_run_writes_trimmed_snapshot(monkeypatch, tmp_path, raw_table):
    stats = ScrapeStats()
    stats.add("kept")
    monkeypatch.setattr(cli, "scrape", lambda universe: (raw_table, stats))
    code = cli.main(["run", "--tickers", "aapl", "msft", "--results-dir", str(tmp_path), "--top", "5"])
    assert code == 0
    (out,) = tmp_path.glob("stocks_*.csv")
    assert len(pd.read_csv(out, index_col=0)) == 5


def test_run_without_user_agent_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv(tickers.USER_AGENT_ENV, raising=False)
    assert cli.main(["run", "--results-dir", str(tmp_path)]) == 2
    assert "SEC_USER_AGENT" in capsys.readouterr().err


def test_run_with_nothing_scraped_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "scrape", lambda universe: (pd.DataFrame(), ScrapeStats()))
    assert cli.main(["run", "--tickers", "AAPL", "--results-dir", str(tmp_path)]) == 1
    assert not list(tmp_path.glob("*.csv"))


def test_limit_applies_after_sort(monkeypatch):
    args = cli.build_parser().parse_args(["run", "--tickers", "zzz", "aaa", "mmm", "--limit", "2"])
    assert cli.resolve_universe(args) == ["AAA", "MMM"]


def test_trim_command(tmp_path, raw_table):
    from magic_formula.ranking import rank_stocks

    rank_stocks(raw_table).to_csv(tmp_path / "stocks_2026-01-01.csv")
    assert cli.main(["trim", "--results-dir", str(tmp_path), "--top", "7"]) == 0
    assert len(pd.read_csv(tmp_path / "stocks_2026-01-01.csv", index_col=0)) == 7
