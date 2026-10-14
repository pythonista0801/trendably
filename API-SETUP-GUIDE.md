# Strategy Lab Real Data Setup Guide

## ✅ What's Been Created

1. **`backend/api.py`** - Flask API wrapping the backtest engine
2. **`backend/engine.py`** - Extended with `run_cell_extended()` function
3. **`test_api.py`** - Test suite for the API
4. **`requirements.txt`** - Updated with Flask dependency

## 📋 Step-by-Step Instructions

### **STEP 1: Install Flask**

```bash
cd C:\Users\natal\Documents\trendably
pip install flask
```

### **STEP 2: Start the API Server**

Open a terminal and run:

```bash
python backend/api.py
```

You should see:
```
============================================================
Trendably Strategy Lab API
============================================================
Starting server on http://localhost:5000

Test endpoints:
  Health: http://localhost:5000/api/health
  Backtest: http://localhost:5000/api/backtest?sym=NVDA&strat=macd

Press Ctrl+C to stop
============================================================
 * Running on http://127.0.0.1:5000
```

**Leave this terminal running** - the API needs to stay active.

### **STEP 3: Test the API**

Open a **second terminal** and run:

```bash
python test_api.py
```

This will test 5 scenarios with real Yahoo Finance data:
1. Health check
2. Basic backtest (NVDA + MACD)
3. Custom parameters (AAPL + MA crossover)
4. Bollinger Bands (TSLA)
5. Mean Reversion (MSFT)

Expected output:
```
============================================================
✓ ALL TESTS PASSED
============================================================
The API is working correctly with real Yahoo Finance data!
```

### **STEP 4: Manual Testing**

With the API running, open your browser and try:

**Health Check:**
```
http://localhost:5000/api/health
```

**Basic Backtest:**
```
http://localhost:5000/api/backtest?sym=NVDA&strat=macd
```

**With Custom Parameters:**
```
http://localhost:5000/api/backtest?sym=AAPL&strat=ma&fast=15&slow=40
```

You should see JSON responses with real backtest data!

## 🔧 API Reference

### Endpoint: `/api/backtest`

**Parameters:**
- `sym` - Stock ticker (e.g., NVDA, AAPL, TSLA)
- `strat` - Strategy ID:
  - `ma` - MA Crossover
  - `gc` - Golden Cross
  - `macd` - MACD
  - `bb` - Bollinger Bands
  - `mom` - Momentum
  - `mr` - Mean Reversion
  - `bo` - Breakout
  - `bh` - Buy & Hold
- `window` - Optional: `1y`, `3y`, or `5y` (default: `1y`)
- **Strategy-specific parameters:**

#### MA Crossover / Golden Cross
- `fast` - Fast MA length (e.g., 20)
- `slow` - Slow MA length (e.g., 50)

#### MACD
- `fast` - Fast EMA (e.g., 12)
- `slow` - Slow EMA (e.g., 26)
- `signal` - Signal line (e.g., 9)

#### Bollinger Bands
- `period` - Period (e.g., 20)
- `stddev` - Standard deviations (e.g., 2.0)

#### Mean Reversion (RSI)
- `rsiLen` - RSI period (e.g., 14)
- `oversold` - Buy threshold (e.g., 30)
- `overbought` - Sell threshold (e.g., 70)

#### Momentum
- `lookback` - Lookback period in days (e.g., 252)
- `rebalance` - Rebalance frequency in days (e.g., 21)

#### Breakout
- `channel` - Channel length (e.g., 20)

### Response Format

```json
{
  "ticker": "NVDA",
  "strategy": "macd",
  "window": "1y",
  "status": "ok",
  "totalRet": 58.7,
  "annualRet": 58.7,
  "maxDD": 21.4,
  "winRate": 55.0,
  "numTrades": 12,
  "avgRet": 4.2,
  "sharpe": 1.38,
  "bhReturn": 58.7,
  "bhMaxDD": 21.4,
  "trades": [
    {
      "entryDate": "Jan 15",
      "exitDate": "Feb 3",
      "entryPx": 142.50,
      "exitPx": 148.30,
      "ret": 4.1,
      "win": true
    }
  ],
  "equityPts": [
    {"x": 0, "y": 100},
    {"x": 10.5, "y": 104.2}
  ],
  "bhPts": [
    {"x": 0, "y": 100},
    {"x": 10.5, "y": 103.8}
  ]
}
```

## ⚠️ Important Notes

### Parameter Name Mapping

The API automatically maps frontend parameter names to backend:
- `rsiLen` → `period` (Mean Reversion)
- `stddev` → `width` (Bollinger Bands)
- `channel` → `entry_days` (Breakout)

### Integer Conversion

Parameters that need to be integers are automatically converted:
- `fast`, `slow`, `signal`
- `period`, `rsiLen`
- `oversold`, `overbought`
- `channel`, `lookback`, `rebalance`
- `entry_days`, `exit_days`

This fixes the issue where rolling windows would reject decimal values.

## 🚨 Known Issues to Resolve

### Strategy Parameter Mismatches (⚠ from DATA-SPEC.md)

The following strategies have differences between frontend display and backend defaults:

1. **Bollinger Bands**: Page says "sell near upper", engine sells at middle band
2. **Momentum**: Page says 6-month, engine uses 12-month (252 days)
3. **Mean Reversion**: Page slider shows overbought=70, engine uses 55
4. **Breakout**: Page shows one channel setting, engine has separate entry/exit

**Next Step:** Decide whether to change the frontend or backend for consistency.

## 📝 Next Steps

1. ✅ Test API with real data (you're here!)
2. ⏭️ Resolve the 4 strategy parameter mismatches
3. ⏭️ Update Strategy Lab frontend to call API instead of simulation
4. ⏭️ Update optimization to use API
5. ⏭️ Full end-to-end test

## 🔍 Troubleshooting

**"No module named 'flask'"**
```bash
pip install flask
```

**"Connection refused"**
- Make sure the API server is running (`python backend/api.py`)
- Check that it's on port 5000

**"No data for ticker"**
- Yahoo Finance may not have data for that ticker
- Try a common ticker like AAPL, MSFT, or NVDA

**Slow first run**
- First time downloads historical data from Yahoo Finance
- Subsequent runs use cached data (much faster)

## 📦 For Production (Later)

When deploying online:
1. Replace Flask's built-in server with gunicorn
2. Deploy to a platform that supports Python (Render, Fly.io, Railway, etc.)
3. Netlify cannot run Python backends
4. Consider adding rate limiting and authentication

---

**Status:** API created and ready for testing ✅
**Next:** Run the test suite to verify real data integration
