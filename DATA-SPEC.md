# Trendably — data, calculations and placeholders

Companion to `HANDOVER.md`. This file lists **every figure each page shows**: what it means, where the sample value sits in the code now, which data stream feeds it, exactly how to calculate it, how often it refreshes, and what replaces the placeholder.

**The backtest engine already exists.** It is the FinStrategyGrid engine, now in `backend/` (Part I). It runs real backtests on real Yahoo Finance prices. The Grid and Strategy Lab are wired to it, not rebuilt.

Anything marked **PROPOSAL** is a suggested method that Natalie has not signed off. Anything marked **DECISION** is a choice that must be made before building.

---

## Part A — Principles

1. **One snapshot per refresh.** A backend job computes every market figure once per refresh cycle and writes JSON files. Every page reads those files. No page calculates market data on its own, and no figure is typed by hand. This alone fixes the sample inconsistencies listed in Part F.
2. **Pages only render.** The calculations below run in Python on the backend (pandas/numpy). The one exception is Strategy Lab, which re-runs a backtest in the browser when the user moves a slider (Part D.6).
3. **Every number carries its time.** Each JSON file has an `asOf` timestamp, and every page shows "Updated HH:MM ET · 15-min delayed" from it.
4. **Placeholders stay labelled** ("sample data") until their real source is connected. Remove the label only when the figure is live.
5. **Text that contains figures is generated from the figures** — templates or an LLM given the computed numbers — never written once and left to go stale.

## Part B — Data streams

| ID | Stream | Contents | Suggested source | Refresh |
|---|---|---|---|---|
| S1 | Daily price history | Adjusted daily open, high, low, close, volume for all S&P 500 members and these indexes: `^GSPC` (S&P 500), `^IXIC` (NASDAQ Composite), `^NDX` (Nasdaq 100), `^DJI`, `^N225`, `^FTSE`, `^GDAXI`, `^VIX`, `^TNX` (10Y yield), `^IRX` (3-month T-bill). At least **3 years** (200-day averages and 1-year backtests need warm-up). | Yahoo Finance via `yfinance`: `yf.download(tickers, period="3y", auto_adjust=True, group_by="ticker")` | Nightly after close |
| S2 | Intraday quotes | Last price, previous close, day volume for members and indexes. | `yfinance` (`Ticker.fast_info`, or `yf.download(..., period="1d", interval="5m")`) | Every 15 min, 9:30–16:00 ET |
| S3 | Membership and classification | S&P 500 members with **GICS** sector, industry group, industry, sub-industry; shares outstanding; market cap. | Members + GICS sector/sub-industry: Wikipedia "List of S&P 500 companies" table. Map sub-industry → industry with the published GICS structure. Market cap / shares: `yfinance` `.info` (`marketCap`, `sharesOutstanding`). | Weekly, plus on index changes |
| S4 | Fundamentals | Trailing and forward P/E, EV/EBITDA, price-to-sales, price-to-book, revenue growth, EPS growth, profit margin, return on equity, free cash flow, debt-to-equity, average volume. | `yfinance` `.info`: `trailingPE`, `forwardPE`, `enterpriseToEbitda`, `priceToSalesTrailing12Months`, `priceToBook`, `revenueGrowth`, `earningsGrowth`, `profitMargins`, `returnOnEquity`, `freeCashflow`, `debtToEquity`, `averageVolume`. | Nightly; values change after earnings |
| S5 | News | Headlines for the biggest movers and each sector's top contributors. | `yfinance` `Ticker.news`, or a news API (Finnhub, Polygon, NewsAPI). | Every 15 min for the day's top movers only |
| S6 | Language model | Tutor replies; optional plain-language "why" sentences built from computed figures. | Anthropic API, called **from the backend only** (never put an API key in a page). | On request |

**Source cautions**

- **DECISION — licensing.** `yfinance` is an unofficial scraper of Yahoo. It is fine for building and testing, but Yahoo's terms don't permit commercial redistribution and it rate-limits and breaks without notice. Before launch choose a licensed feed (for example Polygon.io, Financial Modeling Prep, Tiingo, EODHD). The JSON shapes in Part E stay the same whichever feed is used.
- **Yahoo's sector and industry labels are not GICS** (for example it says "Technology", not "Information Technology", and its industries differ). Always take classification from S3, never from `.info["sector"]`.
- **Index weights are approximate.** Official S&P weights use float-adjusted market cap and require a licence. Use `marketCap`, and keep the "≈" sign in the interface.
- `debtToEquity` from Yahoo is a percentage (17.2 means 0.172). Divide by 100.
- Yahoo's own `beta` uses 5 years of monthly data. Calculate our own from S1 (Part C) so the method matches what the glossary explains.

### Backend layout (suggested)

```
backend/
  fetch_prices.py        S1, S2 → data/raw/
  fetch_universe.py      S3 → data/universe.json
  fetch_fundamentals.py  S4 → data/raw/fundamentals.json
  compute_snapshot.py    → data/snapshot.json        (market-wide, every 15 min)
  compute_stocks.py      → data/stocks/<SYM>.json    (nightly + price fields every 15 min)
  compute_groups.py      → data/sectors/<slug>.json, data/industries/<slug>.json
  run.py (existing)      → data/grid.json, data/grid.js, data/prices/<SYM>.js   (Grid; see Part I)
  api.py (to add)        → /api/backtest for Strategy Lab, /api/tutor for lessons
  scheduler              cron / APScheduler: 15-min loop in market hours, nightly job at 18:00 ET
```

## Part C — Shared definitions (use these everywhere)

`P_t` is the adjusted close on day t; `r_t = P_t / P_{t-1} − 1` is the daily return; trading days per year = 252.

| Measure | Formula |
|---|---|
| Period return | `P_end / P_start − 1`, using adjusted closes. 1W = 5 trading days, 1M = 21, 3M = 63, 6M = 126, 1Y = 252. 1D intraday = `last / previous close − 1`. |
| Points change | `last − previous close` |
| Simple moving average SMA(n) | mean of the last n closes |
| Exponential moving average EMA(n) | `EMA_t = α·P_t + (1−α)·EMA_{t−1}`, α = 2/(n+1); seed with SMA(n) |
| RSI(n) | **The engine uses simple n-day averages of gains and losses** (`strategies.rsi`). Use that same function for Stock Detail's RSI so the numbers match. (Wilder's smoothing is the textbook alternative: average gain and average loss over n days with smoothing `avg_t = (avg_{t−1}·(n−1) + x_t)/n`; `RSI = 100 − 100/(1 + avgGain/avgLoss)`.) |
| MACD(f,s,g) | `MACD = EMA(f) − EMA(s)`; `signal = EMA(g)` of MACD; `histogram = MACD − signal` |
| Bollinger(n,k) | middle = SMA(n); upper/lower = middle ± k·(standard deviation of the last n closes) |
| Donchian(n) | upper = highest high of the previous n days; lower = lowest low of the previous n days (exclude today) |
| ATR(14) | true range = max(high−low, |high−prev close|, |low−prev close|); Wilder-smoothed over 14 days |
| Annualised volatility | standard deviation of the last 252 daily log returns × √252 |
| Downside volatility | same, using only days with negative returns (others set to 0), × √252 |
| Max drawdown | over the window: `min_t (P_t / max_{s≤t} P_s − 1)` |
| Beta | `Cov(r_stock, r_S&P) / Var(r_S&P)` over the last 252 daily returns |
| Sharpe ratio | `(annualised return − risk-free rate) / annualised volatility`; risk-free = latest `^IRX` / 100; annualised return = `(1+total)^(252/days) − 1` |
| Market-cap weight in a group | `cap_i / Σ cap_group` |
| Group move (index, sector, industry) | cap-weighted: `Σ w_i·r_i`, weights taken at the **start** of the period |
| Contribution of a stock to its group | `c_i = w_i · r_i` (percentage points). Leaders = largest positive c; laggards = most negative c. |
| Share of a group's move | `c_i / Σ c` (only meaningful when Σc isn't near zero — if |Σc| < 0.1 pt, show "mixed" instead of a share) |
| Breadth | % of S&P 500 members with r > 0 over the period |
| Percentile rank | position of a value among a comparison set (all S&P 500 members, or its sector), 0–100 |

## Part D — Page by page

### D.0 Ticker strip (top of every page)

| Shown now | Sample | Source | Calculation | Refresh |
|---|---|---|---|---|
| S&P 500 day move | +0.8% | S2 `^GSPC` | 1D return | 15 min |
| NASDAQ day move | +1.1% | S2 `^IXIC` | 1D return | 15 min |
| VIX | 14.8 | S2 `^VIX` | level, not a % | 15 min |
| NVDA day move | +2.4% (but −2.2% on Stock Detail) | S2 | 1D return | 15 min |
| 10Y yield | 4.18% | S2 `^TNX` | level, % | 15 min |

The strip is hard-coded in each page's HTML. Replace with one shared script that reads `snapshot.json → strip`.
**DECISION:** what the fifth slot shows. Options: the day's biggest S&P mover, the user's watched stock, or the stock open on Stock Detail.

### D.1 Landing — `index.html`

Every figure is a repeat of Market Weather or Stock Detail and must read the same files.

| Figure | Sample | Source |
|---|---|---|
| Market mood label | Cautious | `snapshot.mood.label` (D.2) |
| S&P 500 day move | +0.8% | `snapshot.index.move` |
| Leading sector + move | Energy +1.8% | `snapshot.sectors`, highest 1D move |
| Four emotions + "Uncertainty leads today" | 64 / 48 / 41 / 35 | `snapshot.emotions` (D.2) |
| Best and worst sector | Energy +1.8%, IT −1.4% | `snapshot.sectors` |
| Sector → industry → stock chain | IT −1.4%, Semiconductors −2.1%, NVDA −2.2% | sector and industry files, 1D; pick the industry and stock with the largest contribution |
| Example score card | NVDA 69; 85/54/29/88 | `stocks/<SYM>.json → score` |

Placeholders: "Start free", "No card required. Full depth on a handful of stocks, free." — **DECISION:** sign-up and the free vs paid (Core) limits are not defined.

### D.2 Market Weather — `market-weather.html`

| Figure | Sample (where) | Source | Calculation | Refresh |
|---|---|---|---|---|
| Headline answer | "Mixed — conditions call for care…" (HTML) | snapshot | Template keyed to the mood label (three fixed sentences, one per label) | 15 min |
| Mood gauge: Calm / Cautious / Elevated risk | needle on Cautious (HTML) | derived | **PROPOSAL:** *Elevated risk* if VIX ≥ 25 **or** Fear ≥ 65; *Calm* if VIX < 16 **and** Fear < 40 **and** Uncertainty < 45; otherwise *Cautious*. Needle position = Fear score. | 15 min |
| Four emotions, each 0–100 | `var EMO` | S1, S2 | **PROPOSAL** below | 15 min |
| "X leads today" | from EMO | derived | highest of the four | 15 min |
| "Why this reading" text | HTML | derived | Template or LLM, given the three driver values and the leading emotion | 15 min |
| Volatility card | 19.4 (strip says 14.8) | S2 `^VIX` | VIX level; band: < 15 low, 15–20 mid-range, 20–30 elevated, > 30 high | 15 min |
| Breadth card | 34% advancing | S2 members | breadth, 1D | 15 min |
| Momentum card | +2.1% vs 20-day avg | S1 + S2 `^GSPC` | `last / SMA(20) − 1` | 15 min |
| Card explanations | HTML | derived | one sentence per band per card (template) | 15 min |
| Global markets chart, 1D/1W/1M/1Y | generated `series` | S1, S2: `^GSPC`, `^NDX`, `^N225`, `^FTSE`, `^GDAXI` | % change from the first point of the window; 1D uses 5-minute bars from that market's open | 15 min (1D), nightly (others) |
| Sector heatmap, 11 sectors | HTML tiles | S2 + S3 | sector 1D move, cap-weighted (Part C). Acceptable shortcut: the SPDR sector ETFs (XLK, XLF, XLV, XLY, XLC, XLI, XLP, XLE, XLU, XLB, XLRE) | 15 min |
| Sector panel: reason sentence | `var SEC[name][0]` (hand-written) | S5 + S6 | LLM summary of the top contributors' headlines, or omit until news is connected | 15 min |
| Sector panel: top two and bottom two stocks | `SEC[name][1..2]` | S2 + S3 | highest and lowest contributions in the sector, 1D | 15 min |
| Sector panel: weight | `SEC[name][3]` | S3 | sector cap / S&P 500 cap | weekly |
| "What this means for my strategy": three fit labels | HTML | backtests | **PROPOSAL:** for each strategy, average daily strategy return (default settings, all Grid stocks, past 3 years) on days in today's regime (D.6 regimes), minus its average on all days. > +0.02%/day → "Historically stronger fit"; < −0.02% → "weaker"; otherwise "Mixed". | nightly |
| "Mood & volatility refresh every 15 min" | static text | — | replace with the real `asOf` time | 15 min |

**Emotions — PROPOSAL.** Each is a 0–100 percentile against the past 252 trading days, so 50 means "a typical day this year". Each input is turned into a percentile first, then the inputs are averaged:

- **Fear:** VIX level; S&P 500 distance below its 20-day high; % of members below their 50-day average.
- **Uncertainty:** VIX level; cross-sectional spread of the 11 sector moves (standard deviation); 10-day realised volatility ÷ 60-day realised volatility.
- **Optimism:** breadth (1D); % of members above their 50-day average; S&P 500 20-day return.
- **Confidence:** S&P 500 above its 50- and 200-day averages (0, 50 or 100); 5-day average breadth; inverse of VIX.

They are scored separately, so they don't add up to 100 — the page already says this.
Note: the emotion history (252 days of % above 50-day average, breadth, sector spread) needs S1 for every member. Compute it once and store `data/history/market_internals.parquet`, then append daily.

### D.3 The Grid — `the-grid.html`

| Figure | Sample (where) | Source | Calculation | Refresh |
|---|---|---|---|---|
| Today's sector moves | HTML | snapshot | same as the heatmap | 15 min |
| Stock list (2 per sector, 22 stocks) | `universe` array | S3 | **DECISION:** keep this curated list, or let users search all ~500 | weekly |
| Seven strategies with fixed settings | HTML | — | defaults: MA 20/50, Golden Cross 50/200, MACD 12/26/9, Bollinger 20 / 2σ, Momentum 6 months, Mean Reversion RSI 14 (30/70), Breakout 20-day | static |
| **Result per stock × strategy** | `returnFor()` — **a hash of the ticker name, not a backtest** | `data/grid.json` (written by `backend/run.py`) | `GRID.results[ticker][window][strategy]` = `[annual %, total %, max drawdown %, win rate %, trades]`, or `null` when the stock lacks history. Outline the best strategy per stock. | monthly cache; re-run as often as wanted |

**Replace `returnFor(ticker, stratId)`** with a lookup into `window.GRID` (load `data/grid.js` with a `<script>` tag, so it also works by double-click). The page's strategy ids map to the engine's: `ma`→`ma_crossover`, `gc`→`golden_cross`, `macd`→`macd`, `bb`→`bollinger`, `mom`→`momentum`, `mr`→`mean_reversion`, `bo`→`breakout`. The engine also gives `buy_hold`, the benchmark.
**DECISION:** which window the Grid shows (the engine runs 1, 3 and 5 years; a switch like FinStrategyGrid's is easy), annual or total return, and whether buy-and-hold appears as an eighth column (recommended — a return means little without it).
Open: keep or remove the "Today's sector moves" block.

### D.4 Sector page — `sector-technology.html`

Make it a template: `sector.html?sector=<slug>`, one file per sector in `data/sectors/<slug>.json`.

| Figure | Sample (where) | Source | Calculation | Refresh |
|---|---|---|---|---|
| Sector move for 1D/1W/1M/6M/1Y | `TODAY` + `TF` scale/bias + seeded random (`rng`) — **synthetic** | S1 + S2 + S3 | cap-weighted period return of members (Part C) | 1D: 15 min; others nightly |
| "≈38% of the S&P 500" | text | S3 | sector cap / S&P 500 cap | weekly |
| "31 of 34 stocks rising" | computed from synthetic moves | S1/S2 | count of members with period return > 0 | with the move |
| "6 industries inside" | `IND` | S3 | count of GICS industries | weekly |
| "What moved the sector" paragraph | template already in code | derived | keep the template; feed it the real top industry and top two contributors | with the move |
| Leaders ("Pushing up") and laggards ("Holding back") | computed from synthetic moves | derived | top 3 positive and bottom 2 negative contributions | with the move |
| Stock row: "Pushed IT up — about N% as much as IT's whole net move" | template | derived | share of the group's move (Part C) | with the move |
| Stock row: "What usually moves it" | `IND[].stocks[][3]` (hand-written) | content | static per-stock description; generate once per stock with an LLM, review, store in `universe.json` | quarterly |
| Stock row: news slot | placeholder text | S5 | headlines for that stock for the period | 15 min |
| Industries: share of sector, move, share of the sector's move | `IND`, synthetic | S1/S2/S3 | weight = industry cap / sector cap; move = cap-weighted; share of move = industry contribution / sector total | with the move |
| Stock weights within the sector | `IND[].stocks[][2]` | S3 | stock cap / sector cap | weekly |

### D.5 Industry page — `industry.html?ind=<slug>`

Same calculations as the sector page, one level down. `data/industries/<slug>.json`.

| Figure | Sample | Calculation |
|---|---|---|
| Industry move per period | +4.7% (synthetic) | cap-weighted |
| "Information Technology: +3.9% · ahead of the sector by 0.8 pts" | derived | industry move − sector move, in points |
| "≈45% of the sector" | `IND` weight | industry cap / sector cap |
| "14 of 14 stocks rising" | derived | count |
| "≈17.1% of the S&P 500" | `SPX_W` (hard-coded 38) × share | industry cap / S&P 500 cap — replace `SPX_W` with the real sector weight |
| "Accounted for about 54% of the sector's net move" | derived | industry contribution / sector total |
| Leaders, laggards, full stock table (weight, share of move, move) | synthetic | as on the sector page |
| Other industries in the sector | synthetic | their moves for the same period |

### D.6 Strategy Lab — `strategy-lab.html?sym=<SYM>&strat=<id>`

**Important: the current `runBacktest()` is not a backtest.** It invents trades from a seeded random generator and scales them to land near a target return (`OUTPERF_CAP`, `OUTPERF_SCALE`, `OUTPERF_OFFSET`, `ticker.annualReturn`). It was built so the page behaves realistically. Replace it with the existing engine (Part I). The page layout, sliders and charts stay as they are.

**Where it runs — one engine, not two.** Sliders need a fresh backtest with custom settings, so the page calls a small backend endpoint, for example `GET /api/backtest?sym=NVDA&strat=macd&fast=12&slow=26&signal=9`, which calls `run_cell` with those settings. `backtesting.py` already accepts settings at run time (`Backtest(...).run(fast=12, slow=26)` overrides the class defaults), so the Python strategies stay the only source of truth. One run takes well under a second. (A JavaScript copy of the engine would mean two engines to keep in agreement — avoid it.)

**Engine rules, as built** (`backend/strategies.py`, `backend/engine.py`)

- `backtesting.py` library. Long or flat; never short. One position at a time, all-in (`STARTING_CASH` 10,000).
- A signal is read on the close of day t; the order fills at the **open of day t+1** (the library's default — no look-ahead).
- Windows: 1, 3 and 5 years (252 / 756 / 1,260 trading days), each with **260 warm-up days** in front where indicators fill but nothing trades. A stock without enough history for a window gets `null` for it.
- Costs: `COMMISSION = 0.0`. **DECISION:** keep at zero or add a cost (for example 0.0005 = 0.05% per trade).
- Positions still open at the end are closed and counted (`finalize_trades=True`).

**Strategy signals, as built** — the engine's defaults. Where the Trendably pages say something different, the page text is out of date (marked ⚠).

| Engine id (page id) | Strategy | Enter | Exit |
|---|---|---|---|
| `ma_crossover` (`ma`) | MA crossover, 20 / 50 | 20-day SMA crosses above 50-day | crosses below |
| `golden_cross` (`gc`) | Golden cross, 50 / 200 | 50-day SMA crosses above 200-day | crosses below |
| `macd` (`macd`) | MACD 12 / 26 / 9 | MACD line crosses above signal line | crosses below |
| `bollinger` (`bb`) | Bollinger 20-day, 2σ | close < lower band | close > **middle band** (20-day average) ⚠ page says "sell near the upper" |
| `momentum` (`mom`) | Momentum, **12-month** lookback ⚠ pages say 6-month | trailing 252-day return > 0, checked every 21 trading days | ≤ 0 at a check |
| `mean_reversion` (`mr`) | RSI 14 | RSI < 30 | RSI > **55** ⚠ page slider says overbought 70 |
| `breakout` (`bo`) | Breakout 20 / 10 | close > highest high of the previous 20 days | close < lowest low of the previous **10** days ⚠ page has one channel setting |
| `buy_hold` | Buy and hold | first day of the window | never (closed at the end) |

**DECISION:** for each ⚠ row, either change the page text and sliders to match the engine, or change the engine default. Strategy Lab's sliders map to the class attributes: `fast`/`slow` (MA, Golden cross, MACD), `signal` (MACD), `period`/`width` (Bollinger), `lookback`/`rebalance` (Momentum, in trading days), `period`/`buy_below`/`sell_above` (Mean reversion), `entry_days`/`exit_days` (Breakout).

**Figures shown.** The engine already returns total return, annual return, max drawdown, win rate and number of trades. The rest come from the same run — `run_cell` needs extending to also return them from `stats["_trades"]` and `stats["_equity_curve"]`, which the library already produces (measured over the window only, as `run_cell` does now):

| Figure | Calculation |
|---|---|
| Stock header price and day change | S2 |
| Total return | compound the daily equity curve: `E_end / E_start − 1` |
| Buy-and-hold return | `P_end / P_start − 1` over the same window |
| Strategy vs buy-and-hold | difference in percentage points |
| Number of trades | completed round trips |
| Win rate | % of trades with return > 0 after costs |
| Average per trade | mean of trade returns |
| Max drawdown | of the daily equity curve (marked to market every day, not just at exits) |
| Sharpe ratio | from daily equity returns (Part C) |
| Equity curve | `E_t`, scaled to start at 100, beside buy-and-hold scaled the same; mark entries and exits |
| Trade log | entry date, exit date, entry price, exit price, return, win/loss |
| Summary sentence | template, already in `renderVerdict()` — keep it, feed it real results |

**Performance by market condition.** Today `condPerf()` makes these numbers up with fixed multipliers. Replace it with:

- Tag every day in the window: **Calm** VIX < 18; **Volatile** VIX > 25; **Broad** breadth ≥ 60% of members up that day; **Narrow** breadth ≤ 40%. (Thresholds match Market Weather; days can sit in none or in two groups.)
- Return in a condition = compound the strategy's daily returns on the days in that condition.
- Win rate in a condition = win rate of trades **entered** on days in that condition.
- Show "too few trades" when a condition has fewer than 3 trades.
- Needs historical VIX (S1) and historical breadth (from `market_internals`, D.2). Ship both inside `data/prices/<SYM>.json` as a `regime` array, or as one shared `data/regimes.json`.

The ticker chips include **TSLA**, which isn't in the Grid's list. **DECISION:** use one shared stock universe for both pages.

### D.7 Stock Detail — `stock-detail.html?sym=<SYM>`

Today the page ignores `?sym=` and shows `SYM='NVDA'` with hard-coded values in `subscores` and the indicator rows built through `ind()`. Replace both with `data/stocks/<SYM>.json` (Part E).

**Header**

| Figure | Sample | Source / calculation |
|---|---|---|
| Name, ticker, breadcrumb (sector › industry) | NVIDIA, IT › Semiconductors | S3 |
| Price, change, % change today | $148.32, −3.34 (−2.2%) | S2 |
| Composite score and band label | 69, "Solid composite score" | below |
| Summary sentence | hand-written | template from the strongest and weakest sub-score, or an LLM given the sub-scores and key indicators |

**Sub-scores — PROPOSAL.** Each is 0–100, higher = more favourable. Each indicator is converted to a percentile rank first, then averaged.

| Sub-score | Sample | Inputs and comparison set |
|---|---|---|
| Momentum | 85 | 40% 6-month return, 30% 12-month return (both ranked across the S&P 500), 30% trend: share of the 20/50/200-day averages the price is above (0, 33, 67, 100) |
| Risk (higher = calmer) | 54 | 100 − average rank across the S&P 500 of annualised volatility, |max drawdown 1Y| and beta |
| Valuation (higher = cheaper) | 29 | 100 − average rank **within the stock's sector** of forward P/E, EV/EBITDA and price-to-sales. Negative or missing values are ranked as most expensive and flagged. |
| Fundamentals | 88 | average rank across the S&P 500 of revenue growth, EPS growth, profit margin, return on equity, plus (100 − rank of debt-to-equity) |
| **Composite** | 69 | 0.30 Momentum + 0.20 Risk + 0.20 Valuation + 0.30 Fundamentals — **weights still need Natalie's sign-off**. Round to a whole number. |
| Band labels | "Strong uptrend", "Rich vs. sector"… | ≥ 70 favourable · 40–69 middle · < 40 unfavourable; one label per sub-score per band (template table) |

Check: the sample 69 is consistent with these weights (0.3·85 + 0.2·54 + 0.2·29 + 0.3·88 = 68.5).

**Indicator groups.** Each row also has a one-line "meaning" that must be **chosen from a template by value band**, never fixed text (the samples, such as "currently one of the strongest readings on the Grid", become false as soon as values change).

| Group | Indicator | Sample | Source | Calculation |
|---|---|---|---|---|
| Price and performance | 1M / 3M / 6M / 1Y return | +6.8 / +19.5 / +34.2 / +58.7% | S1 | period return |
| | Distance from 52-week high | −4.1% | S1 | `last / max(high, 252d) − 1` |
| | 52-week high / low | $152.89 / $86.62 | S1 | max high / min low, 252 days |
| Momentum and trend | RSI (14) | 64 | S1 | Part C |
| | Price vs moving averages | "Above all 3" | S1 | count of SMA20/50/200 below the price |
| | 20 / 50 / 200-day averages | $139 / $126 / $108 | S1 | SMA |
| | MACD | +2.4, rising | S1 | MACD line; "rising" if today's histogram > yesterday's |
| | Momentum score | 85 | — | the sub-score above |
| Risk and volatility | Annualised volatility | 38.6% | S1 | Part C |
| | Beta | 1.72 | S1 | Part C, vs `^GSPC` |
| | Max drawdown (1 year) | −21.4% | S1 | Part C |
| | Downside volatility | 24.1% | S1 | Part C |
| | Sharpe ratio | 1.38 | S1 | Part C, 1-year |
| Valuation | P/E trailing / forward | 54.1 / 38.9 | S4 | `trailingPE`, `forwardPE` |
| | vs sector median P/E | +61% | S4 + S3 | `forwardPE / median(sector forwardPE) − 1`; **DECISION**: trailing or forward (forward suggested) |
| | EV/EBITDA | 41.3 | S4 | `enterpriseToEbitda` |
| | Price-to-sales | 26.1 | S4 | `priceToSalesTrailing12Months` |
| | Price-to-book | 48.7 | S4 | `priceToBook` |
| Fundamentals | Revenue growth (YoY) | +94.3% | S4 | `revenueGrowth` × 100 |
| | EPS growth (YoY) | +111.7% | S4 | `earningsGrowth` × 100 |
| | Profit margin | 55.0% | S4 | `profitMargins` × 100 |
| | Return on equity | 91.4% | S4 | `returnOnEquity` × 100 |
| | Free cash flow (12 months) | $27.1B | S4 | `freeCashflow`, formatted |
| | Debt-to-equity | 0.17 | S4 | `debtToEquity / 100` |
| Trading and activity | Average daily volume (30 days) | 218M | S1 | mean volume, last 30 days |
| | Today vs average volume | +32% | S2 + S1 | `today's volume / 30-day average − 1`; scale today's volume by elapsed share of the session before the close |
| | ATR (14) | $4.87 | S1 | Part C |
| | Liquidity | "Very high" | S1 | **PROPOSAL** by average daily dollar volume (price × volume): > $1B very high, $250M–1B high, $50–250M moderate, < $50M low |

Each group shows a short list and "See all N indicators". The glossary pop-up (`.gl-sheet`) content is written text, not data — keep it in a shared `glossary.json` so every page can use it.

Optional additions not built yet: "where it sits" (sector/industry rank), compact strategy results (from `backtests.json`), price chart (S1), news (S5).

### D.8 Study Room — `study-room.html`

| Figure | Now | Real source |
|---|---|---|
| Hero stats: lessons finished, concepts checked, chapters | computed from `localStorage['tb-study']` and the curriculum | same calculation; read progress from the user account once sign-in exists |
| Tier tiles: "6 chapters · 1 lesson ready · 0 done" | computed | same |
| Continue card | computed | same |
| Glossary search box | **does nothing** | search `glossary.json`; open the same pop-up as Stock Detail |
| Points | not shown | **DECISION:** per concept or per lesson, and the "understood" rule |
| Tales of Markets (16) | titles and one-line summaries only | written content; AI-generated drafts, reviewed |
| Practitioner and Mastery chapters | sketch titles | **the whole curriculum is being re-planned** (see the conversation of 14 Oct 2026); rewrite `<script id="curriculum">` when settled |

### D.9 Lesson template — `study-lesson.html?lesson=<id>`

| Item | Now | Real source |
|---|---|---|
| Lesson content | inline fallback + `lessons/<id>.json` | AI-generated JSON (HANDOVER §5.2, §6) |
| Market figures inside lessons | `<script id="market-data">` sample, via `{{tokens}}` | `data/snapshot.json`, same shape as `data/market-sample.json` |
| Snapshot pictures (strip, grid, weights, quote, moves) | drawn from that market data | same; they update automatically |
| Tutor | the preview's built-in `sample` capability | backend endpoint `POST /api/tutor` that calls the Anthropic API with the system prompt built in `sys()` |
| Progress | `localStorage['tb-study']` | user account |

### D.10 Controls that look live but aren't wired (all pages)

Search icon, notification bell and dot, the Study Room glossary search, "Start free", "Read more" news slots, and every "news will appear here" placeholder. Each needs either wiring or hiding before launch.

## Part E — JSON files the pages read

```jsonc
// data/snapshot.json — every 15 min
{ "asOf": "2026-10-14T15:45:00-04:00", "delayedMinutes": 15,
  "strip":  [{"name":"S&P 500","value":-0.6,"unit":"%"}, {"name":"VIX","value":19.4,"unit":""}],
  "index":  {"name":"S&P 500","level":6612.40,"points":-39.90,"move":-0.6},
  "drivers":{"vix":19.4,"vixBand":"mid-range","breadth":34,"momentum20d":2.1},
  "emotions":{"fear":48,"uncertainty":64,"optimism":41,"confidence":35},
  "mood":   {"label":"Cautious","headline":"…","why":"…"},
  "sectors":[{"name":"Information Technology","slug":"information-technology","weight":38,"move":-1.4,
              "top":[["AVGO",0.31]],"bottom":[["NVDA",-0.48]],"reason":"…"}],
  "global": {"1D":{"^GSPC":[…]}, "1W":{…}, "1M":{…}, "1Y":{…}},
  "strategyFit":[{"id":"mr","label":"Historically weaker fit","why":"…"}] }

// data/stocks/<SYM>.json — nightly, price fields every 15 min
{ "asOf":"…","sym":"NVDA","name":"NVIDIA Corporation","sector":"Information Technology","industry":"Semiconductors & Semiconductor Equipment",
  "price":148.32,"change":-3.34,"move":-2.2,
  "score":{"composite":69,"momentum":85,"risk":54,"valuation":29,"fundamentals":88},
  "indicators":{"ret1m":6.8,"ret3m":19.5,"ret6m":34.2,"ret1y":58.7,"fromHigh":-4.1,"high52":152.89,"low52":86.62,
                "rsi14":64,"aboveMAs":3,"sma20":139,"sma50":126,"sma200":108,"macd":2.4,"macdRising":true,
                "vol":38.6,"beta":1.72,"mdd1y":-21.4,"downVol":24.1,"sharpe":1.38,
                "pe":54.1,"fpe":38.9,"peVsSector":61,"evEbitda":41.3,"ps":26.1,"pb":48.7,
                "revGrowth":94.3,"epsGrowth":111.7,"margin":55.0,"roe":91.4,"fcf":27.1e9,"de":0.17,
                "avgVol30":218e6,"volVsAvg":32,"atr14":4.87,"liquidity":"Very high"},
  "about":"What usually moves it …","news":[{"title":"…","url":"…","time":"…"}] }

// data/sectors/<slug>.json and data/industries/<slug>.json — 1D every 15 min, other periods nightly
{ "asOf":"…","name":"Information Technology","weightOfIndex":38,
  "periods":{"1D":{"move":-1.4,"rising":9,"count":34},"1W":{…},"1M":{…},"6M":{…},"1Y":{…}},
  "industries":[{"slug":"semiconductors","name":"…","weight":45,"periods":{"1M":{"move":4.7,"contribution":2.1}}}],
  "stocks":[{"sym":"NVDA","name":"Nvidia","industry":"semiconductors","weight":22,"periods":{"1M":{"move":1.5,"contribution":0.33}}}] }

// data/grid.json (+ data/grid.js) — written by backend/run.py; this shape exists today
{ "generated":"2026-10-14",
  "strategies":[{"id":"ma_crossover","name":"MA crossover"}],
  "windows":[{"id":"1y","name":"1 year","days":252},{"id":"3y","name":"3 years","days":756},{"id":"5y","name":"5 years","days":1260}],
  "default_window":"5y","dates":["2021-07-…"],
  "stocks":[{"ticker":"NVDA","name":"…","gics_sector":"…","gics_sub_industry":"…","last":148.32,"chg":-2.2,"ret12":58.7,"vol":38.6,"avgvol":218000000,"days":2500}],
  "results":{"NVDA":{"1y":{"macd":[48.9,48.5,-34.1,55.0,20],"buy_hold":[…]}}} }   // [annual, total, maxDD, winRate, trades]
// data/prices/<SYM>.js — written by backend/run.py: closes aligned to grid.json "dates"
(window.PRICES = window.PRICES || {})["NVDA"] = [ … ];

// data/regimes.json — to add: daily VIX and breadth for Strategy Lab's market-condition split
{ "dates":[…], "vix":[…], "breadth":[…] }
```

## Part F — Sample inconsistencies (disappear once Part A rule 1 is in place)

- S&P 500 shows **+0.8%** in the strip and on the Landing, but the sector moves (mostly negative) and the lessons imply **−0.6%**.
- VIX is **14.8** in the strip and **19.4** on the Market Weather volatility card.
- NVDA is **+2.4%** in the strip on most pages and **−2.2%** on Stock Detail and Strategy Lab.
- Sector page and industry page periods are generated from a random seed, so they don't add up to the 1D heatmap.
- Grid results are a hash of the ticker name; Strategy Lab results are simulated; the two will not match each other.

## Part G — Replacement checklist, file by file

| File | Remove / replace | With |
|---|---|---|
| every page | hard-coded ticker strip | shared `strip.js` reading `snapshot.json` |
| `index.html` | hard-coded mood, emotions, sector moves, chain, score card | `snapshot.json`, sector/industry files, one `stocks/<SYM>.json` |
| `market-weather.html` | `EMO`, `SEC`, heatmap tiles, driver cards, generated `series`, strategy-fit text, refresh line | `snapshot.json` |
| `the-grid.html` | `returnFor()`; sector moves block; `universe` (if made dynamic) | `data/grid.js` from `backend/run.py`, `snapshot.json` |
| `sector-technology.html` → `sector.html` | `IND`, `TODAY`, `TF` + `rng` | `sectors/<slug>.json` |
| `industry.html` | `IND`, `TODAY`, `TF` + `rng`, `SPX_W` | `industries/<slug>.json` |
| `stock-detail.html` | `SYM`, `subscores`, all `ind({...})` values and meaning lines | `stocks/<SYM>.json` + meaning templates by band |
| `strategy-lab.html` | `tickers` prices/`annualReturn`/`vol`, `runBacktest()`, `condPerf()`, `OUTPERF_*` | `/api/backtest` calling `run_cell` (D.6), quotes from `snapshot.json` |
| `study-room.html` | glossary search (unwired) | `glossary.json` |
| `study-lesson.html` | `#market-data`, tutor `sample` call | `snapshot.json`, `/api/tutor` |

## Part H — Decisions needed (Natalie)

1. Data provider for launch (licensed feed vs `yfinance`).
2. Emotion, mood and strategy-fit formulas (D.2) — accept, adjust or replace.
3. Sub-score formulas and composite weights (D.7).
4. Grid window and return type, trading costs (engine has zero), buy-and-hold column (D.3, D.6), and the four ⚠ strategy-setting mismatches between the pages and the engine (D.6).
5. Fifth slot of the ticker strip (D.0).
6. One shared stock universe for the Grid and Strategy Lab; curated list or all ~500 (D.3).
7. Free vs Core limits and sign-up (D.1).
8. Study Room points rule and the re-planned curriculum (D.8).
9. Keep or remove the Grid's "Today's sector moves".

## Part I — The existing engine (`backend/`)

Carried over unchanged from FinStrategyGrid, apart from two paths in `config.py` so it fits this folder: the download cache is now `cache/` (was `data/`) and results go to `data/grid.json` (was `frontend/data/grid.json`).

| File | Job |
|---|---|
| `backend/config.py` | Settings: 10 years of history, windows 1y / 3y / 5y, 260 warm-up days, starting cash, commission, folders |
| `backend/universe.py` | Downloads the S&P 500 list with official GICS sector and sub-industry (Wikipedia, cached monthly) and filters it by `universe.json` |
| `backend/data.py` | Downloads adjusted daily prices from Yahoo Finance in batches of 50, cached monthly in `cache/` |
| `backend/strategies.py` | The eight strategies, one class each, plus `REGISTRY` |
| `backend/engine.py` | `run_cell` (one stock × strategy × window), `run_grid` (everything, in parallel across CPU cores), `save` |
| `backend/run.py` | Entry point |
| `universe.json` | Which stocks to cover. Empty lists = the whole S&P 500 |
| `requirements.txt` | `yfinance backtesting pandas numpy requests lxml` |

**Run it** from the `trendably` folder, with the virtual environment active:

```
pip install -r requirements.txt
python backend/run.py --tickers NVDA      # quick test, one stock
python backend/run.py                     # full S&P 500, about 5–10 minutes the first time
```

Tested here end to end on simulated prices (5 stocks × 8 strategies × 3 windows, including one stock with too little history): no errors, and `data/grid.json`, `data/grid.js` and `data/prices/*.js` were written in the shape shown in Part E. Your first real run is the true test.

**What it does not do yet** (needed by the Trendably pages): Sharpe ratio, average per trade, trade log and equity curve for one run (extend `run_cell`, D.6); custom settings from Strategy Lab's sliders (`/api/backtest`, D.6); performance by market condition (needs `regimes.json`); anything on Market Weather, the sector pages or Stock Detail beyond the `summary()` fields (`last`, `chg`, `ret12`, `vol`, `avgvol`).
