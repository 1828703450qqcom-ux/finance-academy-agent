import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from services.akshare_service import get_stock_history, get_stock_list


def run_vnpy_strategy(
    stock_pool: str, start_date: str, end_date: str, initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    """vnpy-based strategy runner using BacktestingEngine"""
    from services.vnpy_engine import (
        BacktestingEngine, STRATEGY_MAP as VNPY_STRATEGY_MAP, STRATEGY_INFO
    )

    params = params or {}
    strategy_type = params.pop("_strategy_type", "double_ma")

    stocks = get_stock_list(stock_pool)
    symbol = stocks[0] if stocks else "000001"

    df = get_stock_history(symbol, start_date, end_date)
    if df is None or len(df) < 30:
        return _generate_synthetic_result(initial_capital, strategy_type)

    # rename columns to match vnpy engine expectations
    df = df.rename(columns={"日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close", "成交量": "volume"})
    df = df[["date", "open", "high", "low", "close", "volume"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # filter date range
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)].reset_index(drop=True)

    strategy_class = VNPY_STRATEGY_MAP.get(strategy_type)
    if not strategy_class:
        return _generate_synthetic_result(initial_capital, strategy_type)

    engine = BacktestingEngine()
    engine.set_parameters(
        symbol=symbol,
        capital=initial_capital,
    )

    strategy_params = {}
    info = STRATEGY_INFO.get(strategy_type, {})
    for p in info.get("params", []):
        k = p["key"]
        if k in params:
            strategy_params[k] = params[k]
        else:
            strategy_params[k] = p["default"]

    engine.add_strategy(strategy_class, strategy_params)
    engine.load_data(df)
    trades = engine.run_backtesting()
    result_df = engine.calculate_result()
    stats = engine.calculate_statistics(result_df)

    if "error" in stats:
        return _generate_synthetic_result(initial_capital, strategy_type)

    return {**stats, "synthetic": False}


def _calculate_metrics(daily_returns: pd.Series, equity: pd.Series, benchmark_returns: pd.Series = None) -> Dict[str, Any]:
    """计算专业绩效指标"""
    total_days = len(daily_returns)
    annual_factor = 252

    total_return = (equity.iloc[-1] / equity.iloc[0] - 1) if len(equity) > 0 else 0
    years = total_days / annual_factor
    annual_return = (1 + total_return) ** (1 / max(years, 0.01)) - 1

    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min()) if len(drawdown) > 0 else 0

    # 最大回撤持续时间
    dd_duration = 0
    if len(drawdown) > 0:
        in_dd = False
        max_dd_days = 0
        current_dd_days = 0
        for dd in drawdown:
            if dd < 0:
                current_dd_days += 1
                max_dd_days = max(max_dd_days, current_dd_days)
            else:
                current_dd_days = 0
        dd_duration = max_dd_days

    volatility = daily_returns.std()
    downside_returns = daily_returns[daily_returns < 0]
    downside_vol = downside_returns.std() if len(downside_returns) > 0 else volatility

    # Sharpe
    sharpe = (daily_returns.mean() / volatility * np.sqrt(annual_factor)) if volatility > 0 else 0

    # Sortino
    sortino = (daily_returns.mean() / downside_vol * np.sqrt(annual_factor)) if downside_vol > 0 else 0

    # Calmar
    calmar = (annual_return / abs(max_drawdown)) if max_drawdown != 0 else 0

    # 信息比率（如果有基准）
    information_ratio = 0
    if benchmark_returns is not None and len(benchmark_returns) > 0:
        excess = daily_returns.values[:len(benchmark_returns)] - benchmark_returns.values[:len(daily_returns)]
        tracking_error = np.std(excess) * np.sqrt(annual_factor)
        information_ratio = (np.mean(excess) * annual_factor / tracking_error) if tracking_error > 0 else 0

    # 胜率
    win_rate = (daily_returns > 0).sum() / total_days * 100 if total_days > 0 else 0

    # 盈亏比
    avg_win = daily_returns[daily_returns > 0].mean() if (daily_returns > 0).any() else 0
    avg_loss = abs(daily_returns[daily_returns < 0].mean()) if (daily_returns < 0).any() else 1
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    # 月度统计
    monthly_returns = daily_returns.resample('ME').apply(lambda x: (1 + x).prod() - 1) if hasattr(daily_returns.index, 'freq') else daily_returns
    best_month = float(monthly_returns.max() * 100) if len(monthly_returns) > 0 else 0
    worst_month = float(monthly_returns.min() * 100) if len(monthly_returns) > 0 else 0

    # 基准对比
    benchmark_metrics = {}
    if benchmark_returns is not None and len(benchmark_returns) > 0:
        bm_equity = (1 + benchmark_returns).cumprod()
        bm_total_return = bm_equity.iloc[-1] - 1
        bm_annual_return = (1 + bm_total_return) ** (1 / max(years, 0.01)) - 1
        bm_volatility = benchmark_returns.std()
        bm_sharpe = (benchmark_returns.mean() / bm_volatility * np.sqrt(annual_factor)) if bm_volatility > 0 else 0
        benchmark_metrics = {
            "bm_annual_return": round(float(bm_annual_return * 100), 2),
            "bm_sharpe": round(float(bm_sharpe), 2),
            "excess_return": round(float((annual_return - bm_annual_return) * 100), 2),
            "bm_max_drawdown": round(float(((bm_equity - bm_equity.cummax()) / bm_equity.cummax()).min() * 100), 2),
        }

    return {
        "annual_return": round(float(annual_return * 100), 2),
        "max_drawdown": round(float(max_drawdown * 100), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "sortino_ratio": round(float(sortino), 2),
        "calmar_ratio": round(float(calmar), 2),
        "information_ratio": round(float(information_ratio), 2),
        "volatility": round(float(volatility * np.sqrt(annual_factor) * 100), 2),
        "win_rate": round(float(win_rate), 2),
        "profit_loss_ratio": round(float(profit_loss_ratio), 2),
        "trade_count": total_days,
        "max_drawdown_days": dd_duration,
        "best_month": round(float(best_month), 2),
        "worst_month": round(float(worst_month), 2),
        "total_return": round(float(total_return * 100), 2),
        **benchmark_metrics,
    }


def _generate_benchmark(dates, initial_capital=1000000):
    """生成基准指数（沪深300模拟）"""
    np.random.seed(100)
    returns = np.random.normal(0.0003, 0.012, len(dates))
    return pd.Series(returns, index=dates)


# ==================== 策略实现 ====================

def run_momentum_strategy(
    stock_pool: str, start_date: str, end_date: str, initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    """动量策略：买入过去N日涨幅最大的股票"""
    params = params or {}
    lookback = params.get("lookback", 20)
    top_n = params.get("top_n", 5)

    stocks = get_stock_list(stock_pool)
    all_data = {}
    for symbol in stocks[:15]:
        df = get_stock_history(symbol, start_date, end_date)
        if df is not None and len(df) > lookback + 10:
            df["returns"] = df["收盘"].pct_change()
            df["momentum"] = df["收盘"].pct_change(lookback)
            all_data[symbol] = df

    if not all_data:
        return _generate_synthetic_result(initial_capital, "momentum")

    # 按日期合并
    dates = sorted(set.intersection(*[set(d["日期"].tolist()) for d in all_data.values()]))
    portfolio_returns = []

    for date in dates:
        rankings = []
        for sym, df in all_data.items():
            row = df[df["日期"] == date]
            if len(row) > 0 and not pd.isna(row["momentum"].iloc[0]):
                rankings.append((sym, row["momentum"].iloc[0], row["returns"].iloc[0]))
        rankings.sort(key=lambda x: x[1], reverse=True)
        selected = rankings[:top_n]
        if selected:
            day_return = np.mean([r[2] for r in selected])
            portfolio_returns.append({"date": date, "return": day_return})

    if not portfolio_returns:
        return _generate_synthetic_result(initial_capital, "momentum")

    ret_series = pd.Series(
        [r["return"] for r in portfolio_returns],
        index=pd.to_datetime([r["date"] for r in portfolio_returns]),
    )
    equity = initial_capital * (1 + ret_series).cumprod()
    benchmark = _generate_benchmark(ret_series.index)
    metrics = _calculate_metrics(ret_series, equity, benchmark)

    equity_curve = [{"date": str(d.date()), "value": round(float(v), 2)} for d, v in zip(equity.index, equity.values)]
    return {"equity_curve": equity_curve, **metrics}


def run_mean_reversion_strategy(
    stock_pool: str, start_date: str, end_date: str, initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    """均值回归策略：价格偏离均线时反向操作"""
    params = params or {}
    ma_window = params.get("ma_window", 20)
    entry_std = params.get("entry_std", 2.0)

    stocks = get_stock_list(stock_pool)
    all_data = {}
    for symbol in stocks[:15]:
        df = get_stock_history(symbol, start_date, end_date)
        if df is not None and len(df) > ma_window + 10:
            df["returns"] = df["收盘"].pct_change()
            df["ma"] = df["收盘"].rolling(ma_window).mean()
            df["std"] = df["收盘"].rolling(ma_window).std()
            df["zscore"] = (df["收盘"] - df["ma"]) / df["std"]
            all_data[symbol] = df

    if not all_data:
        return _generate_synthetic_result(initial_capital, "mean_reversion")

    dates = sorted(set.intersection(*[set(d["日期"].tolist()) for d in all_data.values()]))
    portfolio_returns = []

    for date in dates:
        signals = []
        for sym, df in all_data.items():
            row = df[df["日期"] == date]
            if len(row) > 0 and not pd.isna(row["zscore"].iloc[0]):
                z = row["zscore"].iloc[0]
                ret = row["returns"].iloc[0]
                if z < -entry_std:
                    signals.append(ret)  # 买入
                elif z > entry_std:
                    signals.append(-ret)  # 卖出
                # z在中间不动
        if signals:
            portfolio_returns.append({"date": date, "return": np.mean(signals)})

    if not portfolio_returns:
        return _generate_synthetic_result(initial_capital, "mean_reversion")

    ret_series = pd.Series(
        [r["return"] for r in portfolio_returns],
        index=pd.to_datetime([r["date"] for r in portfolio_returns]),
    )
    equity = initial_capital * (1 + ret_series).cumprod()
    benchmark = _generate_benchmark(ret_series.index)
    metrics = _calculate_metrics(ret_series, equity, benchmark)

    equity_curve = [{"date": str(d.date()), "value": round(float(v), 2)} for d, v in zip(equity.index, equity.values)]
    return {"equity_curve": equity_curve, **metrics}


def run_multi_factor_strategy(
    stock_pool: str, start_date: str, end_date: str, initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    """多因子策略：综合价值、动量、质量因子"""
    params = params or {}
    lookback = params.get("lookback", 20)
    top_n = params.get("top_n", 5)

    stocks = get_stock_list(stock_pool)
    all_data = {}
    for symbol in stocks[:15]:
        df = get_stock_history(symbol, start_date, end_date)
        if df is not None and len(df) > lookback + 30:
            df["returns"] = df["收盘"].pct_change()
            df["momentum"] = df["收盘"].pct_change(lookback)
            df["volatility"] = df["returns"].rolling(20).std()
            df["ma_ratio"] = df["收盘"] / df["收盘"].rolling(lookback).mean() - 1
            # 综合因子得分
            df["factor_score"] = (
                df["momentum"].rank(pct=True) * 0.4 +
                (-df["volatility"].rank(pct=True)) * 0.3 +
                df["ma_ratio"].rank(pct=True) * 0.3
            )
            all_data[symbol] = df

    if not all_data:
        return _generate_synthetic_result(initial_capital, "multi_factor")

    dates = sorted(set.intersection(*[set(d["日期"].tolist()) for d in all_data.values()]))
    portfolio_returns = []

    for date in dates:
        rankings = []
        for sym, df in all_data.items():
            row = df[df["日期"] == date]
            if len(row) > 0 and not pd.isna(row["factor_score"].iloc[0]):
                rankings.append((sym, row["factor_score"].iloc[0], row["returns"].iloc[0]))
        rankings.sort(key=lambda x: x[1], reverse=True)
        selected = rankings[:top_n]
        if selected:
            day_return = np.mean([r[2] for r in selected])
            portfolio_returns.append({"date": date, "return": day_return})

    if not portfolio_returns:
        return _generate_synthetic_result(initial_capital, "multi_factor")

    ret_series = pd.Series(
        [r["return"] for r in portfolio_returns],
        index=pd.to_datetime([r["date"] for r in portfolio_returns]),
    )
    equity = initial_capital * (1 + ret_series).cumprod()
    benchmark = _generate_benchmark(ret_series.index)
    metrics = _calculate_metrics(ret_series, equity, benchmark)

    equity_curve = [{"date": str(d.date()), "value": round(float(v), 2)} for d, v in zip(equity.index, equity.values)]
    return {"equity_curve": equity_curve, **metrics}


def run_pair_trading_strategy(
    stock_pool: str, start_date: str, end_date: str, initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    """配对交易策略：利用相关性高的股票价差回归"""
    params = params or {}
    lookback = params.get("lookback", 60)
    entry_threshold = params.get("entry_threshold", 2.0)

    stocks = get_stock_list(stock_pool)
    all_data = {}
    for symbol in stocks[:10]:
        df = get_stock_history(symbol, start_date, end_date)
        if df is not None and len(df) > lookback + 10:
            df["returns"] = df["收盘"].pct_change()
            all_data[symbol] = df

    if len(all_data) < 2:
        return _generate_synthetic_result(initial_capital, "pair_trading")

    # 找最相关的配对
    symbols = list(all_data.keys())[:6]
    best_corr = -1
    best_pair = (symbols[0], symbols[1])
    for i in range(len(symbols)):
        for j in range(i+1, len(symbols)):
            df1 = all_data[symbols[i]]
            df2 = all_data[symbols[j]]
            common_dates = set(df1["日期"]) & set(df2["日期"])
            if len(common_dates) > 60:
                r1 = df1[df1["日期"].isin(common_dates)].set_index("日期")["收盘"]
                r2 = df2[df2["日期"].isin(common_dates)].set_index("日期")["收盘"]
                corr = r1.corr(r2)
                if corr > best_corr:
                    best_corr = corr
                    best_pair = (symbols[i], symbols[j])

    df1 = all_data[best_pair[0]].copy()
    df2 = all_data[best_pair[1]].copy()
    df1 = df1.set_index("日期")
    df2 = df2.set_index("日期")
    common = sorted(set(df1.index) & set(df2.index))
    df1 = df1.loc[common]
    df2 = df2.loc[common]

    # 价差
    spread = np.log(df1["收盘"]) - np.log(df2["收盘"])
    spread_ma = spread.rolling(lookback).mean()
    spread_std = spread.rolling(lookback).std()
    zscore = (spread - spread_ma) / spread_std

    signals = pd.Series(0, index=common)
    signals[zscore < -entry_threshold] = 1   # 价差低，做多spread
    signals[zscore > entry_threshold] = -1   # 价差高，做空spread

    ret1 = df1["收盘"].pct_change()
    ret2 = df2["收盘"].pct_change()
    strategy_returns = signals.shift(1) * (ret1 - ret2) / 2

    strategy_returns = strategy_returns.dropna()
    ret_series = strategy_returns.iloc[-len(common):]
    if len(ret_series) < 10:
        return _generate_synthetic_result(initial_capital, "pair_trading")

    equity = initial_capital * (1 + ret_series).cumprod()
    benchmark = _generate_benchmark(ret_series.index)
    metrics = _calculate_metrics(ret_series, equity, benchmark)

    equity_curve = [{"date": str(d.date()), "value": round(float(v), 2)} for d, v in zip(equity.index, equity.values)]
    return {"equity_curve": equity_curve, "pair": list(best_pair), "correlation": round(best_corr, 4), **metrics}


def _generate_synthetic_result(initial_capital: float, strategy_name: str = "") -> Dict[str, Any]:
    """生成合成结果（仅在无法获取真实数据时使用）"""
    np.random.seed(42)
    dates = pd.date_range("2019-01-01", "2024-12-31", freq="B")
    if strategy_name == "momentum":
        returns = np.random.normal(0.0006, 0.014, len(dates))
    elif strategy_name == "mean_reversion":
        returns = np.random.normal(0.0004, 0.011, len(dates))
    elif strategy_name == "multi_factor":
        returns = np.random.normal(0.0007, 0.013, len(dates))
    else:
        returns = np.random.normal(0.0005, 0.015, len(dates))

    equity = initial_capital * np.cumprod(1 + returns)
    equity_series = pd.Series(equity, index=dates)
    ret_series = pd.Series(returns, index=dates)
    benchmark = _generate_benchmark(dates)
    metrics = _calculate_metrics(ret_series, equity_series, benchmark)

    equity_curve = [
        {"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
        for d, v in zip(dates, equity)
    ]
    return {"equity_curve": equity_curve, "synthetic": True, **metrics}


STRATEGY_MAP = {
    "momentum": run_momentum_strategy,
    "mean_reversion": run_mean_reversion_strategy,
    "multi_factor": run_multi_factor_strategy,
    "pair_trading": run_pair_trading_strategy,
    # vnpy-based strategies
    "double_ma": run_vnpy_strategy,
    "atr_rsi": run_vnpy_strategy,
    "bollinger": run_vnpy_strategy,
    "donchian": run_vnpy_strategy,
    "keltner": run_vnpy_strategy,
}


def run_backtest(
    strategy_type: str,
    stock_pool: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 1000000,
    params: Dict = None,
) -> Dict[str, Any]:
    func = STRATEGY_MAP.get(strategy_type, run_momentum_strategy)
    return func(stock_pool, start_date, end_date, initial_capital, params)
