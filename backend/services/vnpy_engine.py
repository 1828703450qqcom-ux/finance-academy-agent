"""
vnpy-inspired Quantitative Backtesting Engine
Based on vnpy's architecture: CtaTemplate + BacktestingEngine + ArrayManager
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
from enum import Enum


# ==================== Data Objects ====================

class Direction(Enum):
    LONG = "多"
    SHORT = "空"

class Offset(Enum):
    OPEN = "开"
    CLOSE = "平"

class Interval(Enum):
    MINUTE = "1m"
    DAILY = "d"


@dataclass
class BarData:
    symbol: str
    datetime: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float = 0
    open_interest: float = 0


@dataclass
class TickData:
    symbol: str
    datetime: datetime
    last_price: float
    volume: float = 0
    bid_price_1: float = 0
    ask_price_1: float = 0


@dataclass
class OrderData:
    vt_orderid: str
    symbol: str
    direction: Direction
    offset: Offset
    price: float
    volume: float
    traded: float = 0
    status: str = "SUBMITTING"


@dataclass
class TradeData:
    vt_tradeid: str
    vt_orderid: str
    symbol: str
    direction: Direction
    offset: Offset
    price: float
    volume: float


@dataclass
class PositionData:
    symbol: str
    direction: Direction
    volume: float = 0
    price: float = 0
    pnl: float = 0


# ==================== ArrayManager (Technical Indicators) ====================

class ArrayManager:
    """numpy-based technical analysis container, inspired by vnpy's ArrayManager"""

    def __init__(self, size: int = 100):
        self.count = 0
        self.size = size
        self.inited = False

        self.close_arr = np.zeros(size)
        self.open_arr = np.zeros(size)
        self.high_arr = np.zeros(size)
        self.low_arr = np.zeros(size)
        self.volume_arr = np.zeros(size)

    def update_bar(self, bar: BarData):
        self.count += 1
        if not self.inited and self.count >= self.size:
            self.inited = True

        self.close_arr[:-1] = self.close_arr[1:]
        self.open_arr[:-1] = self.open_arr[1:]
        self.high_arr[:-1] = self.high_arr[1:]
        self.low_arr[:-1] = self.low_arr[1:]
        self.volume_arr[:-1] = self.volume_arr[1:]

        self.close_arr[-1] = bar.close_price
        self.open_arr[-1] = bar.open_price
        self.high_arr[-1] = bar.high_price
        self.low_arr[-1] = bar.low_price
        self.volume_arr[-1] = bar.volume

    def sma(self, n: int) -> float:
        """Simple Moving Average"""
        if self.count < n:
            return 0
        return float(np.mean(self.close_arr[-n:]))

    def ema(self, n: int) -> float:
        """Exponential Moving Average"""
        if self.count < n:
            return 0
        alpha = 2 / (n + 1)
        ema_val = self.close_arr[-n]
        for i in range(-n + 1, 0):
            ema_val = alpha * self.close_arr[i] + (1 - alpha) * ema_val
        return float(ema_val)

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD indicator, returns (dif, dea, macd_hist)"""
        if self.count < slow:
            return 0, 0, 0
        ema_fast = self._ema_arr(self.close_arr, fast)
        ema_slow = self._ema_arr(self.close_arr, slow)
        dif = ema_fast - ema_slow
        dea = self._ema_arr(dif, signal)
        macd_hist = 2 * (dif - dea)
        return float(dif[-1]), float(dea[-1]), float(macd_hist[-1])

    def rsi(self, n: int = 14) -> float:
        """Relative Strength Index"""
        if self.count < n + 1:
            return 50
        deltas = np.diff(self.close_arr[-(n + 1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return float(100 - 100 / (1 + rs))

    def atr(self, n: int = 14) -> float:
        """Average True Range"""
        if self.count < n + 1:
            return 0
        high = self.high_arr[-n - 1:]
        low = self.low_arr[-n - 1:]
        close = self.close_arr[-n - 1:]
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        return float(np.mean(tr))

    def boll(self, n: int = 20, dev: float = 2.0):
        """Bollinger Bands, returns (upper, middle, lower)"""
        if self.count < n:
            return 0, 0, 0
        middle = np.mean(self.close_arr[-n:])
        std = np.std(self.close_arr[-n:])
        upper = middle + dev * std
        lower = middle - dev * std
        return float(upper), float(middle), float(lower)

    def keltner(self, n: int = 20, dev: float = 1.5):
        """Keltner Channel, returns (upper, middle, lower)"""
        if self.count < n:
            return 0, 0, 0
        middle = np.mean(self.close_arr[-n:])
        atr_val = self.atr(n)
        upper = middle + dev * atr_val
        lower = middle - dev * atr_val
        return float(upper), float(middle), float(lower)

    def donchian(self, n: int = 20):
        """Donchian Channel, returns (upper, lower)"""
        if self.count < n:
            return 0, 0
        upper = float(np.max(self.high_arr[-n:]))
        lower = float(np.min(self.low_arr[-n:]))
        return upper, lower

    def _ema_arr(self, arr: np.ndarray, n: int) -> np.ndarray:
        alpha = 2 / (n + 1)
        result = np.zeros_like(arr)
        result[0] = arr[0]
        for i in range(1, len(arr)):
            result[i] = alpha * arr[i] + (1 - alpha) * result[i - 1]
        return result


# ==================== CtaTemplate (Strategy Base Class) ====================

class CtaTemplate(ABC):
    """CTA strategy base class, inspired by vnpy's CtaTemplate"""

    author: str = ""
    parameters: List[str] = []
    variables: List[str] = []

    def __init__(self, strategy_name: str = "", symbol: str = ""):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.am = ArrayManager(size=100)
        self.pos: float = 0
        self.inited: bool = False
        self.trading: bool = False
        self._trades: List[Dict] = []

    @abstractmethod
    def on_init(self):
        """Strategy initialization"""
        pass

    @abstractmethod
    def on_bar(self, bar: BarData):
        """Called on each new bar - implement strategy logic here"""
        pass

    def on_start(self):
        self.trading = True

    def on_stop(self):
        self.trading = False

    def buy(self, price: float, volume: float):
        """Buy to open LONG"""
        self.pos += volume
        self._trades.append({
            "direction": "LONG", "offset": "OPEN",
            "price": price, "volume": volume
        })

    def sell(self, price: float, volume: float):
        """Sell to close LONG"""
        self.pos -= volume
        self._trades.append({
            "direction": "LONG", "offset": "CLOSE",
            "price": price, "volume": volume
        })

    def short(self, price: float, volume: float):
        """Sell to open SHORT"""
        self.pos -= volume
        self._trades.append({
            "direction": "SHORT", "offset": "OPEN",
            "price": price, "volume": volume
        })

    def cover(self, price: float, volume: float):
        """Buy to close SHORT"""
        self.pos += volume
        self._trades.append({
            "direction": "SHORT", "offset": "CLOSE",
            "price": price, "volume": volume
        })

    def cancel_all(self):
        pass

    def get_parameters(self) -> Dict[str, Any]:
        return {p: getattr(self, p) for p in self.parameters if hasattr(self, p)}

    def set_parameters(self, params: Dict[str, Any]):
        for k, v in params.items():
            if k in self.parameters and hasattr(self, k):
                setattr(self, k, v)


# ==================== Built-in Strategies ====================

class DoubleMaStrategy(CtaTemplate):
    """Dual Moving Average Crossover Strategy"""
    author = "vnpy"
    parameters = ["fast_window", "slow_window", "fixed_size"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    fast_window = 10
    slow_window = 20
    fixed_size = 1

    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0

    def on_init(self):
        pass

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.fast_ma0 = self.am.sma(self.fast_window)
        self.slow_ma0 = self.am.sma(self.slow_window)

        if self.fast_ma1 > 0 and self.slow_ma1 > 0:
            cross_above = self.fast_ma0 > self.slow_ma0 and self.fast_ma1 <= self.slow_ma1
            cross_below = self.fast_ma0 < self.slow_ma0 and self.fast_ma1 >= self.slow_ma1

            if cross_above:
                if self.pos == 0:
                    self.buy(bar.close_price, self.fixed_size)
                elif self.pos < 0:
                    self.cover(bar.close_price, abs(self.pos))
                    self.buy(bar.close_price, self.fixed_size)
            elif cross_below:
                if self.pos == 0:
                    self.short(bar.close_price, self.fixed_size)
                elif self.pos > 0:
                    self.sell(bar.close_price, abs(self.pos))
                    self.short(bar.close_price, self.fixed_size)

        self.fast_ma1 = self.fast_ma0
        self.slow_ma1 = self.slow_ma0


class AtrRsiStrategy(CtaTemplate):
    """ATR + RSI Strategy with trailing stop"""
    author = "vnpy"
    parameters = ["rsi_window", "atr_window", "atr_multiplier", "rsi_long", "rsi_short", "fixed_size"]
    variables = ["rsi_value", "atr_value", "entry_price", "trailing_stop"]

    rsi_window = 14
    atr_window = 14
    atr_multiplier = 3.0
    rsi_long = 25
    rsi_short = 75
    fixed_size = 1

    rsi_value = 50.0
    atr_value = 0.0
    entry_price = 0.0
    trailing_stop = 0.0

    def on_init(self):
        pass

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.rsi_value = self.am.rsi(self.rsi_window)
        self.atr_value = self.atr(self.atr_window) if hasattr(self, '_atr') else self.am.atr(self.atr_window)

        if self.pos > 0:
            self.trailing_stop = bar.close_price - self.atr_value * self.atr_multiplier
            if bar.low_price <= self.trailing_stop:
                self.sell(bar.close_price, abs(self.pos))
                return

        if self.pos < 0:
            self.trailing_stop = bar.close_price + self.atr_value * self.atr_multiplier
            if bar.high_price >= self.trailing_stop:
                self.cover(bar.close_price, abs(self.pos))
                return

        if self.pos == 0:
            if self.rsi_value < self.rsi_long:
                self.buy(bar.close_price, self.fixed_size)
                self.entry_price = bar.close_price
            elif self.rsi_value > self.rsi_short:
                self.short(bar.close_price, self.fixed_size)
                self.entry_price = bar.close_price

    def atr(self, n):
        return self.am.atr(n)


class BollingerStrategy(CtaTemplate):
    """Bollinger Band Breakout Strategy"""
    author = "vnpy"
    parameters = ["boll_window", "boll_dev", "fixed_size"]
    variables = ["boll_up", "boll_mid", "boll_down"]

    boll_window = 20
    boll_dev = 2.0
    fixed_size = 1

    boll_up = 0.0
    boll_mid = 0.0
    boll_down = 0.0

    def on_init(self):
        pass

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.boll_up, self.boll_mid, self.boll_down = self.am.boll(self.boll_window, self.boll_dev)

        if self.pos == 0:
            if bar.close_price > self.boll_up:
                self.buy(bar.close_price, self.fixed_size)
            elif bar.close_price < self.boll_down:
                self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if bar.close_price < self.boll_mid:
                self.sell(bar.close_price, abs(self.pos))
        elif self.pos < 0:
            if bar.close_price > self.boll_mid:
                self.cover(bar.close_price, abs(self.pos))


class DonchianStrategy(CtaTemplate):
    """Donchian Channel Breakout Strategy"""
    author = "vnpy"
    parameters = ["donchian_window", "fixed_size"]
    variables = ["donchian_up", "donchian_down"]

    donchian_window = 20
    fixed_size = 1

    donchian_up = 0.0
    donchian_down = 0.0

    def on_init(self):
        pass

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.donchian_up, self.donchian_down = self.am.donchian(self.donchian_window)

        if self.pos == 0:
            if bar.close_price >= self.donchian_up:
                self.buy(bar.close_price, self.fixed_size)
            elif bar.close_price <= self.donchian_down:
                self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if bar.close_price <= self.donchian_down:
                self.sell(bar.close_price, abs(self.pos))
        elif self.pos < 0:
            if bar.close_price >= self.donchian_up:
                self.cover(bar.close_price, abs(self.pos))


class KeltnerStrategy(CtaTemplate):
    """Keltner Channel Strategy"""
    author = "vnpy"
    parameters = ["keltner_window", "keltner_dev", "fixed_size"]
    variables = ["keltner_up", "keltner_mid", "keltner_down"]

    keltner_window = 20
    keltner_dev = 1.5
    fixed_size = 1

    keltner_up = 0.0
    keltner_mid = 0.0
    keltner_down = 0.0

    def on_init(self):
        pass

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.keltner_up, self.keltner_mid, self.keltner_down = self.am.keltner(self.keltner_window, self.keltner_dev)

        if self.pos == 0:
            if bar.close_price > self.keltner_up:
                self.buy(bar.close_price, self.fixed_size)
            elif bar.close_price < self.keltner_down:
                self.short(bar.close_price, self.fixed_size)
        elif self.pos > 0:
            if bar.close_price < self.keltner_mid:
                self.sell(bar.close_price, abs(self.pos))
        elif self.pos < 0:
            if bar.close_price > self.keltner_mid:
                self.cover(bar.close_price, abs(self.pos))


# ==================== Strategy Registry ====================

STRATEGY_MAP: Dict[str, Type[CtaTemplate]] = {
    "double_ma": DoubleMaStrategy,
    "atr_rsi": AtrRsiStrategy,
    "bollinger": BollingerStrategy,
    "donchian": DonchianStrategy,
    "keltner": KeltnerStrategy,
}

STRATEGY_INFO = {
    "double_ma": {
        "name": "双均线交叉",
        "description": "经典趋势跟踪：快均线上穿慢均线做多，下穿做空",
        "category": "趋势跟踪",
        "params": [
            {"key": "fast_window", "label": "快均线周期", "default": 10, "min": 3, "max": 50, "desc": "短期均线窗口"},
            {"key": "slow_window", "label": "慢均线周期", "default": 20, "min": 10, "max": 120, "desc": "长期均线窗口"},
            {"key": "fixed_size", "label": "每笔手数", "default": 1, "min": 1, "max": 100, "desc": "每次交易数量"},
        ],
    },
    "atr_rsi": {
        "name": "ATR-RSI",
        "description": "RSI超卖买入+ATR移动止损，适合波动行情",
        "category": "均值回归",
        "params": [
            {"key": "rsi_window", "label": "RSI周期", "default": 14, "min": 5, "max": 30, "desc": "RSI计算窗口"},
            {"key": "atr_window", "label": "ATR周期", "default": 14, "min": 5, "max": 30, "desc": "ATR计算窗口"},
            {"key": "atr_multiplier", "label": "ATR倍数", "default": 3.0, "min": 1.0, "max": 5.0, "desc": "止损距离=ATR×倍数"},
            {"key": "rsi_long", "label": "RSI买入线", "default": 25, "min": 10, "max": 40, "desc": "RSI低于此值买入"},
            {"key": "rsi_short", "label": "RSI卖空线", "default": 75, "min": 60, "max": 90, "desc": "RSI高于此值卖空"},
            {"key": "fixed_size", "label": "每笔手数", "default": 1, "min": 1, "max": 100, "desc": "每次交易数量"},
        ],
    },
    "bollinger": {
        "name": "布林带突破",
        "description": "价格突破上轨做多，突破下轨做空，回归中轨平仓",
        "category": "波动突破",
        "params": [
            {"key": "boll_window", "label": "布林窗口", "default": 20, "min": 10, "max": 60, "desc": "布林带均线窗口"},
            {"key": "boll_dev", "label": "标准差倍数", "default": 2.0, "min": 1.0, "max": 3.0, "desc": "布林带宽度"},
            {"key": "fixed_size", "label": "每笔手数", "default": 1, "min": 1, "max": 100, "desc": "每次交易数量"},
        ],
    },
    "donchian": {
        "name": "唐奇安通道",
        "description": "突破N日最高价做多，突破N日最低价做空（海龟交易法核心）",
        "category": "趋势跟踪",
        "params": [
            {"key": "donchian_window", "label": "通道周期", "default": 20, "min": 5, "max": 60, "desc": "唐奇安通道窗口"},
            {"key": "fixed_size", "label": "每笔手数", "default": 1, "min": 1, "max": 100, "desc": "每次交易数量"},
        ],
    },
    "keltner": {
        "name": "肯特纳通道",
        "description": "基于ATR的通道策略，突破上下轨交易，中轨平仓",
        "category": "波动突破",
        "params": [
            {"key": "keltner_window", "label": "通道周期", "default": 20, "min": 10, "max": 60, "desc": "肯特纳通道窗口"},
            {"key": "keltner_dev", "label": "ATR倍数", "default": 1.5, "min": 0.5, "max": 3.0, "desc": "通道宽度"},
            {"key": "fixed_size", "label": "每笔手数", "default": 1, "min": 1, "max": 100, "desc": "每次交易数量"},
        ],
    },
}


# ==================== BacktestingEngine ====================

class BacktestingEngine:
    """
    vnpy-inspired backtesting engine
    Workflow: set_parameters -> add_strategy -> run_backtesting -> calculate_result -> calculate_statistics
    """

    def __init__(self):
        self.strategy: Optional[CtaTemplate] = None
        self.strategy_name: str = ""
        self.symbol: str = ""
        self.interval: str = "d"
        self.rate: float = 0.3 / 10000  # commission rate
        self.slippage: float = 0.2      # slippage per trade
        self.size: float = 1             # contract multiplier
        self.pricetick: float = 0.01     # minimum price tick
        self.capital: float = 1_000_000

        self.start: datetime = datetime(2020, 1, 1)
        self.end: datetime = datetime(2024, 12, 31)

        self.bars: List[BarData] = []
        self.daily_results: Dict[str, Dict] = {}
        self.trades: List[Dict] = []

    def set_parameters(
        self,
        symbol: str = "000001",
        interval: str = "d",
        start: datetime = None,
        end: datetime = None,
        rate: float = 0.3 / 10000,
        slippage: float = 0.2,
        size: float = 1,
        pricetick: float = 0.01,
        capital: float = 1_000_000,
    ):
        self.symbol = symbol
        self.interval = interval
        self.start = start or datetime(2020, 1, 1)
        self.end = end or datetime(2024, 12, 31)
        self.rate = rate
        self.slippage = slippage
        self.size = size
        self.pricetick = pricetick
        self.capital = capital

    def add_strategy(self, strategy_class: Type[CtaTemplate], params: Dict = None):
        self.strategy_name = strategy_class.__name__
        self.strategy = strategy_class(strategy_name=self.strategy_name, symbol=self.symbol)
        if params:
            self.strategy.set_parameters(params)
        self.strategy.on_init()
        self.strategy.pos = 0

    def load_data(self, df: pd.DataFrame):
        """Load data from DataFrame (columns: date, open, high, low, close, volume)"""
        self.bars = []
        for _, row in df.iterrows():
            bar = BarData(
                symbol=self.symbol,
                datetime=pd.to_datetime(row["date"]),
                open_price=float(row["open"]),
                high_price=float(row["high"]),
                low_price=float(row["low"]),
                close_price=float(row["close"]),
                volume=float(row.get("volume", 1000000)),
            )
            self.bars.append(bar)

    def run_backtesting(self) -> List[Dict]:
        """Run backtesting, return list of trade records"""
        self.trades = []
        self.daily_results = {}
        self.strategy.pos = 0

        prev_pos = 0
        for bar in self.bars:
            prev_pos = self.strategy.pos
            self.strategy.on_bar(bar)

            # record trade if position changed
            if self.strategy.pos != prev_pos:
                trade_volume = abs(self.strategy.pos - prev_pos)
                direction = "LONG" if self.strategy.pos > prev_pos else "SHORT"
                offset = "OPEN" if prev_pos == 0 or abs(self.strategy.pos) > abs(prev_pos) else "CLOSE"

                trade_price = bar.close_price + (self.slippage if direction == "LONG" else -self.slippage)
                commission = trade_price * trade_volume * self.size * self.rate

                trade = {
                    "date": bar.datetime.strftime("%Y-%m-%d"),
                    "datetime": bar.datetime,
                    "direction": direction,
                    "offset": offset,
                    "price": round(trade_price, 4),
                    "volume": trade_volume,
                    "commission": round(commission, 4),
                    "symbol": self.symbol,
                }
                self.trades.append(trade)

            # track daily close and position
            date_str = bar.datetime.strftime("%Y-%m-%d")
            self.daily_results[date_str] = {
                "close": bar.close_price,
                "pos": self.strategy.pos,
            }

        return self.trades

    def calculate_result(self) -> pd.DataFrame:
        """Calculate daily PnL from trades"""
        if not self.bars:
            return pd.DataFrame()

        dates = [bar.datetime.strftime("%Y-%m-%d") for bar in self.bars]
        closes = [bar.close_price for bar in self.bars]

        # build trade cashflow
        cashflow = np.zeros(len(dates))
        trade_map = {}
        for t in self.trades:
            d = t["date"]
            if d not in trade_map:
                trade_map[d] = 0
            sign = 1 if t["direction"] == "LONG" and t["offset"] == "OPEN" else -1
            if t["offset"] == "CLOSE":
                sign = -sign
            trade_map[d] += sign * t["price"] * t["volume"] * self.size

        for i, d in enumerate(dates):
            if d in trade_map:
                cashflow[i] = trade_map[d]

        # build position series
        pos = np.zeros(len(dates))
        current_pos = 0
        for t in self.trades:
            d = t["date"]
            idx = dates.index(d) if d in dates else -1
            if idx >= 0:
                if t["direction"] == "LONG":
                    current_pos += t["volume"] if t["offset"] == "OPEN" else -t["volume"]
                else:
                    current_pos -= t["volume"] if t["offset"] == "OPEN" else -t["volume"]
                pos[idx] = current_pos

        # forward fill position
        for i in range(1, len(pos)):
            if pos[i] == 0:
                pos[i] = pos[i - 1]

        # daily returns
        close_arr = np.array(closes)
        price_change = np.diff(close_arr, prepend=close_arr[0])
        daily_pnl = pos * price_change

        # deduct commissions
        total_commission = sum(t["commission"] for t in self.trades)
        commission_per_day = total_commission / len(dates) if dates else 0
        daily_pnl -= commission_per_day

        result = pd.DataFrame({
            "date": dates,
            "close": closes,
            "pos": pos,
            "daily_pnl": daily_pnl,
        })
        return result

    def calculate_statistics(self, result_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        if result_df is None:
            result_df = self.calculate_result()
        if result_df.empty:
            return {"error": "No data"}

        daily_pnl = result_df["daily_pnl"]
        closes = result_df["close"]

        # equity curve
        equity = self.capital + daily_pnl.cumsum()
        total_days = len(result_df)

        # returns
        total_return = (equity.iloc[-1] / self.capital - 1) * 100
        years = total_days / 252
        annual_return = ((1 + total_return / 100) ** (1 / max(years, 0.01)) - 1) * 100

        # drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max * 100
        max_drawdown = float(drawdown.min())
        max_dd_idx = drawdown.idxmin()
        max_dd_duration = 0
        dd_days = 0
        for dd in drawdown:
            if dd < 0:
                dd_days += 1
                max_dd_duration = max(max_dd_duration, dd_days)
            else:
                dd_days = 0

        # volatility
        daily_returns = daily_pnl / equity.shift(1).fillna(self.capital)
        volatility = float(daily_returns.std() * np.sqrt(252) * 100)

        # sharpe
        sharpe = float(daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0

        # sortino
        downside = daily_returns[daily_returns < 0]
        downside_vol = downside.std() if len(downside) > 0 else daily_returns.std()
        sortino = float(daily_returns.mean() / downside_vol * np.sqrt(252)) if downside_vol > 0 else 0

        # calmar
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # win rate
        winning_days = (daily_pnl > 0).sum()
        win_rate = winning_days / total_days * 100 if total_days > 0 else 0

        # profit/loss ratio
        avg_win = daily_pnl[daily_pnl > 0].mean() if (daily_pnl > 0).any() else 0
        avg_loss = abs(daily_pnl[daily_pnl < 0].mean()) if (daily_pnl < 0).any() else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # trade stats
        total_trades = len(self.trades)
        total_commission = sum(t["commission"] for t in self.trades)

        # best/worst month
        result_df["month"] = pd.to_datetime(result_df["date"]).dt.to_period("M")
        monthly = result_df.groupby("month")["daily_pnl"].sum()
        best_month = float(monthly.max() / self.capital * 100) if len(monthly) > 0 else 0
        worst_month = float(monthly.min() / self.capital * 100) if len(monthly) > 0 else 0

        equity_curve = [
            {"date": d, "value": round(float(v), 2)}
            for d, v in zip(result_df["date"], equity.values)
        ]

        return {
            "total_return": round(total_return, 2),
            "annual_return": round(annual_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_duration": max_dd_duration,
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "win_rate": round(win_rate, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
            "total_trades": total_trades,
            "total_commission": round(total_commission, 2),
            "best_month": round(best_month, 2),
            "worst_month": round(worst_month, 2),
            "end_balance": round(float(equity.iloc[-1]), 2),
            "total_days": total_days,
            "profit_days": int(winning_days),
            "loss_days": int(total_days - winning_days),
            "equity_curve": equity_curve,
            "trades": self.trades,
        }


# ==================== Parameter Optimization ====================

def optimize_strategy(
    strategy_class: Type[CtaTemplate],
    df: pd.DataFrame,
    param_grid: Dict[str, List],
    target: str = "sharpe_ratio",
    symbol: str = "000001",
) -> List[Dict]:
    """
    Grid search parameter optimization
    Returns sorted list of (params, metric) by target metric
    """
    import itertools

    keys = list(param_grid.keys())
    values = list(param_grid.values())
    results = []

    for combo in itertools.product(*values):
        params = dict(zip(keys, combo))

        engine = BacktestingEngine()
        engine.set_parameters(symbol=symbol)
        engine.add_strategy(strategy_class, params)
        engine.load_data(df)
        engine.run_backtesting()
        result_df = engine.calculate_result()
        stats = engine.calculate_statistics(result_df)

        results.append({
            "params": params,
            "metrics": stats,
        })

    results.sort(key=lambda x: x["metrics"].get(target, 0), reverse=True)
    return results[:20]
