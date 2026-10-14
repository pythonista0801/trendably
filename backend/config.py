"""Settings. Which stocks to analyse is set in universe.json, not here."""

UNIVERSE_FILE = "universe.json"
SP500_SOURCE = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

HISTORY_PERIOD = "10y"       # download more than 5 years, so the 5-year window has warm-up days

# Return windows: id -> (label, trading days). A stock is scored for a window only if it has enough history.
WINDOWS = {
    "1y": ("1 year",  252),
    "3y": ("3 years", 756),
    "5y": ("5 years", 1260),
}
DEFAULT_WINDOW = "5y"
WARMUP_DAYS = 260            # days before each window where indicators fill up but no trading happens
                             # (must exceed the longest look-back, currently momentum's 252 days)
WORKERS = None               # parallel processes for the grid; None = one per CPU core

STARTING_CASH = 10_000
COMMISSION = 0.0             # Alpaca-style zero commission

DATA_DIR = "cache"                   # downloaded price and S&P 500 files (Trendably layout: was "data")
OUTPUT_FILE = "data/grid.json"       # results the pages read (Trendably layout: was "frontend/data/grid.json")
