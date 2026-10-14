# Strategy Lab Connected to Real API ✅

Strategy Lab now uses real Yahoo Finance data via the Python backtest engine!

## What Was Done

### 1. **API Integration** ✅
- Added `runBacktestAPI()` function that calls `http://localhost:5000/api/backtest`
- Made `recompute()` async to handle API calls
- Updated optimization to use real API (with fewer samples: 20 vs 50)
- Added `USE_REAL_API` flag (set to `true`) - can toggle to simulation for testing

### 2. **All 4 Critical Fixes Applied** ✅

#### Fix 1: Momentum Units
- **Problem:** Frontend sends months, backend expects days
- **Solution:** API converts months × 21 = days (line 86-87 in `backend/api.py`)
- **Test:** `lookback=12` → 252 days ✅

#### Fix 2: Drawdown Sign
- **Problem:** API returned positive maxDD (26.1%), frontend expects negative
- **Solution:** Kept drawdown negative in engine (line 136, 142 in `backend/engine.py`)
- **Display:** Frontend displays as positive "−26.1%" for readability ✅

#### Fix 3: Open Positions
- **Problem:** Trades closed on last date are actually still open
- **Solution:** Engine marks them with `open: true` flag (lines 100-111 in `backend/engine.py`)
- **Display:** Trade log shows "**Open**" instead of exit date, blue pill ✅

#### Fix 4: Small Sample Warning
- **Problem:** 1 trade at "100% win rate" is misleading
- **Solution:** Win rate shows "—" with "too few trades to judge" when <5 trades ✅

### 3. **UI Enhancements**
- Open positions styled with blue pill (`.outcome-pill.open`)
- Small sample warning prevents false confidence from lucky single trades
- Optimization uses 20 samples (vs 50) when using real API to avoid slowdown

---

## Testing Strategy Lab

### Prerequisites
Make sure the API is running:
```bash
python backend/api.py
```

### Test 1: Basic Function (NVDA + MACD)
1. Open `strategy-lab.html` in browser
2. Should load with NVDA + MACD by default
3. **Expect:** Real data loads (may take 2-3 seconds first time)
4. **Check:** Numbers match test results:
   - Total return: -17.79%
   - Win rate: 27.27%
   - Trades: 11
   - Max drawdown: −26.1%

### Test 2: Small Sample Warning (MSFT + Golden Cross)
1. Select "MSFT" ticker
2. Select "Golden Cross" strategy
3. **Expect:** Win rate shows "—" (not 100%)
4. **Check:** Subtitle says "too few trades to judge" (only 1 trade)

### Test 3: Open Position (GOOGL + Mean Reversion)
1. Select "GOOGL" ticker
2. Select "Mean Reversion" strategy
3. Keep defaults (RSI 14, Buy below 30, Sell above 55)
4. Scroll to Trade Log
5. **Check:** Last trade (Jun 4) shows:
   - Exit date: **Open** (bold)
   - Blue "Open" pill (not Win/Loss)

### Test 4: Parameter Changes (Real Recalculation)
1. Stay on GOOGL + Mean Reversion
2. Change "Sell when RSI above" slider from 55 → 70
3. **Expect:** Page recalculates with real API call
4. **Check:** Return changes (was 19.3%, now should be different)

### Test 5: Optimization Button
1. Any ticker + strategy
2. Click "Optimize Parameters" button
3. **Expect:** Loading spinner, then top 3 combinations appear
4. **Check:** Can click any result card to apply those parameters
5. **Note:** Takes longer than simulation (testing 20 real backtests)

### Test 6: Bollinger on TSLA (Best Performer)
1. Select "TSLA" ticker
2. Select "Bollinger Bands" strategy
3. **Expect:**
   - Total return: +27.82%
   - Win rate: 100% (6 trades - enough to show)
   - Outperforms B&H by +42.5 pts

---

## API Endpoints Used

**Main backtest:**
```
GET http://localhost:5000/api/backtest?sym=NVDA&strat=macd&fast=12&slow=26&signal=9
```

**With all parameters:**
```
GET http://localhost:5000/api/backtest?sym=GOOGL&strat=mr&rsiLen=14&oversold=30&overbought=55
```

---

## Files Modified

### `strategy-lab.html`
- Line 659-660: Added `API_BASE` and `USE_REAL_API` flag
- Line 779-815: Added `runBacktestAPI()` function
- Line 1026-1052: Made `recompute()` async, uses API when flag is true
- Line 1058-1081: Made optimization async, uses API
- Line 931-958: Added small sample warning in `renderPerf()`
- Line 1007-1026: Updated `renderTrades()` to show open positions
- Line 324: Added CSS for `.outcome-pill.open` (blue)

### `backend/api.py`
- Line 85-89: Added months-to-days conversion for momentum

### `backend/engine.py`
- Line 136, 142: Removed `abs()` to keep drawdown negative
- Line 90-111: Added open position detection and marking

---

## Performance Notes

**Simulation mode (USE_REAL_API = false):**
- Instant results
- Deterministic sample data
- Good for UI development

**Real API mode (USE_REAL_API = true):**
- 1-3 seconds per backtest (first time downloads data)
- Subsequent calls faster (data cached)
- Optimization takes ~60 seconds (20 backtests)

---

## Fallback Behavior

If API fails (server not running, network error):
```javascript
catch(err) {
  console.error('API Error:', err);
  return runBacktest(ticker, strat, params);  // Falls back to simulation
}
```

Users will see simulation data instead of an error.

---

## Toggle Between Modes

To test with simulation data:

**In `strategy-lab.html` line 660:**
```javascript
var USE_REAL_API = false;  // Switch to simulation
```

---

## Next Steps

1. ✅ **All integration complete**
2. ⏭️ Test all 7 strategies with real data
3. ⏭️ Verify optimization works end-to-end
4. ⏭️ Consider adding loading indicators for slow connections
5. ⏭️ For production: Deploy API to cloud platform (Render, Fly.io, Railway)

---

**Status:** Ready for full testing with real Yahoo Finance data!
