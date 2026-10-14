"""The one engine. Runs any stock x strategy x window combination — one cell or the whole grid."""

import json
import math
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date

import numpy as np
import pandas as pd
from backtesting import Backtest

from config import (COMMISSION, DEFAULT_WINDOW, OUTPUT_FILE, STARTING_CASH, WARMUP_DAYS, WINDOWS,
                    WORKERS)
from data import get_prices
from strategies import REGISTRY

CHART_DAYS = 1320          # longest window plus 60 days, so the chart's moving averages start full


def _clean(value):
    """Round numbers; turn NaN or missing values into None."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(float(value), 2)


# ---------- One cell ----------
def run_cell(ticker: str, strategy_id: str, window: str = DEFAULT_WINDOW, prices=None,
             extended: bool = False, **kwargs) -> dict:
    """Backtest one stock with one strategy over one window and return the results.

    Args:
        ticker: stock symbol (e.g. 'NVDA')
        strategy_id: backend strategy id (e.g. 'macd', 'ma_crossover')
        window: '1y', '3y', or '5y'
        prices: pre-loaded price data (optional, will download if None)
        extended: if True, return full data for Strategy Lab (trades, equity curve, etc.)
                  if False, return summary only (for Grid)
        **kwargs: strategy parameter overrides (e.g. fast=15, slow=40)
    """
    _, strategy_cls = REGISTRY[strategy_id]
    _, days = WINDOWS[window]
    prices = prices if prices is not None else get_prices(ticker)
    base = {"ticker": ticker, "strategy": strategy_id, "window": window}

    # Calculate required warm-up: max of WARMUP_DAYS and any custom parameter that's a lookback period
    # (e.g. Golden Cross slow=300 needs 300 days of warm-up, not just the default 260)
    # Add +20 buffer to prevent edge cases
    warmup = WARMUP_DAYS
    for key, val in kwargs.items():
        if key in ['slow', 'lookback', 'period', 'channel', 'entry_days', 'exit_days'] and isinstance(val, (int, float)):
            warmup = max(warmup, int(val) + 20)

    if len(prices) < days + warmup:
        return {**base, "status": "insufficient_history", "days": len(prices)}

    data = prices.iloc[-(days + warmup):]
    stats = Backtest(data, strategy_cls, cash=STARTING_CASH, commission=COMMISSION,
                     finalize_trades=True).run(start_bar=warmup, **kwargs)

    # Extract data (measure only the window itself, not the warm-up days)
    equity = stats["_equity_curve"]["Equity"].iloc[warmup:]
    trades_df = stats["_trades"]

    # Calculate metrics
    total = equity.iloc[-1] / equity.iloc[0] - 1
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    annual = (1 + total) ** (1 / years) - 1 if total > -1 else -1
    drawdown = (equity / equity.cummax() - 1).min()
    win_rate = (trades_df["PnL"] > 0).mean() * 100 if len(trades_df) else None

    # Grid format (summary only)
    if not extended:
        return {
            **base,
            "status": "ok",
            "annual_return": _clean(annual * 100),
            "total_return":  _clean(total * 100),
            "max_drawdown":  _clean(drawdown * 100),
            "win_rate":      _clean(win_rate),
            "trades":        len(trades_df),
        }

    # Strategy Lab format (full data)
    avg_return = (trades_df["ReturnPct"].mean() * 100) if len(trades_df) else 0
    daily_returns = equity.pct_change().dropna()
    sharpe = (daily_returns.mean() / daily_returns.std() * math.sqrt(252)) if len(daily_returns) > 1 else 0

    # Format trades for frontend
    # Identify the last date (positions closed on this date are still open)
    last_date = equity.index[-1] if len(equity) > 0 else None

    trades_list = []
    for _, trade in trades_df.iterrows():
        # Windows-compatible date formatting with year (no %-d flag)
        entry_str = trade['EntryTime'].strftime('%b %d, %Y').replace(' 0', ' ')
        exit_str = trade['ExitTime'].strftime('%b %d, %Y').replace(' 0', ' ')

        # Check if this trade is still open (exits on the last bar)
        is_open = (trade['ExitTime'].date() == last_date.date()) if last_date else False

        trades_list.append({
            'entryDate': entry_str,
            'exitDate': exit_str if not is_open else 'Open',
            'entryPx': round(float(trade['EntryPrice']), 2),
            'exitPx': round(float(trade['ExitPrice']), 2),
            'ret': round(float(trade['ReturnPct'] * 100), 1),
            'win': float(trade['PnL']) > 0,
            'open': is_open
        })

    # Equity curve points (scale to start at 100)
    scale_factor = 100 / equity.iloc[0]
    equity_points = []
    for i, (date, val) in enumerate(equity.items()):
        day_idx = i * (252.0 / len(equity))
        equity_points.append({
            'x': round(day_idx, 1),
            'y': round(float(val * scale_factor), 2)
        })

    # Buy & hold curve for comparison
    buy_hold_prices = data['Close'].iloc[warmup:]
    bh_scale = 100 / buy_hold_prices.iloc[0]
    bh_total = (buy_hold_prices.iloc[-1] / buy_hold_prices.iloc[0] - 1) * 100
    bh_peak = (buy_hold_prices * bh_scale).cummax()
    bh_drawdown = ((buy_hold_prices * bh_scale) / bh_peak - 1).min() * 100

    bh_points = []
    for i, val in enumerate(buy_hold_prices):
        day_idx = i * (252.0 / len(buy_hold_prices))
        bh_points.append({
            'x': round(day_idx, 1),
            'y': round(float(val * bh_scale), 2)
        })

    return {
        **base,
        "status": "ok",
        "totalRet": _clean(total * 100),
        "annualRet": _clean(annual * 100),
        "maxDD": _clean(drawdown * 100),  # Keep negative (e.g., -26.1%)
        "winRate": _clean(win_rate or 0),
        "numTrades": len(trades_df),
        "avgRet": _clean(avg_return),
        "sharpe": round(sharpe, 2),
        "bhReturn": _clean(bh_total),
        "bhMaxDD": _clean(bh_drawdown),  # Keep negative (e.g., -20.2%)
        "trades": trades_list,
        "equityPts": equity_points,
        "bhPts": bh_points
    }


# ---------- One stock: every strategy x window, plus summary numbers for the page ----------
def summary(prices: pd.DataFrame) -> dict:
    c, v = prices["Close"], prices["Volume"]
    year = c.iloc[-253:]
    log_ret = np.log(year / year.shift(1)).dropna()
    return {
        "last":   _clean(c.iloc[-1]),
        "chg":    _clean((c.iloc[-1] / c.iloc[-2] - 1) * 100) if len(c) > 1 else 0,
        "ret12":  _clean((year.iloc[-1] / year.iloc[0] - 1) * 100),
        "vol":    _clean(log_ret.std() * math.sqrt(252) * 100),
        "avgvol": int(v.iloc[-60:].mean()),
        "days":   len(c),
    }


def run_stock(ticker: str, strategy_ids: list[str], windows: list[str]):
    """Everything for one stock. Runs inside a worker process."""
    prices = get_prices(ticker)
    cells = {w: {} for w in windows}
    for sid in strategy_ids:
        for w in windows:
            r = run_cell(ticker, sid, w, prices)
            cells[w][sid] = None if r["status"] != "ok" else \
                [r["annual_return"], r["total_return"], r["max_drawdown"], r["win_rate"], r["trades"]]
    return ticker, cells, summary(prices), prices["Close"].tail(CHART_DAYS)


# ---------- The whole grid ----------
def run_grid(tickers: list[str], strategy_ids: list[str], windows: list[str]):
    """Run every combination, several stocks at a time in parallel."""
    results, summaries, closes = {}, {}, {}
    workers = 1 if len(tickers) == 1 else WORKERS
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(run_stock, t, strategy_ids, windows): t for t in tickers}
        for n, job in enumerate(as_completed(jobs), 1):
            t = jobs[job]
            try:
                t, cells, summ, close = job.result()
            except Exception as e:
                print(f"  [{n}/{len(tickers)}] {t}: skipped ({e})")
                continue
            results[t], summaries[t], closes[t] = cells, summ, close
            best = [(sid, v[0]) for sid, v in cells[windows[-1]].items() if v]
            shown = f"best over {windows[-1]}: {REGISTRY[max(best, key=lambda x: x[1])[0]][0]}" if best \
                else "not enough history"
            print(f"  [{n}/{len(tickers)}] {t:<6} {shown}")
    return results, summaries, closes


def save(results: dict, summaries: dict, closes: dict, stocks: pd.DataFrame, strategy_ids: list[str],
         windows: list[str], path: str = OUTPUT_FILE):
    """Write what the page needs.

    grid.json / grid.js  — stocks, strategies, windows, results (small, loads instantly)
    prices/<TICKER>.js   — one file per stock for its chart, loaded only when the stock is opened
    results[ticker][window][strategy] = [annual %, total %, max drawdown %, win rate %, trades], or null
    """
    folder = os.path.dirname(path)
    price_dir = os.path.join(folder, "prices")
    shutil.rmtree(price_dir, ignore_errors=True)       # clear out stocks that have left the index
    os.makedirs(price_dir, exist_ok=True)

    dates = max(closes.values(), key=len).index if closes else pd.DatetimeIndex([])
    for t, c in closes.items():
        aligned = c.reindex(dates).ffill().dropna()    # line up every stock on the same trading days
        with open(os.path.join(price_dir, f"{t}.js"), "w") as f:
            f.write(f'(window.PRICES = window.PRICES || {{}})["{t}"] = '
                    + json.dumps([round(float(x), 2) for x in aligned]) + ";")

    rows = stocks[stocks["ticker"].isin(results)].to_dict(orient="records")
    out = {
        "generated":      date.today().isoformat(),
        "strategies":     [{"id": s, "name": REGISTRY[s][0]} for s in strategy_ids],
        "windows":        [{"id": w, "name": WINDOWS[w][0], "days": WINDOWS[w][1]} for w in windows],
        "default_window": DEFAULT_WINDOW if DEFAULT_WINDOW in windows else windows[-1],
        "dates":          [d.strftime("%Y-%m-%d") for d in dates],
        "stocks":         [{**r, **summaries[r["ticker"]]} for r in rows],
        "results":        results,
    }
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    with open(path.replace(".json", ".js"), "w") as f:
        f.write("window.GRID = " + json.dumps(out, separators=(",", ":")) + ";")
    print(f"\nSaved {len(rows)} stocks x {len(strategy_ids)} strategies x {len(windows)} windows to {path}")
