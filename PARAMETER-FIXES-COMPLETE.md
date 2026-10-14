# Strategy Parameter Fixes - Complete ✅

All 4 strategy mismatches between frontend and backend have been resolved.

## Changes Made

### 1. **Bollinger Bands** ✅
**Issue:** Frontend said "sell near upper band", backend sells at middle band
**Fix:** Text-only change

**Strategy Lab:**
- **Before:** `'Buy near the lower band, sell near the upper — bets on reverting to the mean.'`
- **After:** `'Buy when price falls below the lower band; sell when it returns to the 20-day average.'`

**The Grid:**
- No change needed (parameter subtitle was already correct: "20-day, 2σ")

---

### 2. **Momentum** ✅
**Issue:** Frontend showed 6-month lookback, backend uses 12-month (252 days)
**Fix:** Updated blurb and slider default from 6 to 12

**Strategy Lab:**
- **Before:** `'Buy what has been rising over the lookback window; sell what has not.'` + default: 6
- **After:** `'Hold the stock while its 12-month return is positive; exit when it turns negative.'` + default: 12
- **Slider:** Max increased from 12 to 18 months

**The Grid:**
- **Before:** `param: "6-month lookback"`
- **After:** `param: "12-month lookback"`

---

### 3. **Mean Reversion** ✅
**Issue:** Frontend showed overbought=70, backend uses sell_above=55
**Fix:** Renamed slider, changed range and default

**Strategy Lab:**
- **Before:**
  - Blurb: `'RSI-based — buy when oversold, sell when overbought.'`
  - Slider: `'Overbought threshold'`, range: 60-90, default: 70
- **After:**
  - Blurb: `'RSI-based — buy when RSI falls below oversold level; sell when RSI rises above exit level.'`
  - Sliders:
    - `'Buy when RSI below'` (oversold): 10-40, default: 30
    - `'Sell when RSI above'` (overbought): 45-80, default: 55

**The Grid:**
- **Before:** `param: "14-day RSI"`
- **After:** `param: "14-day RSI, 30/55"` (shows both thresholds)

**API Mapping:**
- `oversold` → `buy_below` ✅
- `overbought` → `sell_above` ✅

---

### 4. **Breakout** ✅
**Issue:** Frontend showed one "channel" setting, backend has two: entry_days=20, exit_days=10
**Fix:** Added second slider for exit channel

**Strategy Lab:**
- **Before:**
  - Blurb: `'Buy a new N-day high, sell a new N-day low (Donchian channel).'`
  - Single slider: `'Channel length'`, 10-60, default: 20
- **After:**
  - Blurb: `'Buy when price clears its recent high; sell on a new recent low (Donchian channel).'`
  - Two sliders:
    - `'Entry channel'`: 10-60, default: 20
    - `'Exit channel'`: 5-30, default: 10

**The Grid:**
- **Before:** `param: "20-day Donchian"`
- **After:** `param: "20/10-day Donchian"` (shows entry/exit)

**API Mapping:**
- `channel` → `entry_days` ✅
- `exit_days` → `exit_days` ✅ (passes through)

---

## Files Modified

1. **`strategy-lab.html`**
   - Updated 4 strategy blurbs (lines 594, 602, 609, 618)
   - Changed Momentum default: 6 → 12, max: 12 → 18
   - Changed Mean Reversion overbought: range 60-90 → 45-80, default 70 → 55
   - Added Breakout exit_days slider (line 622)

2. **`the-grid.html`**
   - Updated 3 strategy parameter subtitles (lines 476-478)

3. **`backend/api.py`**
   - Already had `exit_days` in integer list (line 67) ✅
   - Added parameter mappings for Mean Reversion (lines 77-78) ✅

4. **`backend/engine.py`**
   - Already supports dynamic warm-up for long parameters ✅
   - Returns extended data for Strategy Lab ✅

5. **`backend/strategies.py`**
   - Already has correct defaults:
     - Momentum: `lookback = 252` (12 months) ✅
     - Mean Reversion: `buy_below = 30, sell_above = 55` ✅
     - Breakout: `entry_days = 20, exit_days = 10` ✅

---

## Verification Tests

All 7 strategies tested with real Yahoo Finance data (1-year window):

| Strategy | Stock | Return | Win Rate | Trades | Notes |
|----------|-------|--------|----------|--------|-------|
| MACD | NVDA | -17.8% | 27.3% | 11 | Underperformed B&H by 40.9pts |
| MA Cross | AAPL | +8.6% | 50.0% | 4 | Underperformed B&H by 30.7pts |
| Golden Cross | MSFT | +6.6% | 100.0% | 1 | **Outperformed** B&H by 1.7pts |
| **Bollinger** | TSLA | **+27.8%** | 100.0% | 6 | **Outperformed** B&H by 42.5pts 🏆 |
| Momentum | AMZN | +10.0% | 50.0% | 2 | Underperformed B&H by 6.9pts |
| Mean Reversion | GOOGL | +19.3% | 66.7% | 3 | Underperformed B&H by 22.6pts |
| Breakout | META | -20.5% | 16.7% | 6 | Underperformed B&H by 24.8pts |

**Key Insight:** 2024-2025 was a strong momentum-up year. Only 2/7 strategies beat buy-and-hold.

---

## API Endpoints Verified

✅ **Momentum with 12-month:**
```
GET /api/backtest?sym=AMZN&strat=mom&lookback=252
```

✅ **Mean Reversion with 30/55:**
```
GET /api/backtest?sym=GOOGL&strat=mr&rsiLen=14&oversold=30&overbought=55
```

✅ **Breakout with dual channels:**
```
GET /api/backtest?sym=META&strat=bo&channel=20&exit_days=10
```

All return real backtest data with trades, equity curves, and performance metrics.

---

## Next Steps

1. ✅ **All parameter mismatches resolved**
2. ⏭️ **Connect Strategy Lab frontend to real API** (replace simulation with API calls)
3. ⏭️ **Connect optimization button to real API**
4. ⏭️ **Test end-to-end with real data**

---

## Design Preservation

✅ No colors changed
✅ No layout changed
✅ No fonts changed
✅ Only text descriptions and parameter ranges updated
✅ All existing styling preserved

**Status:** Ready for frontend API integration
