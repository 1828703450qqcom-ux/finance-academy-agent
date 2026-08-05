import json
import pandas as pd
from fastapi import APIRouter
from schemas import QuantRequest
from services.quant_service import run_backtest
from database import SessionLocal, BacktestResult

router = APIRouter(prefix="/api/quant", tags=["quant"])


@router.get("/strategies/vnpy")
async def list_vnpy_strategies():
    """List all vnpy-based strategies with their parameters"""
    from services.vnpy_engine import STRATEGY_INFO
    return {"strategies": STRATEGY_INFO}


@router.post("/optimize")
async def optimize_strategy(req: QuantRequest):
    """Run parameter optimization using grid search"""
    import asyncio

    def _run():
        from services.vnpy_engine import optimize_strategy, STRATEGY_MAP, STRATEGY_INFO
        from services.akshare_service import get_stock_history, get_stock_list

        strategy_type = (req.params or {}).get("_strategy_type", "double_ma")
        strategy_class = STRATEGY_MAP.get(strategy_type)
        if not strategy_class:
            return {"error": f"不支持的策略: {strategy_type}"}

        info = STRATEGY_INFO.get(strategy_type, {})
        param_grid = {}
        for p in info.get("params", []):
            k = p["key"]
            if k == "fixed_size":
                continue
            step = 5 if isinstance(p["default"], int) and p["default"] > 10 else 1
            if isinstance(p["default"], float):
                step = 0.5
            param_grid[k] = list(range(int(p["min"]), int(p["max"]) + 1, step)) if isinstance(p["default"], int) else \
                [p["min"] + i * step for i in range(int((p["max"] - p["min"]) / step) + 1)]

        stocks = get_stock_list(req.stock_pool)
        symbol = stocks[0] if stocks else "000001"
        df = get_stock_history(symbol, req.start_date, req.end_date)
        if df is None or len(df) < 30:
            return {"error": "数据不足，无法优化"}

        df = df.rename(columns={"日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close", "成交量": "volume"})
        df = df[["date", "open", "high", "low", "close", "volume"]].copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        results = optimize_strategy(
            strategy_class, df, param_grid,
            target="sharpe_ratio", symbol=symbol,
        )
        return {"results": results, "target": "sharpe_ratio"}

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)


@router.post("/backtest")
async def run_quant_backtest(req: QuantRequest):
    import asyncio

    def _run():
        params = req.params or {}
        result = run_backtest(
            strategy_type=req.strategy_type,
            stock_pool=req.stock_pool,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            params=params,
        )
        db = SessionLocal()
        try:
            record = BacktestResult(
                strategy_type=req.strategy_type,
                stock_pool=req.stock_pool,
                start_date=req.start_date,
                end_date=req.end_date,
                metrics=json.dumps({k: v for k, v in result.items() if k != "equity_curve"}),
                equity_curve=json.dumps(result.get("equity_curve", [])),
            )
            db.add(record)
            db.commit()
        finally:
            db.close()
        return result

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)


@router.get("/strategies")
async def list_strategies():
    return {
        "strategies": [
            {"key": "momentum", "name": "动量策略", "description": "追逐趋势，买入过去N日涨幅最大的股票", "category": "趋势跟踪"},
            {"key": "mean_reversion", "name": "均值回归", "description": "价格偏离均线超过N个标准差时反向操作", "category": "统计套利"},
            {"key": "multi_factor", "name": "多因子策略", "description": "综合动量+波动率+均线偏移多因子打分", "category": "因子投资"},
            {"key": "pair_trading", "name": "配对交易", "description": "利用相关性高的股票价差回归获利", "category": "统计套利"},
        ],
        "pools": [
            {"key": "hs300", "name": "沪深300", "count": 300},
            {"key": "zz500", "name": "中证500", "count": 500},
            {"key": "sz50", "name": "上证50", "count": 50},
        ],
        "risk_metrics": [
            {"key": "sharpe_ratio", "name": "Sharpe比率", "desc": "每单位风险的超额收益"},
            {"key": "sortino_ratio", "name": "Sortino比率", "desc": "只考虑下行风险的收益风险比"},
            {"key": "calmar_ratio", "name": "Calmar比率", "desc": "年化收益/最大回撤"},
            {"key": "information_ratio", "name": "信息比率", "desc": "超额收益/跟踪误差"},
            {"key": "win_rate", "name": "胜率", "desc": "正收益天数占比"},
            {"key": "profit_loss_ratio", "name": "盈亏比", "desc": "平均盈利/平均亏损"},
            {"key": "max_drawdown_days", "name": "最大回撤持续天数", "desc": "最长亏损期"},
        ],
    }


@router.get("/history")
async def backtest_history():
    db = SessionLocal()
    try:
        records = db.query(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(20).all()
        return {
            "results": [
                {
                    "id": r.id,
                    "strategy_type": r.strategy_type,
                    "stock_pool": r.stock_pool,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in records
            ]
        }
    finally:
        db.close()
