# Trendably

S&P 500 strategy learning platform with real backtest engine.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate grid data:**
   ```bash
   # Test with single ticker first (fast)
   python backend/run.py --tickers NVDA

   # Generate full grid for all stocks (5-10 minutes)
   python backend/run.py
   ```

   This creates:
   - `data/grid.json` - Main results file
   - `data/grid.js` - JavaScript version for offline use
   - `data/prices/*.js` - Individual stock price data

3. **Start the API server (for Strategy Lab):**
   ```bash
   python backend/api.py
   ```
   Server runs at `http://localhost:5000`

## Running Locally

### Option 1: Open files directly
- Double-click HTML files to open in browser
- Grid works offline (uses `data/grid.js`)
- Strategy Lab requires API server running

### Option 2: Use a local server
```bash
# Python 3
python -m http.server 8000

# Then open http://localhost:8000
```

## Pages

- `index.html` - Homepage
- `the-grid.html` - Strategy comparison grid (works offline)
- `strategy-lab.html` - Interactive strategy testing (requires API)
- `market-weather.html` - Market conditions overview
- `sector-technology.html` - Sector analysis
- `industry.html` - Industry details
- `stock-detail.html` - Individual stock analysis
- `study-room.html` - Strategy education hub
- `study-lesson.html` - Interactive lessons

## Deployment Notes

### Frontend (Static Pages)
Can be hosted on:
- Netlify
- Vercel
- GitHub Pages
- Cloudflare Pages

### Backend API (Required for Strategy Lab)
Strategy Lab needs a Python server. Host on:
- **Render** (recommended) - Free tier available, auto-deploy from GitHub
- **Fly.io** - Generous free tier
- **Railway** - Simple Python deployment
- **PythonAnywhere** - Python-specific hosting

### Data Updates
Re-run `python backend/run.py` monthly to refresh backtest results. Can be automated with:
- GitHub Actions (commit fresh data)
- Scheduled job on hosting platform
- Local cron job

## Architecture

```
backend/
  ├── api.py          # Flask API for Strategy Lab
  ├── run.py          # Grid data generator
  ├── engine.py       # Backtest engine core
  ├── strategies.py   # Trading strategy definitions
  ├── data.py         # Yahoo Finance data fetcher
  ├── universe.py     # S&P 500 universe loader
  └── config.py       # Settings

data/
  ├── grid.json       # Generated: full backtest results
  ├── grid.js         # Generated: JavaScript version
  └── prices/         # Generated: individual stock data

cache/                # Downloaded price history (gitignored)
```

## Key Features

- **Real backtests**: Uses `backtesting.py` library with Yahoo Finance data
- **7 strategies**: MA Crossover, Golden Cross, MACD, Bollinger Bands, Momentum, Mean Reversion, Breakout
- **Parameter tuning**: Adjust strategy parameters in real-time
- **Optimization**: Find best parameter combinations
- **Trade-by-trade analysis**: See every entry/exit with dates and returns
- **No fake data**: All numbers come from real backtests, clearly labeled when sample data is used

## Important Notes

1. **Repository Privacy**: This repository should remain **private** as it contains proprietary FinStrategyGrid code.

2. **BRK-B Handling**: Berkshire Hathaway uses `BRK-B` internally (Yahoo format) but displays as `BRK.B` (user-familiar format).

3. **API Requirement**: Strategy Lab requires the Python API server running. Plan for separate backend hosting before going live.

4. **Data Freshness**: Grid data should be regenerated monthly for up-to-date results.

## License

Private - All rights reserved.
