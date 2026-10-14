"""Test script for the Strategy Lab API.

Run after starting the API server (python backend/api.py).
Tests the API with real Yahoo Finance data.
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Health check passed")


def test_basic_backtest():
    """Test basic backtest with default parameters."""
    print("\n" + "="*60)
    print("TEST 2: Basic Backtest (NVDA + MACD, defaults)")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/backtest", params={
        'sym': 'NVDA',
        'strat': 'macd'
    })

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nResults:")
        print(f"  Ticker: {data.get('ticker')}")
        print(f"  Strategy: {data.get('strategy')}")
        print(f"  Total Return: {data.get('totalRet')}%")
        print(f"  Win Rate: {data.get('winRate')}%")
        print(f"  Number of Trades: {data.get('numTrades')}")
        print(f"  Max Drawdown: {data.get('maxDD')}%")
        print(f"  Sharpe Ratio: {data.get('sharpe')}")
        print(f"  Buy & Hold: {data.get('bhReturn')}%")
        print(f"✓ Basic backtest passed")
    else:
        print(f"✗ Error: {response.json()}")
        raise Exception("Basic backtest failed")


def test_custom_parameters():
    """Test backtest with custom parameters."""
    print("\n" + "="*60)
    print("TEST 3: Custom Parameters (AAPL + MA, fast=15, slow=40)")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/backtest", params={
        'sym': 'AAPL',
        'strat': 'ma',
        'fast': 15,
        'slow': 40
    })

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nResults:")
        print(f"  Total Return: {data.get('totalRet')}%")
        print(f"  Trades: {data.get('numTrades')}")
        print(f"  First trade: {data.get('trades', [{}])[0] if data.get('trades') else 'No trades'}")
        print(f"✓ Custom parameters test passed")
    else:
        print(f"✗ Error: {response.json()}")
        raise Exception("Custom parameters test failed")


def test_bollinger():
    """Test Bollinger Bands strategy."""
    print("\n" + "="*60)
    print("TEST 4: Bollinger Bands (TSLA, period=20, stddev=2)")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/backtest", params={
        'sym': 'TSLA',
        'strat': 'bb',
        'period': 20,
        'stddev': 2.0
    })

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nResults:")
        print(f"  Total Return: {data.get('totalRet')}%")
        print(f"  Win Rate: {data.get('winRate')}%")
        print(f"  Equity points: {len(data.get('equityPts', []))} points")
        print(f"  BH points: {len(data.get('bhPts', []))} points")
        print(f"✓ Bollinger test passed")
    else:
        print(f"✗ Error: {response.json()}")
        raise Exception("Bollinger test failed")


def test_mean_reversion():
    """Test Mean Reversion (RSI) strategy."""
    print("\n" + "="*60)
    print("TEST 5: Mean Reversion (MSFT, rsiLen=14, oversold=30, overbought=70)")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/backtest", params={
        'sym': 'MSFT',
        'strat': 'mr',
        'rsiLen': 14,
        'oversold': 30,
        'overbought': 70
    })

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nResults:")
        print(f"  Total Return: {data.get('totalRet')}%")
        print(f"  Avg Return per Trade: {data.get('avgRet')}%")
        print(f"✓ Mean Reversion test passed")
    else:
        print(f"✗ Error: {response.json()}")
        raise Exception("Mean Reversion test failed")


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("TRENDABLY API TEST SUITE")
        print("="*60)
        print("\nMake sure the API server is running:")
        print("  python backend/api.py")
        print("\nPress Ctrl+C to cancel, or Enter to continue...")
        input()

        test_health()
        test_basic_backtest()
        test_custom_parameters()
        test_bollinger()
        test_mean_reversion()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nThe API is working correctly with real Yahoo Finance data!")

    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API server")
        print("Make sure the server is running: python backend/api.py")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
