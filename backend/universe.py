"""Which stocks to analyse — the S&P 500 with its official GICS classification, filtered by universe.json."""

import json
import os
from datetime import date
from io import StringIO

import pandas as pd
import requests

from config import DATA_DIR, SP500_SOURCE, UNIVERSE_FILE


def load_sp500(refresh: bool = False) -> pd.DataFrame:
    """All S&P 500 companies with GICS sector and sub-industry. Downloaded once a month, then cached."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"sp500_{date.today():%Y-%m}.csv")
    if os.path.exists(path) and not refresh:
        return pd.read_csv(path)

    html = requests.get(SP500_SOURCE, headers={"User-Agent": "FinStrategyGrid/0.1"}, timeout=30).text
    table = pd.read_html(StringIO(html), attrs={"id": "constituents"})[0]
    df = pd.DataFrame({
        "ticker":           table["Symbol"].str.replace(".", "-", regex=False),  # BRK.B -> BRK-B for Yahoo
        "name":             table["Security"],
        "gics_sector":      table["GICS Sector"],
        "gics_sub_industry": table["GICS Sub-Industry"],
    })
    df.to_csv(path, index=False)
    return df


def _lower(values):
    return {v.strip().lower() for v in values}


def load_universe() -> pd.DataFrame:
    """The S&P 500 narrowed down by the rules in universe.json."""
    with open(UNIVERSE_FILE) as f:
        rules = json.load(f)
    sp = load_sp500()
    keep = pd.Series(True, index=sp.index)

    if rules.get("gics_sectors"):
        keep &= sp["gics_sector"].str.lower().isin(_lower(rules["gics_sectors"]))
    if rules.get("gics_sub_industries"):
        keep &= sp["gics_sub_industry"].str.lower().isin(_lower(rules["gics_sub_industries"]))
    if rules.get("include_tickers"):
        keep |= sp["ticker"].str.upper().isin({t.upper() for t in rules["include_tickers"]})
    if rules.get("exclude_tickers"):
        keep &= ~sp["ticker"].str.upper().isin({t.upper() for t in rules["exclude_tickers"]})

    chosen = sp[keep].sort_values(["gics_sector", "gics_sub_industry", "ticker"]).reset_index(drop=True)
    if chosen.empty:
        raise ValueError("No stocks match universe.json. Run 'python backend/run.py --list' to see valid names.")
    return chosen


def print_classification():
    """Show every GICS sector and sub-industry in the S&P 500, with stock counts."""
    sp = load_sp500()
    for sector, group in sp.groupby("gics_sector"):
        print(f"\n{sector} ({len(group)})")
        for sub, n in group["gics_sub_industry"].value_counts().sort_index().items():
            print(f"    {sub} ({n})")
