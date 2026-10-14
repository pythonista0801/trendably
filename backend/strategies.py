"""Every strategy is one small class. Add a strategy = write a WindowedStrategy class whose next()
starts with the warm-up check, then add it to REGISTRY."""

import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover


# ---------- Indicator helpers ----------
def sma(values, n):
    return pd.Series(values).rolling(n).mean().values


def ema(values, n):
    return pd.Series(values).ewm(span=n, adjust=False).mean().values


def rsi(values, n=14):
    delta = pd.Series(values).diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = -delta.clip(upper=0).rolling(n).mean()
    return (100 - 100 / (1 + gain / loss)).values


def rolling_high(values, n):
    return pd.Series(values).rolling(n).max().shift(1).values   # previous n days, excluding today


def rolling_low(values, n):
    return pd.Series(values).rolling(n).min().shift(1).values


def macd_line(values, fast, slow):
    return ema(values, fast) - ema(values, slow)


def lower_band(values, n, k):
    s = pd.Series(values)
    return (s.rolling(n).mean() - k * s.rolling(n).std()).values


def past_return(values, n):
    return pd.Series(values).pct_change(n).values


# ---------- Base class: warm-up before the returns window ----------
class WindowedStrategy(Strategy):
    """The engine sets start_bar. Before it, indicators fill up but nothing is traded,
    so every strategy starts the returns window on the same day with ready indicators."""
    start_bar = 0

    def warming_up(self):
        return len(self.data) <= self.start_bar


# ---------- Trend strategies ----------
class MACrossover(WindowedStrategy):
    """Buy when the fast average crosses above the slow one; sell on the reverse cross."""
    fast, slow = 20, 50

    def init(self):
        self.ma_fast = self.I(sma, self.data.Close, self.fast)
        self.ma_slow = self.I(sma, self.data.Close, self.slow)

    def next(self):
        if self.warming_up():
            return
        if crossover(self.ma_fast, self.ma_slow):
            self.buy()
        elif crossover(self.ma_slow, self.ma_fast):
            self.position.close()


class GoldenCross(MACrossover):
    """The classic slow version: 50-day average crossing the 200-day."""
    fast, slow = 50, 200


class MACD(WindowedStrategy):
    """Buy when the MACD line crosses above its signal line; sell on the reverse cross."""
    fast, slow, signal = 12, 26, 9

    def init(self):
        self.macd = self.I(macd_line, self.data.Close, self.fast, self.slow)
        self.sig = self.I(ema, self.macd, self.signal)

    def next(self):
        if self.warming_up():
            return
        if crossover(self.macd, self.sig):
            self.buy()
        elif crossover(self.sig, self.macd):
            self.position.close()


class Momentum(WindowedStrategy):
    """Hold the stock while its past 12-month return is positive. Checked once a month."""
    lookback, rebalance = 252, 21

    def init(self):
        self.mom = self.I(past_return, self.data.Close, self.lookback)

    def next(self):
        if self.warming_up():
            return
        if (len(self.data) - self.start_bar - 1) % self.rebalance:   # only on rebalance days
            return
        if self.mom[-1] > 0 and not self.position:
            self.buy()
        elif self.mom[-1] <= 0 and self.position:
            self.position.close()


class Breakout(WindowedStrategy):
    """Buy when price clears its recent high; sell on a new recent low."""
    entry_days, exit_days = 20, 10

    def init(self):
        self.upper = self.I(rolling_high, self.data.High, self.entry_days)
        self.lower = self.I(rolling_low, self.data.Low, self.exit_days)

    def next(self):
        if self.warming_up():
            return
        price = self.data.Close[-1]
        if not self.position and price > self.upper[-1]:
            self.buy()
        elif self.position and price < self.lower[-1]:
            self.position.close()


# ---------- Mean-reversion strategies ----------
class MeanReversion(WindowedStrategy):
    """Buy when RSI shows the stock oversold; sell once it recovers."""
    period, buy_below, sell_above = 14, 30, 55

    def init(self):
        self.rsi = self.I(rsi, self.data.Close, self.period)

    def next(self):
        if self.warming_up():
            return
        if not self.position and self.rsi[-1] < self.buy_below:
            self.buy()
        elif self.position and self.rsi[-1] > self.sell_above:
            self.position.close()


class Bollinger(WindowedStrategy):
    """Buy when price falls below the lower Bollinger band; sell when it returns to the 20-day average."""
    period, width = 20, 2

    def init(self):
        self.mid = self.I(sma, self.data.Close, self.period)
        self.lower = self.I(lower_band, self.data.Close, self.period, self.width)

    def next(self):
        if self.warming_up():
            return
        price = self.data.Close[-1]
        if not self.position and price < self.lower[-1]:
            self.buy()
        elif self.position and price > self.mid[-1]:
            self.position.close()


# ---------- Benchmark ----------
class BuyAndHold(WindowedStrategy):
    """Benchmark: buy on day one, never sell."""

    def init(self):
        pass

    def next(self):
        if self.warming_up():
            return
        if not self.position:
            self.buy()


# ---------- Registry: id -> (display name, class). Order = column order on the page. ----------
REGISTRY = {
    "ma_crossover":   ("MA crossover",    MACrossover),
    "golden_cross":   ("Golden cross",    GoldenCross),
    "macd":           ("MACD",            MACD),
    "momentum":       ("Momentum",        Momentum),
    "breakout":       ("Breakout",        Breakout),
    "mean_reversion": ("Mean reversion",  MeanReversion),
    "bollinger":      ("Bollinger bands", Bollinger),
    "buy_hold":       ("Buy & hold",      BuyAndHold),
}
