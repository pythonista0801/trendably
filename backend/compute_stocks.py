"""
Generate data/stocks/<SYM>.json for each stock in the S&P 500.

Combines:
- S1 (price history) for returns, volatility, beta, technical indicators
- S2 (current quote) for price, change
- S3 (universe) for name, sector, sub-industry
- S4 (fundamentals) for valuation and fundamentals

Stage 1 (now): All raw indicators from DATA-SPEC D.7
Stage 2 (later): Percentile ranks and scores after full S&P 500 run
"""

import json
import os
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

from universe import load_sp500
from gics_mapping import get_breadcrumb
from strategies import sma, ema, rsi, macd_line


def calculate_volatility(returns, periods=252):
    """Annualized volatility from daily returns."""
    return returns.std() * np.sqrt(periods)


def calculate_beta(stock_returns, market_returns):
    """Beta vs market (^GSPC)."""
    covariance = np.cov(stock_returns, market_returns)[0][1]
    market_variance = np.var(market_returns)
    if market_variance == 0:
        return None
    return covariance / market_variance


def calculate_max_drawdown(prices):
    """Maximum drawdown from peak."""
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax
    return drawdown.min()


def calculate_downside_volatility(returns, periods=252):
    """Annualized downside volatility (only negative returns)."""
    negative_returns = returns[returns < 0]
    if len(negative_returns) == 0:
        return 0.0
    return negative_returns.std() * np.sqrt(periods)


def calculate_sharpe(returns, periods=252):
    """Sharpe ratio (assuming 0% risk-free rate)."""
    if returns.std() == 0:
        return None
    return (returns.mean() * periods) / (returns.std() * np.sqrt(periods))


def calculate_atr(high, low, close, period=14):
    """Average True Range."""
    high_low = high - low
    high_close = np.abs(high - close.shift(1))
    low_close = np.abs(low - close.shift(1))
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]


def load_fundamentals(ticker):
    """Load fundamental data from cache/fundamentals.json."""
    cache_path = Path("cache/fundamentals.json")
    if not cache_path.exists():
        return None

    with open(cache_path) as f:
        data = json.load(f)

    return data.get('stocks', {}).get(ticker)


def compute_stock_data(ticker, universe_row, sp500_hist, market_hist):
    """
    Compute all indicators for one stock.

    Returns dict matching data/stocks/<SYM>.json schema, or None if insufficient data.
    """
    print(f"Computing {ticker}...")

    # Fetch current quote (S2)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        price_change = info.get('regularMarketChange')
        price_change_pct = info.get('regularMarketChangePercent')
        current_volume = info.get('volume') or info.get('regularMarketVolume')

        if current_price is None:
            print(f"  ⚠ {ticker}: No current price available")
            return None
    except Exception as e:
        print(f"  ⚠ {ticker}: Failed to fetch quote: {e}")
        return None

    # Get price history (S1) - need at least 252 days for 1Y metrics
    if ticker not in sp500_hist or len(sp500_hist[ticker]) < 252:
        print(f"  ⚠ {ticker}: Insufficient price history")
        return None

    hist = sp500_hist[ticker].copy()
    closes = hist['Close']
    highs = hist['High']
    lows = hist['Low']
    volumes = hist['Volume']

    # Calculate returns
    returns = closes.pct_change().dropna()

    # Price and performance indicators
    ret_1m = (closes.iloc[-1] / closes.iloc[-21] - 1) * 100 if len(closes) >= 21 else None
    ret_3m = (closes.iloc[-1] / closes.iloc[-63] - 1) * 100 if len(closes) >= 63 else None
    ret_6m = (closes.iloc[-1] / closes.iloc[-126] - 1) * 100 if len(closes) >= 126 else None
    ret_1y = (closes.iloc[-1] / closes.iloc[-252] - 1) * 100 if len(closes) >= 252 else None

    high_52w = highs.iloc[-252:].max() if len(highs) >= 252 else None
    low_52w = lows.iloc[-252:].min() if len(lows) >= 252 else None
    from_high = ((closes.iloc[-1] / high_52w - 1) * 100) if high_52w else None

    # Momentum and trend indicators
    rsi_14 = rsi(closes.values, 14)[-1] if len(closes) >= 14 else None

    sma_20 = sma(closes.values, 20)[-1] if len(closes) >= 20 else None
    sma_50 = sma(closes.values, 50)[-1] if len(closes) >= 50 else None
    sma_200 = sma(closes.values, 200)[-1] if len(closes) >= 200 else None

    above_mas = sum([
        1 if sma_20 and closes.iloc[-1] > sma_20 else 0,
        1 if sma_50 and closes.iloc[-1] > sma_50 else 0,
        1 if sma_200 and closes.iloc[-1] > sma_200 else 0
    ])

    macd = None
    macd_rising = None
    if len(closes) >= 26:
        macd_values = macd_line(closes.values, 12, 26)
        signal_values = ema(macd_values, 9)
        if not np.isnan(macd_values[-1]):
            macd = round(macd_values[-1], 2)
            if len(macd_values) >= 2 and not np.isnan(macd_values[-2]):
                histogram_today = macd_values[-1] - signal_values[-1]
                histogram_yesterday = macd_values[-2] - signal_values[-2]
                macd_rising = bool(histogram_today > histogram_yesterday)

    # Risk and volatility indicators (1 year)
    returns_1y = returns.iloc[-252:] if len(returns) >= 252 else returns
    market_returns_1y = market_hist.iloc[-252:] if len(market_hist) >= 252 else market_hist

    vol = calculate_volatility(returns_1y) * 100 if len(returns_1y) > 1 else None
    beta_val = calculate_beta(returns_1y.values, market_returns_1y.values) if len(returns_1y) > 20 and len(market_returns_1y) > 20 else None
    mdd_1y = calculate_max_drawdown(closes.iloc[-252:]) * 100 if len(closes) >= 252 else None
    down_vol = calculate_downside_volatility(returns_1y) * 100 if len(returns_1y) > 1 else None
    sharpe = calculate_sharpe(returns_1y) if len(returns_1y) > 1 else None

    # Trading and activity indicators
    avg_vol_30 = volumes.iloc[-30:].mean() if len(volumes) >= 30 else None
    vol_vs_avg = None
    if avg_vol_30 and current_volume:
        vol_vs_avg = ((current_volume / avg_vol_30) - 1) * 100

    atr_14 = None
    if len(highs) >= 14 and len(lows) >= 14 and len(closes) >= 14:
        atr_14 = calculate_atr(highs, lows, closes, 14)

    # Liquidity classification
    liquidity = None
    if avg_vol_30 and current_price:
        dollar_volume = avg_vol_30 * current_price
        if dollar_volume > 1e9:
            liquidity = "Very high"
        elif dollar_volume > 250e6:
            liquidity = "High"
        elif dollar_volume > 50e6:
            liquidity = "Moderate"
        else:
            liquidity = "Low"

    # Load fundamentals (S4)
    fund = load_fundamentals(ticker)

    pe_trailing = fund.get('trailingPE') if fund else None
    pe_forward = fund.get('forwardPE') if fund else None
    ev_ebitda = fund.get('enterpriseToEbitda') if fund else None
    ps = fund.get('priceToSalesTrailing12Months') if fund else None
    pb = fund.get('priceToBook') if fund else None

    rev_growth = fund.get('revenueGrowth') * 100 if fund and fund.get('revenueGrowth') is not None else None
    eps_growth = fund.get('earningsGrowth') * 100 if fund and fund.get('earningsGrowth') is not None else None
    margin = fund.get('profitMargins') * 100 if fund and fund.get('profitMargins') is not None else None
    roe = fund.get('returnOnEquity') * 100 if fund and fund.get('returnOnEquity') is not None else None
    fcf = fund.get('freeCashflow') if fund else None
    de = fund.get('debtToEquity') if fund else None

    # Build breadcrumb
    sector = universe_row['gics_sector']
    sub_industry = universe_row['gics_sub_industry']
    breadcrumb = get_breadcrumb(sector, sub_industry)

    # Assemble stock data
    stock_data = {
        "asOf": datetime.now().isoformat(),
        "sym": ticker,
        "name": universe_row['name'],
        "sector": sector,
        "industry": breadcrumb,
        "price": round(current_price, 2) if current_price else None,
        "change": round(price_change, 2) if price_change else None,
        "move": round(price_change_pct, 2) if price_change_pct else None,

        # Scores - Stage 2 (marked as sample for now)
        "score": {
            "composite": None,
            "momentum": None,
            "risk": None,
            "valuation": None,
            "fundamentals": None,
            "note": "Stage 1: scores pending full S&P 500 run for percentile ranks"
        },

        # Raw indicators
        "indicators": {
            # Price and performance
            "ret1m": round(ret_1m, 1) if ret_1m is not None else None,
            "ret3m": round(ret_3m, 1) if ret_3m is not None else None,
            "ret6m": round(ret_6m, 1) if ret_6m is not None else None,
            "ret1y": round(ret_1y, 1) if ret_1y is not None else None,
            "fromHigh": round(from_high, 1) if from_high is not None else None,
            "high52": round(high_52w, 2) if high_52w is not None else None,
            "low52": round(low_52w, 2) if low_52w is not None else None,

            # Momentum and trend
            "rsi14": round(rsi_14, 0) if rsi_14 is not None and not np.isnan(rsi_14) else None,
            "aboveMAs": above_mas,
            "sma20": round(sma_20, 2) if sma_20 is not None and not np.isnan(sma_20) else None,
            "sma50": round(sma_50, 2) if sma_50 is not None and not np.isnan(sma_50) else None,
            "sma200": round(sma_200, 2) if sma_200 is not None and not np.isnan(sma_200) else None,
            "macd": macd,
            "macdRising": macd_rising,

            # Risk and volatility
            "vol": round(vol, 1) if vol is not None else None,
            "beta": round(beta_val, 2) if beta_val is not None else None,
            "mdd1y": round(mdd_1y, 1) if mdd_1y is not None else None,
            "downVol": round(down_vol, 1) if down_vol is not None else None,
            "sharpe": round(sharpe, 2) if sharpe is not None else None,

            # Valuation
            "pe": round(pe_trailing, 1) if pe_trailing is not None and pe_trailing > 0 else None,
            "fpe": round(pe_forward, 1) if pe_forward is not None and pe_forward > 0 else None,
            "peVsSector": None,  # Stage 2: needs sector median calculation
            "evEbitda": round(ev_ebitda, 1) if ev_ebitda is not None and ev_ebitda > 0 else None,
            "ps": round(ps, 1) if ps is not None else None,
            "pb": round(pb, 1) if pb is not None else None,

            # Fundamentals
            "revGrowth": round(rev_growth, 1) if rev_growth is not None else None,
            "epsGrowth": round(eps_growth, 1) if eps_growth is not None else None,
            "margin": round(margin, 1) if margin is not None else None,
            "roe": round(roe, 1) if roe is not None else None,
            "fcf": fcf,
            "de": round(de, 2) if de is not None else None,

            # Trading and activity
            "avgVol30": int(avg_vol_30) if avg_vol_30 is not None else None,
            "volVsAvg": round(vol_vs_avg, 0) if vol_vs_avg is not None else None,
            "atr14": round(atr_14, 2) if atr_14 is not None else None,
            "liquidity": liquidity
        },

        "about": None,  # Stage 2: meaning templates
        "news": []
    }

    return stock_data


def main():
    """Generate data/stocks/<SYM>.json for all S&P 500 stocks."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate stock detail JSON files")
    parser.add_argument('--stocks', nargs='*', help='Specific tickers to process (default: all S&P 500)')
    args = parser.parse_args()

    # Load universe
    sp500 = load_sp500()

    if args.stocks:
        sp500 = sp500[sp500['ticker'].isin(args.stocks)]
        if len(sp500) == 0:
            print("No matching stocks found")
            return

    print(f"Processing {len(sp500)} stocks...")

    # Load market data for beta calculation
    print("Loading market data (^GSPC)...")
    market = yf.Ticker("^GSPC")
    market_hist = market.history(period="2y")['Close'].pct_change().dropna()

    # Load price history for all stocks
    print("Loading price history...")
    from data import prefetch, get_prices
    tickers = sp500['ticker'].tolist()

    # Prefetch all prices
    prefetch(tickers)

    # Load individual histories
    sp500_hist = {}
    for ticker in tickers:
        try:
            sp500_hist[ticker] = get_prices(ticker)
        except Exception as e:
            print(f"  Failed to load {ticker}: {e}")

    # Create output directory
    output_dir = Path("data/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each stock
    success_count = 0
    skip_count = 0

    for _, row in sp500.iterrows():
        ticker = row['ticker']

        stock_data = compute_stock_data(ticker, row, sp500_hist, market_hist)

        if stock_data is None:
            skip_count += 1
            continue

        # Write to file
        output_path = output_dir / f"{ticker}.json"
        with open(output_path, 'w') as f:
            json.dump(stock_data, f, indent=2)

        success_count += 1

    print(f"\n{'='*70}")
    print(f"Complete: {success_count} stocks written, {skip_count} skipped")
    print(f"Output: data/stocks/")


if __name__ == '__main__':
    main()
