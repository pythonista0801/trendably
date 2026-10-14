"""Complete test of all 7 strategies with detailed output."""

import requests
import json

BASE_URL = "http://localhost:5000"

strategies = [
    ("NVDA", "macd", {}, "MACD (defaults)"),
    ("AAPL", "ma", {"fast": 20, "slow": 50}, "MA Crossover (20/50)"),
    ("MSFT", "gc", {"fast": 50, "slow": 200}, "Golden Cross (50/200)"),
    ("TSLA", "bb", {"period": 20, "stddev": 2}, "Bollinger Bands (20, 2σ)"),
    ("AMZN", "mom", {"lookback": 252}, "Momentum (12-month)"),
    ("GOOGL", "mr", {"rsiLen": 14, "oversold": 30, "overbought": 70}, "Mean Reversion (RSI 14, 30/70)"),
    ("META", "bo", {"channel": 20}, "Breakout (20-day)")
]

print("\n" + "="*70)
print("COMPLETE STRATEGY TEST - ALL 7 STRATEGIES")
print("="*70)

for i, (ticker, strat, params, desc) in enumerate(strategies, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}/7: {desc}")
    print(f"Stock: {ticker}, Strategy: {strat}, Params: {params}")
    print("="*70)

    try:
        response = requests.get(f"{BASE_URL}/api/backtest", params={'sym': ticker, 'strat': strat, **params})

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ SUCCESS")
            print(f"  Total Return:     {data.get('totalRet')}%")
            print(f"  Buy & Hold:       {data.get('bhReturn')}%")
            print(f"  Outperformance:   {data.get('totalRet') - data.get('bhReturn'):.2f} pts")
            print(f"  Win Rate:         {data.get('winRate')}%")
            print(f"  Number of Trades: {data.get('numTrades')}")
            print(f"  Avg Return/Trade: {data.get('avgRet')}%")
            print(f"  Max Drawdown:     {data.get('maxDD')}%")
            print(f"  Sharpe Ratio:     {data.get('sharpe')}")

            # Show first 3 trades
            trades = data.get('trades', [])
            if trades:
                print(f"\n  First {min(3, len(trades))} trades:")
                for j, trade in enumerate(trades[:3], 1):
                    result = "WIN" if trade['win'] else "LOSS"
                    print(f"    {j}. {trade['entryDate']} → {trade['exitDate']}: "
                          f"${trade['entryPx']:.2f} → ${trade['exitPx']:.2f} = {trade['ret']:+.1f}% ({result})")
        else:
            print(f"\n✗ ERROR {response.status_code}")
            print(f"  {response.json()}")

    except Exception as e:
        print(f"\n✗ EXCEPTION: {e}")

print("\n" + "="*70)
print("SUMMARY TABLE")
print("="*70)
print(f"{'Strategy':<20} {'Stock':<6} {'Return':<8} {'vs B&H':<8} {'Trades':<7} {'Win%'}")
print("-"*70)

for ticker, strat, params, desc in strategies:
    try:
        response = requests.get(f"{BASE_URL}/api/backtest", params={'sym': ticker, 'strat': strat, **params})
        if response.status_code == 200:
            d = response.json()
            diff = d.get('totalRet', 0) - d.get('bhReturn', 0)
            print(f"{desc:<20} {ticker:<6} {d.get('totalRet'):>6.1f}% {diff:>6.1f}pts {d.get('numTrades'):>4}    {d.get('winRate'):>5.1f}%")
    except:
        pass

print("="*70)
