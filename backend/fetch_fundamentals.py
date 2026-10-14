"""
Fetch fundamental data from Yahoo Finance for all S&P 500 stocks.

Fetches S4 data (P/E, growth rates, margins, etc.) and caches to avoid rate limits.
Run nightly as fundamentals change slowly (quarterly earnings).

Usage:
    python backend/fetch_fundamentals.py
    python backend/fetch_fundamentals.py --stocks NVDA AAPL  # Specific stocks only
"""

import json
import time
from pathlib import Path
from datetime import datetime
import argparse

try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance not installed. Run: pip install yfinance")
    exit(1)

from config import DATA_DIR
from universe import load_sp500


def fetch_fundamental(ticker: str) -> dict:
    """Fetch fundamental data for one stock from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extract fundamental fields (S4 from DATA-SPEC)
        # Note: Yahoo's debtToEquity is a percentage, divide by 100
        fundamental = {
            'ticker': ticker,
            'fetchedAt': datetime.now().isoformat(),

            # Valuation
            'trailingPE': info.get('trailingPE'),
            'forwardPE': info.get('forwardPE'),
            'enterpriseToEbitda': info.get('enterpriseToEbitda'),
            'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months'),
            'priceToBook': info.get('priceToBook'),

            # Growth
            'revenueGrowth': info.get('revenueGrowth'),  # Already a decimal (0.943 = 94.3%)
            'earningsGrowth': info.get('earningsGrowth'),

            # Profitability
            'profitMargins': info.get('profitMargins'),  # Already a decimal
            'returnOnEquity': info.get('returnOnEquity'),

            # Financial health
            'freeCashflow': info.get('freeCashflow'),
            'debtToEquity': info.get('debtToEquity') / 100 if info.get('debtToEquity') is not None else None,

            # Company info
            'sector': info.get('sector'),
            'industry': info.get('industry'),  # Yahoo's industry (not GICS)
            'marketCap': info.get('marketCap'),
            'sharesOutstanding': info.get('sharesOutstanding'),
        }

        return fundamental

    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return {
            'ticker': ticker,
            'fetchedAt': datetime.now().isoformat(),
            'error': str(e)
        }


def fetch_all_fundamentals(tickers: list[str], delay: float = 0.5) -> dict:
    """
    Fetch fundamentals for a list of tickers.

    Args:
        tickers: List of ticker symbols
        delay: Seconds to wait between requests (avoid rate limiting)

    Returns:
        Dict mapping ticker -> fundamental data
    """
    fundamentals = {}
    total = len(tickers)

    print(f"Fetching fundamentals for {total} stocks...")
    print(f"(Rate limit: {delay}s between requests)")

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] {ticker}...", end=' ', flush=True)

        fund = fetch_fundamental(ticker)
        fundamentals[ticker] = fund

        if 'error' in fund:
            print(f"✗ {fund['error']}")
        else:
            print("✓")

        # Rate limiting
        if i < total:
            time.sleep(delay)

    return fundamentals


def save_fundamentals(fundamentals: dict):
    """Save fundamentals cache to disk."""
    cache_dir = Path(DATA_DIR)
    cache_dir.mkdir(exist_ok=True)

    cache_file = cache_dir / "fundamentals.json"

    data = {
        'fetchedAt': datetime.now().isoformat(),
        'count': len(fundamentals),
        'stocks': fundamentals
    }

    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✓ Saved {len(fundamentals)} fundamentals to {cache_file}")


def load_fundamentals() -> dict:
    """Load cached fundamentals if they exist."""
    cache_file = Path(DATA_DIR) / "fundamentals.json"

    if not cache_file.exists():
        return {}

    with open(cache_file) as f:
        data = json.load(f)

    return data.get('stocks', {})


def main():
    parser = argparse.ArgumentParser(description='Fetch fundamental data from Yahoo Finance')
    parser.add_argument('--stocks', nargs='+', help='Specific stocks to fetch (default: all in universe)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--update', action='store_true', help='Update existing cache (only fetch missing)')

    args = parser.parse_args()

    # Determine which stocks to fetch
    if args.stocks:
        tickers = args.stocks
        print(f"Fetching specific stocks: {', '.join(tickers)}")
    else:
        universe = load_sp500()
        tickers = universe['ticker'].tolist()
        print(f"Fetching all stocks from S&P 500 ({len(tickers)} total)")

    # If updating, load existing cache and only fetch missing
    if args.update:
        existing = load_fundamentals()
        tickers = [t for t in tickers if t not in existing]
        print(f"Update mode: {len(tickers)} stocks need fetching")

        if not tickers:
            print("All stocks already cached!")
            return

    # Fetch fundamentals
    fundamentals = fetch_all_fundamentals(tickers, delay=args.delay)

    # If updating, merge with existing cache
    if args.update:
        existing = load_fundamentals()
        existing.update(fundamentals)
        fundamentals = existing

    # Save to cache
    save_fundamentals(fundamentals)

    # Summary
    errors = sum(1 for f in fundamentals.values() if 'error' in f)
    print(f"\nSummary: {len(fundamentals)} stocks, {errors} errors")


if __name__ == '__main__':
    main()
