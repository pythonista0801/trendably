"""Price data for any ticker. Downloads from Yahoo Finance once a month, then reuses the saved file."""

import os
from datetime import date

import pandas as pd
import yfinance as yf

from config import DATA_DIR, HISTORY_PERIOD

FIELDS = ["Open", "High", "Low", "Close", "Volume"]


def _path(ticker: str) -> str:
    return os.path.join(DATA_DIR, f"{ticker}_{HISTORY_PERIOD}_{date.today():%Y-%m}.csv")   # one file per month


def _tidy(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):          # newer yfinance returns two-level column names
        df.columns = df.columns.get_level_values(0)
    return df[FIELDS].dropna()


def prefetch(tickers: list[str], batch: int = 50):
    """Download every ticker not yet cached this month, 50 at a time (much faster than one by one)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    missing = [t for t in tickers if not os.path.exists(_path(t))]
    for i in range(0, len(missing), batch):
        group = missing[i:i + batch]
        print(f"  downloading prices {i + 1}-{i + len(group)} of {len(missing)}")
        try:
            df = yf.download(group, period=HISTORY_PERIOD, auto_adjust=True, progress=False,
                             group_by="ticker", threads=True)
        except Exception as e:
            print(f"  batch failed ({e}); those stocks will be tried one by one")
            continue
        for t in group:
            try:
                one = _tidy(df[t].copy() if len(group) > 1 else df.copy())
                if not one.empty:
                    one.to_csv(_path(t))
            except KeyError:
                pass                                   # not in this batch's result; retried one by one later


def get_prices(ticker: str, refresh: bool = False) -> pd.DataFrame:
    """Return daily Open/High/Low/Close/Volume for one ticker."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = _path(ticker)
    if os.path.exists(path) and not refresh:
        return pd.read_csv(path, index_col=0, parse_dates=True)

    df = yf.download(ticker, period=HISTORY_PERIOD, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No price data returned for {ticker}")
    df = _tidy(df)
    df.to_csv(path)
    return df
