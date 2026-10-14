"""Entry point. Always run from the project root (the trendably folder).

    python backend/run.py --list                     -> show all GICS sectors and sub-industries
    python backend/run.py                            -> every stock in universe.json x every strategy
    python backend/run.py --tickers NVDA             -> one stock, all strategies
    python backend/run.py --tickers NVDA --strategies macd           -> one stock, one strategy
    python backend/run.py --windows 1y                -> only the 1-year window
"""

import argparse
import time

from config import WINDOWS
from data import prefetch
from engine import run_grid, save
from strategies import REGISTRY
from universe import load_sp500, load_universe, print_classification


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="show GICS sectors and sub-industries")
    parser.add_argument("--tickers", nargs="+", help="override universe.json for a quick test")
    parser.add_argument("--strategies", nargs="+", default=list(REGISTRY), choices=list(REGISTRY))
    parser.add_argument("--windows", nargs="+", default=list(WINDOWS), choices=list(WINDOWS))
    args = parser.parse_args()

    if args.list:
        print_classification()
        return

    if args.tickers:
        sp = load_sp500()
        stocks = sp[sp["ticker"].isin([t.upper() for t in args.tickers])]
    else:
        stocks = load_universe()
    tickers = stocks["ticker"].tolist()

    start = time.time()
    print(f"Running {len(tickers)} stocks x {len(args.strategies)} strategies x {len(args.windows)} windows\n")
    prefetch(tickers)
    results, summaries, closes = run_grid(tickers, args.strategies, args.windows)
    save(results, summaries, closes, stocks, args.strategies, args.windows)
    print(f"Finished in {(time.time() - start) / 60:.1f} minutes")


if __name__ == "__main__":      # needed for parallel processing on Windows and Mac
    main()
