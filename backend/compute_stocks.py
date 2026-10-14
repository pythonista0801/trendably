"""
Generate data/stocks/<SYM>.json for each stock in the S&P 500.

Stage 2 (production): All indicators + real scores (percentile ranks) + meaning templates.
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
    # Align arrays to same length (use shorter length)
    min_len = min(len(stock_returns), len(market_returns))
    stock_returns = stock_returns[-min_len:]
    market_returns = market_returns[-min_len:]

    if min_len < 20:  # Need at least 20 days for meaningful beta
        return None

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


def get_meaning(indicator, value, extra=None):
    """
    Get meaning template based on value bands.

    Returns a one-line explanation chosen by value, never placeholder text.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Data not available for this indicator."

    # Price and performance
    if indicator == 'ret6m':
        if value > 20: return "Strong 6-month gain, well ahead of typical market moves."
        if value > 5: return "Positive 6-month return, outpacing many peers."
        if value > -5: return "Roughly flat over 6 months, tracking the broader market."
        if value > -20: return "Modest decline over 6 months, underperforming the market."
        return "Significant 6-month loss, substantially weaker than the market."

    if indicator == 'ret1y':
        if value > 30: return "Exceptional 1-year return, among the market's strongest performers."
        if value > 10: return "Solid 1-year gain, ahead of the typical market return."
        if value > -10: return "Modest 1-year performance, roughly in line with the market."
        if value > -30: return "Weak 1-year performance, lagging the broader market."
        return "Severe 1-year loss, one of the market's worst performers."

    if indicator == 'fromHigh':
        if value > -5: return "Trading near its 52-week high, showing strong momentum."
        if value > -15: return "Modest pullback from recent highs, typical consolidation."
        if value > -30: return "Notable decline from 52-week high, under pressure."
        return "Deep drawdown from peak, significantly below recent highs."

    # Momentum and trend
    if indicator == 'rsi14':
        if value > 70: return "Overbought territory — buying pressure is very strong but potentially stretched."
        if value > 60: return "Approaching overbought levels — strong buying pressure."
        if value > 40: return "Neutral RSI reading, no extreme buying or selling pressure."
        if value > 30: return "Approaching oversold levels — selling pressure building."
        return "Oversold territory — heavy selling, but potential bounce candidate."

    if indicator == 'aboveMAs':
        if value == 3: return "Above all three moving averages — confirmed uptrend."
        if value == 2: return "Above 2 of 3 averages — mostly bullish structure."
        if value == 1: return "Above 1 of 3 averages — mixed trend signals."
        return "Below all moving averages — downtrend or consolidation."

    if indicator == 'macd':
        rising = extra  # macdRising boolean
        if value > 0 and rising: return "MACD positive and rising — strong bullish momentum."
        if value > 0: return "MACD positive but weakening — uptrend may be losing steam."
        if value < 0 and not rising: return "MACD negative and falling — bearish momentum."
        return "MACD negative but improving — downtrend may be slowing."

    # Risk and volatility
    if indicator == 'vol':
        if value > 50: return "Very high volatility, significantly more volatile than the broad market."
        if value > 30: return "High volatility, larger swings than the typical stock."
        if value > 15: return "Moderate volatility, roughly in line with the market."
        return "Low volatility, relatively stable price action."

    if indicator == 'beta':
        if value > 1.5: return "High beta — tends to amplify market moves by 50% or more."
        if value > 1.1: return "Above-market beta — tends to move more than the overall market."
        if value > 0.9: return "In-line with market — moves roughly in step with the S&P 500."
        if value > 0.5: return "Below-market beta — less volatile than the overall index."
        return "Low beta — relatively insulated from broad market swings."

    if indicator == 'mdd1y':
        if value < -40: return "Extreme 1-year drawdown — experienced a severe peak-to-trough decline."
        if value < -25: return "Large 1-year drawdown — significant decline from peak."
        if value < -15: return "Moderate 1-year drawdown — typical for most stocks."
        return "Mild 1-year drawdown — relatively stable price path."

    if indicator == 'sharpe':
        if value > 2: return "Excellent risk-adjusted return — strong gains relative to volatility."
        if value > 1: return "Good risk-adjusted return — returns have compensated for risk taken."
        if value > 0: return "Modest risk-adjusted return — gains barely exceed volatility."
        return "Poor risk-adjusted return — losses or gains don't justify the volatility."

    # Valuation
    if indicator == 'pe':
        trailing, forward = extra if extra else (value, None)
        if trailing and trailing < 0:
            return "Negative P/E (company is loss-making) — valuation metrics limited."
        if forward and forward < 15:
            return "Low P/E ratio — trading at a discount, may signal value or concerns."
        if forward and forward > 30:
            return "High P/E ratio — priced for strong growth, high expectations built in."
        return "Moderate P/E ratio — fairly valued relative to current earnings."

    if indicator == 'peVsSector':
        if value > 50: return "Trading at a significant premium to its sector peers."
        if value > 0: return "Above the sector median — more expensive than typical peers."
        if value > -20: return "Roughly in line with sector valuation norms."
        return "Trading at a discount to sector peers — relatively cheaper."

    if indicator == 'pb':
        # P/B is None for negative book value
        return "Negative book value — the ratio isn't meaningful."

    # Fundamentals
    if indicator == 'revGrowth':
        if value > 40: return "Exceptional revenue growth, far outpacing most companies."
        if value > 15: return "Strong revenue growth, expanding the top line."
        if value > 0: return "Positive revenue growth, modest expansion."
        if value > -10: return "Flat to declining revenue, limited growth."
        return "Revenue contraction, shrinking top line."

    if indicator == 'epsGrowth':
        if value > 50: return "Explosive earnings growth, profitability expanding rapidly."
        if value > 20: return "Strong earnings growth, bottom line improving."
        if value > 0: return "Positive earnings growth, modest improvement."
        if value > -20: return "Earnings declining, profitability under pressure."
        return "Severe earnings decline or loss-making."

    if indicator == 'margin':
        if value > 40: return "Exceptionally high profit margin, elite profitability."
        if value > 20: return "Strong profit margin, well above most industries."
        if value > 10: return "Healthy profit margin, solid profitability."
        if value > 5: return "Modest profit margin, competitive pressure."
        if value > 0: return "Thin profit margin, limited pricing power."
        return "Negative margin, company is loss-making."

    if indicator == 'roe':
        if value > 30: return "Excellent return on equity, highly efficient use of capital."
        if value > 15: return "Strong return on equity, generating solid returns for shareholders."
        if value > 10: return "Adequate return on equity, meeting baseline expectations."
        if value > 0: return "Weak return on equity, capital not well deployed."
        return "Negative return on equity, destroying shareholder value."

    if indicator == 'de':
        if value > 2: return "High leverage — significant debt load relative to equity."
        if value > 1: return "Moderate leverage — meaningful debt but manageable."
        if value > 0.5: return "Low leverage — conservative balance sheet."
        return "Minimal debt — very strong financial position."

    # Trading and activity
    if indicator == 'liquidity':
        if value == "Very high": return "Extremely liquid — tight spreads, easy to trade in size."
        if value == "High": return "Highly liquid — ample trading volume and depth."
        if value == "Moderate": return "Moderate liquidity — sufficient for most trades."
        return "Low liquidity — wider spreads, more challenging to trade."

    # Default
    return "Current reading for this indicator."


def get_score_tag(score_type, value):
    """Get sub-score tag based on value band."""
    if value is None:
        return "Not enough data"

    if score_type == 'momentum':
        if value >= 70: return "Strong uptrend"
        if value >= 40: return "Mixed momentum"
        return "Weak momentum"

    if score_type == 'risk':
        if value >= 70: return "Low volatility"
        if value >= 40: return "Moderate volatility"
        return "High volatility"

    if score_type == 'valuation':
        if value >= 70: return "Attractive valuation"
        if value >= 40: return "Fairly valued"
        return "Rich vs. sector"

    if score_type == 'fundamentals':
        if value >= 70: return "Robust growth"
        if value >= 40: return "Steady fundamentals"
        return "Weak fundamentals"

    return ""


def get_composite_label(score):
    """Get composite score label."""
    if score is None:
        return "Insufficient data"
    if score >= 70: return "Strong composite score"
    if score >= 40: return "Mixed composite score"
    return "Weak composite score"


def get_summary_sentence(scores):
    """Generate summary sentence from strongest and weakest sub-scores."""
    if all(s is None for s in scores.values()):
        return "Insufficient data to generate summary."

    # Filter out None values
    valid_scores = {k: v for k, v in scores.items() if v is not None}

    if not valid_scores:
        return "Insufficient data to generate summary."

    strongest = max(valid_scores.items(), key=lambda x: x[1])
    weakest = min(valid_scores.items(), key=lambda x: x[1])

    strengths = {
        'momentum': 'strong price momentum',
        'risk': 'low volatility',
        'valuation': 'attractive valuation',
        'fundamentals': 'robust fundamentals'
    }

    weaknesses = {
        'momentum': 'weak momentum',
        'risk': 'high volatility',
        'valuation': 'rich valuation',
        'fundamentals': 'weak fundamentals'
    }

    if strongest[1] >= 60 and weakest[1] <= 40:
        return f"Shows {strengths[strongest[0]]} but faces challenges with {weaknesses[weakest[0]]}."
    elif strongest[1] >= 60:
        return f"Standout strength in {strengths[strongest[0]]}, with balanced profile elsewhere."
    elif weakest[1] <= 40:
        return f"Primary concern is {weaknesses[weakest[0]]}, with mixed signals in other areas."
    else:
        return f"Relatively balanced profile across momentum, risk, valuation, and fundamentals."


def compute_stock_data(ticker, universe_row, sp500_hist, market_hist, all_fundamentals, sector_medians):
    """
    Compute all indicators for one stock.

    Returns dict matching data/stocks/<SYM>.json schema, or None if insufficient data.
    """

    # Fetch current quote (S2)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        price_change = info.get('regularMarketChange')
        price_change_pct = info.get('regularMarketChangePercent')
        current_volume = info.get('volume') or info.get('regularMarketVolume')

        if current_price is None:
            return None
    except Exception:
        return None

    # Get price history (S1) - allow partial data for recent stocks
    if ticker not in sp500_hist or len(sp500_hist[ticker]) < 20:  # Need at least 20 days for basic indicators
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

    # Risk and volatility indicators - need at least 6 months (126 days) for meaningful statistics
    returns_1y = returns.iloc[-252:] if len(returns) >= 252 else returns
    market_returns_1y = market_hist.iloc[-252:] if len(market_hist) >= 252 else market_hist

    # Require 126 days minimum for risk metrics (6 months)
    vol = calculate_volatility(returns_1y) * 100 if len(returns_1y) >= 126 else None
    beta_val = calculate_beta(returns_1y.values, market_returns_1y.values) if len(returns_1y) >= 126 and len(market_returns_1y) >= 126 else None
    mdd_1y = calculate_max_drawdown(closes.iloc[-252:]) * 100 if len(closes) >= 252 else None
    down_vol = calculate_downside_volatility(returns_1y) * 100 if len(returns_1y) >= 126 else None
    sharpe = calculate_sharpe(returns_1y) if len(returns_1y) >= 126 else None

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
    fund = all_fundamentals.get(ticker) if all_fundamentals else None

    pe_trailing = fund.get('trailingPE') if fund else None

    # Calculate forward P/E from price / forwardEps (Yahoo's forwardPE field is unreliable)
    pe_forward = None
    if fund and fund.get('forwardEps') and fund.get('currentPrice'):
        forward_eps = fund.get('forwardEps')
        current_price = fund.get('currentPrice')
        if forward_eps > 0:
            pe_forward = current_price / forward_eps

    ev_ebitda = fund.get('enterpriseToEbitda') if fund else None
    ps = fund.get('priceToSalesTrailing12Months') if fund else None
    pb = fund.get('priceToBook') if fund else None

    rev_growth = fund.get('revenueGrowth') * 100 if fund and fund.get('revenueGrowth') is not None else None
    eps_growth = fund.get('earningsGrowth') * 100 if fund and fund.get('earningsGrowth') is not None else None
    margin = fund.get('profitMargins') * 100 if fund and fund.get('profitMargins') is not None else None
    roe = fund.get('returnOnEquity') * 100 if fund and fund.get('returnOnEquity') is not None else None
    fcf = fund.get('freeCashflow') if fund else None
    de = fund.get('debtToEquity') if fund else None

    # Calculate vs sector median P/E
    sector = universe_row['gics_sector']
    sector_median_fpe = sector_medians.get(sector, {}).get('forwardPE')
    pe_vs_sector = None
    if pe_forward and pe_forward > 0 and sector_median_fpe and sector_median_fpe > 0:
        pe_vs_sector = ((pe_forward / sector_median_fpe) - 1) * 100

    # Build breadcrumb
    sub_industry = universe_row['gics_sub_industry']
    breadcrumb = get_breadcrumb(sector, sub_industry)

    # Return raw indicators (scores calculated later in batch)
    return {
        'ticker': ticker,
        'name': universe_row['name'],
        'sector': sector,
        'sub_industry': sub_industry,
        'breadcrumb': breadcrumb,
        'price': round(current_price, 2) if current_price else None,
        'change': round(price_change, 2) if price_change else None,
        'move': round(price_change_pct, 2) if price_change_pct else None,
        'indicators': {
            'ret1m': round(ret_1m, 1) if ret_1m is not None else None,
            'ret3m': round(ret_3m, 1) if ret_3m is not None else None,
            'ret6m': round(ret_6m, 1) if ret_6m is not None else None,
            'ret1y': round(ret_1y, 1) if ret_1y is not None else None,
            'fromHigh': round(from_high, 1) if from_high is not None else None,
            'high52': round(high_52w, 2) if high_52w is not None else None,
            'low52': round(low_52w, 2) if low_52w is not None else None,
            'rsi14': round(rsi_14, 0) if rsi_14 is not None and not np.isnan(rsi_14) else None,
            'aboveMAs': above_mas,
            'sma20': round(sma_20, 2) if sma_20 is not None and not np.isnan(sma_20) else None,
            'sma50': round(sma_50, 2) if sma_50 is not None and not np.isnan(sma_50) else None,
            'sma200': round(sma_200, 2) if sma_200 is not None and not np.isnan(sma_200) else None,
            'macd': macd,
            'macdRising': macd_rising,
            'vol': round(vol, 1) if vol is not None else None,
            'beta': round(beta_val, 2) if beta_val is not None else None,
            'mdd1y': round(mdd_1y, 1) if mdd_1y is not None else None,
            'downVol': round(down_vol, 1) if down_vol is not None else None,
            'sharpe': round(sharpe, 2) if sharpe is not None else None,
            'pe': round(pe_trailing, 1) if pe_trailing is not None and pe_trailing > 0 else None,
            'fpe': round(pe_forward, 1) if pe_forward is not None and pe_forward > 0 else None,
            'peVsSector': round(pe_vs_sector, 1) if pe_vs_sector is not None else None,
            'evEbitda': round(ev_ebitda, 1) if ev_ebitda is not None and ev_ebitda > 0 else None,
            'ps': round(ps, 1) if ps is not None else None,
            'pb': round(pb, 1) if pb is not None and pb > 0 else None,
            'revGrowth': round(rev_growth, 1) if rev_growth is not None else None,
            'epsGrowth': round(eps_growth, 1) if eps_growth is not None else None,
            'margin': round(margin, 1) if margin is not None else None,
            'roe': round(roe, 1) if roe is not None else None,
            'fcf': fcf,
            'de': round(de, 2) if de is not None else None,
            'avgVol30': int(avg_vol_30) if avg_vol_30 is not None else None,
            'volVsAvg': round(vol_vs_avg, 0) if vol_vs_avg is not None else None,
            'atr14': round(atr_14, 2) if atr_14 is not None else None,
            'liquidity': liquidity
        }
    }


def main():
    """Generate data/stocks/<SYM>.json for all S&P 500 stocks."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate stock detail JSON files")
    parser.add_argument('--stocks', nargs='*', help='Specific tickers to process (default: all S&P 500)')
    args = parser.parse_args()

    print("="*70)
    print("COMPUTE STOCKS - Production Mode")
    print("="*70)

    # Load universe
    sp500 = load_sp500()

    if args.stocks:
        sp500 = sp500[sp500['ticker'].isin(args.stocks)]
        if len(sp500) == 0:
            print("No matching stocks found")
            return

    print(f"\nProcessing {len(sp500)} stocks...")

    # Load fundamentals cache
    print("Loading fundamentals cache...")
    cache_path = Path("cache/fundamentals.json")
    if cache_path.exists():
        with open(cache_path) as f:
            fund_data = json.load(f)
        all_fundamentals = fund_data.get('stocks', {})
        print(f"  Loaded {len(all_fundamentals)} stocks from cache")
    else:
        print("  WARNING: No fundamentals cache found!")
        all_fundamentals = {}

    # Calculate sector median forward P/E (using same calculation as individual stocks: price / forwardEps)
    print("Calculating sector medians...")
    sector_medians = {}
    for sector in sp500['gics_sector'].unique():
        sector_stocks = sp500[sp500['gics_sector'] == sector]['ticker'].tolist()
        fpe_values = []
        for ticker in sector_stocks:
            fund = all_fundamentals.get(ticker)
            if fund and fund.get('forwardEps') and fund.get('currentPrice'):
                forward_eps = fund['forwardEps']
                current_price = fund['currentPrice']
                if forward_eps > 0:
                    fpe = current_price / forward_eps
                    if fpe > 0:  # Ignore negative P/E
                        fpe_values.append(fpe)

        if fpe_values:
            sector_medians[sector] = {
                'forwardPE': np.median(fpe_values)
            }
            print(f"  {sector}: median fPE = {sector_medians[sector]['forwardPE']:.1f}")

    # Load market data
    print("\nLoading market data (^GSPC)...")
    market = yf.Ticker("^GSPC")
    market_hist = market.history(period="2y")['Close'].pct_change().dropna()

    # Load price history
    print("Loading price history...")
    from data import prefetch, get_prices
    tickers = sp500['ticker'].tolist()

    # Prefetch (uses cached data from backend/run.py)
    prefetch(tickers)

    sp500_hist = {}
    for ticker in tickers:
        try:
            sp500_hist[ticker] = get_prices(ticker)
        except Exception:
            pass

    # First pass: compute raw indicators
    print("\n" + "="*70)
    print("PASS 1: Computing indicators...")
    print("="*70 + "\n")

    all_data = {}
    skip_count = 0

    for i, (_, row) in enumerate(sp500.iterrows(), 1):
        ticker = row['ticker']
        print(f"[{i}/{len(sp500)}] {ticker}...", end=' ', flush=True)

        stock_data = compute_stock_data(
            ticker, row, sp500_hist, market_hist, all_fundamentals, sector_medians
        )

        if stock_data is None:
            print("SKIP (insufficient data)")
            skip_count += 1
            continue

        all_data[ticker] = stock_data
        print("OK")

    print(f"\n{len(all_data)} stocks with data, {skip_count} skipped")

    # Second pass: calculate percentile ranks and scores
    print("\n" + "="*70)
    print("PASS 2: Calculating scores (percentile ranks)...")
    print("="*70 + "\n")

    # Collect values for ranking
    momentum_6m = {t: d['indicators']['ret6m'] for t, d in all_data.items() if d['indicators']['ret6m'] is not None}
    momentum_1y = {t: d['indicators']['ret1y'] for t, d in all_data.items() if d['indicators']['ret1y'] is not None}
    momentum_trend = {t: d['indicators']['aboveMAs'] / 3 * 100 for t, d in all_data.items()}  # 0/33/67/100

    risk_vol = {t: d['indicators']['vol'] for t, d in all_data.items() if d['indicators']['vol'] is not None}
    risk_mdd = {t: abs(d['indicators']['mdd1y']) for t, d in all_data.items() if d['indicators']['mdd1y'] is not None}
    risk_beta = {t: abs(d['indicators']['beta'] - 1) for t, d in all_data.items() if d['indicators']['beta'] is not None}

    fund_rev = {t: d['indicators']['revGrowth'] for t, d in all_data.items() if d['indicators']['revGrowth'] is not None}
    fund_eps = {t: d['indicators']['epsGrowth'] for t, d in all_data.items() if d['indicators']['epsGrowth'] is not None}
    fund_margin = {t: d['indicators']['margin'] for t, d in all_data.items() if d['indicators']['margin'] is not None}
    fund_roe = {t: d['indicators']['roe'] for t, d in all_data.items() if d['indicators']['roe'] is not None}
    fund_de = {t: d['indicators']['de'] for t, d in all_data.items() if d['indicators']['de'] is not None}

    # Calculate percentile ranks
    def percentile_rank(values_dict, ticker):
        """Return 0-100 percentile rank for ticker in values_dict."""
        if ticker not in values_dict:
            return None
        val = values_dict[ticker]
        all_vals = list(values_dict.values())
        rank = sum(1 for v in all_vals if v < val) / len(all_vals) * 100
        return round(rank, 0)

    # Calculate scores for each stock
    for ticker, data in all_data.items():
        # Momentum score (40% 6M, 30% 1Y, 30% trend)
        m_6m = percentile_rank(momentum_6m, ticker)
        m_1y = percentile_rank(momentum_1y, ticker)
        m_trend = momentum_trend[ticker]

        if m_6m is not None or m_1y is not None:
            momentum_score = 0
            count = 0
            if m_6m is not None:
                momentum_score += m_6m * 0.4
                count += 0.4
            if m_1y is not None:
                momentum_score += m_1y * 0.3
                count += 0.3
            momentum_score += m_trend * 0.3
            count += 0.3
            momentum_score = round(momentum_score / count * (count / 1.0))  # Normalize if missing inputs
        else:
            momentum_score = None

        # Risk score (100 - average rank of vol, mdd, beta)
        r_vol = percentile_rank(risk_vol, ticker)
        r_mdd = percentile_rank(risk_mdd, ticker)
        r_beta = percentile_rank(risk_beta, ticker)

        risk_components = [r for r in [r_vol, r_mdd, r_beta] if r is not None]
        if risk_components:
            risk_score = round(100 - np.mean(risk_components))
        else:
            risk_score = None

        # Valuation score (within sector)
        sector = data['sector']
        sector_stocks = {t: d for t, d in all_data.items() if d['sector'] == sector}

        sector_fpe = {t: d['indicators']['fpe'] for t, d in sector_stocks.items() if d['indicators']['fpe'] is not None}
        sector_evebitda = {t: d['indicators']['evEbitda'] for t, d in sector_stocks.items() if d['indicators']['evEbitda'] is not None}
        sector_ps = {t: d['indicators']['ps'] for t, d in sector_stocks.items() if d['indicators']['ps'] is not None}

        v_fpe = percentile_rank(sector_fpe, ticker)
        v_ev = percentile_rank(sector_evebitda, ticker)
        v_ps = percentile_rank(sector_ps, ticker)

        val_components = [v for v in [v_fpe, v_ev, v_ps] if v is not None]
        if val_components:
            valuation_score = round(100 - np.mean(val_components))  # Lower is better, so invert
        else:
            valuation_score = None

        # Fundamentals score
        f_rev = percentile_rank(fund_rev, ticker)
        f_eps = percentile_rank(fund_eps, ticker)
        f_margin = percentile_rank(fund_margin, ticker)
        f_roe = percentile_rank(fund_roe, ticker)
        f_de = percentile_rank(fund_de, ticker)

        # Invert debt-to-equity (lower is better)
        if f_de is not None:
            f_de = 100 - f_de

        fund_components = [f for f in [f_rev, f_eps, f_margin, f_roe, f_de] if f is not None]
        if fund_components:
            fundamentals_score = round(np.mean(fund_components))
        else:
            fundamentals_score = None

        # Composite score
        scores_dict = {
            'momentum': momentum_score,
            'risk': risk_score,
            'valuation': valuation_score,
            'fundamentals': fundamentals_score
        }

        valid_scores = [s for s in scores_dict.values() if s is not None]
        if valid_scores:
            composite_score = round(
                0.30 * (momentum_score or 0) +
                0.20 * (risk_score or 0) +
                0.20 * (valuation_score or 0) +
                0.30 * (fundamentals_score or 0)
            )
        else:
            composite_score = None

        # Add scores to data
        data['score'] = {
            'composite': composite_score,
            'momentum': momentum_score,
            'risk': risk_score,
            'valuation': valuation_score,
            'fundamentals': fundamentals_score,
            'label': get_composite_label(composite_score),
            'tags': {
                'momentum': get_score_tag('momentum', momentum_score),
                'risk': get_score_tag('risk', risk_score),
                'valuation': get_score_tag('valuation', valuation_score),
                'fundamentals': get_score_tag('fundamentals', fundamentals_score)
            }
        }

        data['summary'] = get_summary_sentence(scores_dict)

    # Third pass: add meaning templates and write files
    print("\n" + "="*70)
    print("PASS 3: Adding meanings and writing files...")
    print("="*70 + "\n")

    output_dir = Path("data/stocks")
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, (ticker, data) in enumerate(all_data.items(), 1):
        print(f"[{i}/{len(all_data)}] Writing {ticker}.json...", end=' ')

        ind = data['indicators']

        # Add meanings for each indicator group
        data['meanings'] = {
            'ret6m': get_meaning('ret6m', ind['ret6m']),
            'ret1y': get_meaning('ret1y', ind['ret1y']),
            'fromHigh': get_meaning('fromHigh', ind['fromHigh']),
            'rsi14': get_meaning('rsi14', ind['rsi14']),
            'aboveMAs': get_meaning('aboveMAs', ind['aboveMAs']),
            'macd': get_meaning('macd', ind['macd'], ind['macdRising']),
            'vol': get_meaning('vol', ind['vol']),
            'beta': get_meaning('beta', ind['beta']),
            'mdd1y': get_meaning('mdd1y', ind['mdd1y']),
            'sharpe': get_meaning('sharpe', ind['sharpe']),
            'pe': get_meaning('pe', ind['pe'], (ind['pe'], ind['fpe'])),
            'peVsSector': get_meaning('peVsSector', ind['peVsSector']),
            'pb': get_meaning('pb', ind['pb']),
            'revGrowth': get_meaning('revGrowth', ind['revGrowth']),
            'epsGrowth': get_meaning('epsGrowth', ind['epsGrowth']),
            'margin': get_meaning('margin', ind['margin']),
            'roe': get_meaning('roe', ind['roe']),
            'de': get_meaning('de', ind['de']),
            'liquidity': get_meaning('liquidity', ind['liquidity'])
        }

        # Add timestamp
        data['asOf'] = datetime.now().isoformat()

        # Write file
        output_path = output_dir / f"{ticker}.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print("OK")

    print(f"\n{'='*70}")
    print(f"COMPLETE")
    print(f"{'='*70}")
    print(f"Succeeded: {len(all_data)} stocks")
    print(f"Skipped:   {skip_count} stocks")
    print(f"Output:    data/stocks/")


if __name__ == '__main__':
    main()
