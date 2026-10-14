"""Flask API for Strategy Lab — wraps the existing backtest engine.

Run with:
    python backend/api.py

Then test with:
    http://localhost:5000/api/backtest?sym=NVDA&strat=macd&fast=12&slow=26&signal=9
"""

from flask import Flask, request, jsonify
import sys
from pathlib import Path

# Import existing engine
from engine import run_cell
from strategies import REGISTRY

app = Flask(__name__)


@app.route('/api/backtest', methods=['GET'])
def backtest():
    """
    Run a single backtest for Strategy Lab.

    Query params:
        sym: ticker (e.g. NVDA)
        strat: strategy id (ma, gc, macd, bb, mom, mr, bo)
        window: 1y, 3y, or 5y (optional, defaults to 1y)
        ...plus strategy-specific parameters (e.g. fast=12, slow=26)

    Example: /api/backtest?sym=NVDA&strat=macd&fast=12&slow=26&signal=9
    """
    try:
        ticker = request.args.get('sym', 'NVDA').upper()
        strat_id = request.args.get('strat', 'macd').lower()
        window_id = request.args.get('window', '1y')

        # Map frontend strategy IDs to backend
        strat_map = {
            'ma': 'ma_crossover',
            'gc': 'golden_cross',
            'macd': 'macd',
            'bb': 'bollinger',
            'mom': 'momentum',
            'mr': 'mean_reversion',
            'bo': 'breakout',
            'bh': 'buy_hold'
        }

        backend_strat = strat_map.get(strat_id, strat_id)

        # Check if strategy exists
        if backend_strat not in REGISTRY:
            return jsonify({'error': f'Unknown strategy: {strat_id}'}), 400

        # Parse custom parameters and convert to integers where needed
        # The frontend sends decimals, but rolling windows need integers
        custom_params = {}
        for key in request.args:
            if key not in ['sym', 'strat', 'window']:
                try:
                    val = float(request.args[key])
                    # Parameters that must be integers (for rolling windows)
                    if key in ['fast', 'slow', 'signal', 'period', 'rsiLen',
                               'oversold', 'overbought', 'channel', 'lookback',
                               'rebalance', 'entry_days', 'exit_days']:
                        custom_params[key] = int(val)
                    else:
                        custom_params[key] = val
                except ValueError:
                    pass

        # Map frontend parameter names to backend names
        param_map = {
            'rsiLen': 'period',         # Mean Reversion: rsiLen -> period
            'oversold': 'buy_below',    # Mean Reversion: oversold -> buy_below
            'overbought': 'sell_above', # Mean Reversion: overbought -> sell_above
            'stddev': 'width',          # Bollinger: stddev -> width
            'channel': 'entry_days'     # Breakout: channel -> entry_days (assuming single param)
        }

        mapped_params = {}
        for k, v in custom_params.items():
            # Convert months to days for momentum lookback
            if k == 'lookback':
                mapped_params[k] = int(v * 21)  # 1 month ≈ 21 trading days
            else:
                mapped_params[param_map.get(k, k)] = v

        # Run backtest with extended=True for Strategy Lab (includes trades, equity curve, etc.)
        # Parameters are passed via **kwargs, not a dict
        result = run_cell(ticker, backend_strat, window_id, prices=None, extended=True, **mapped_params)

        if result is None:
            return jsonify({'error': f'No data for {ticker}'}), 404

        if result.get('status') != 'ok':
            return jsonify({'error': result.get('status', 'unknown error')}), 400

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'Trendably API is running'})


if __name__ == '__main__':
    print("=" * 60)
    print("Trendably Strategy Lab API")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("\nTest endpoints:")
    print("  Health: http://localhost:5000/api/health")
    print("  Backtest: http://localhost:5000/api/backtest?sym=NVDA&strat=macd")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    app.run(debug=True, port=5000, host='127.0.0.1')
