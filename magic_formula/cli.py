"""Command line entry point: ``python -m magic_formula``."""

import argparse
import sys

from magic_formula import snapshot, tickers
from magic_formula.ranking import rank_stocks
from magic_formula.scrape import scrape


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="magic_formula", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="scrape, rank and write today's snapshot")
    run.add_argument("--tickers", nargs="+", metavar="SYM",
                     help="screen only these tickers instead of the full SEC list")  # fmt: skip
    run.add_argument("--tickers-file", help="text file of tickers (one per line or comma separated)")
    run.add_argument("--extra-tickers-file",
                     help="add tickers from this file to the SEC list")  # fmt: skip
    run.add_argument("--limit", type=int, help="only process the first N tickers (smoke test)")
    run.add_argument("--results-dir", default="Results")
    run.add_argument("--top", type=int, default=snapshot.TOP_N,
                     help=f"rows to keep in the snapshot (default {snapshot.TOP_N})")  # fmt: skip

    trim = sub.add_parser("trim", help="trim existing snapshots to the top N rows in place")
    trim.add_argument("--results-dir", default="Results")
    trim.add_argument("--top", type=int, default=snapshot.TOP_N)
    return p


def resolve_universe(args: argparse.Namespace) -> list[str]:
    if args.tickers or args.tickers_file:
        names = list(args.tickers or [])
        if args.tickers_file:
            names += tickers.read_ticker_file(args.tickers_file)
    else:
        names = tickers.fetch_sec_tickers()
        if args.extra_tickers_file:
            names += tickers.read_ticker_file(args.extra_tickers_file)
    universe = tickers.normalize(names)
    return universe[: args.limit] if args.limit else universe


def cmd_run(args: argparse.Namespace) -> int:
    universe = resolve_universe(args)
    print(f"Screening {len(universe)} tickers...")
    raw, stats = scrape(universe)
    print(stats.summary())
    if raw.empty:
        print("No stocks passed the filters; nothing written.", file=sys.stderr)
        return 1
    path = snapshot.write_snapshot(rank_stocks(raw), args.results_dir, args.top)
    print(f"Wrote {path}")
    return 0


def cmd_trim(args: argparse.Namespace) -> int:
    changed = snapshot.trim_existing(args.results_dir, args.top)
    print(f"Trimmed {len(changed)} file(s) to the top {args.top} rows")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return {"run": cmd_run, "trim": cmd_trim}[args.command](args)
    except tickers.MissingUserAgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
