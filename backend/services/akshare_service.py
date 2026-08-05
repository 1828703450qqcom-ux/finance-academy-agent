import akshare as ak
import pandas as pd
import requests as _requests
from typing import Optional, List, Dict, Any


def get_realtime_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """获取个股实时行情（腾讯数据源，服务器可用）"""
    try:
        prefix = "sh" if symbol.startswith("6") else "sz"
        url = f"http://qt.gtimg.cn/q={prefix}{symbol}"
        r = _requests.get(url, timeout=5)
        text = r.text.strip()
        if not text or '=""' in text:
            return None
        # 解析腾讯行情数据
        parts = text.split("~")
        if len(parts) < 50:
            return None
        return {
            "name": parts[1],
            "code": parts[2],
            "price": float(parts[3]) if parts[3] else None,
            "yesterday_close": float(parts[4]) if parts[4] else None,
            "open": float(parts[5]) if parts[5] else None,
            "volume": int(parts[6]) if parts[6] else None,
            "buy_volume": int(parts[7]) if parts[7] else None,
            "sell_volume": int(parts[8]) if parts[8] else None,
            "high": float(parts[33]) if parts[33] else None,
            "low": float(parts[34]) if parts[34] else None,
            "change": float(parts[31]) if parts[31] else None,
            "change_pct": float(parts[32]) if parts[32] else None,
            "turnover": float(parts[38]) if parts[38] else None,
            "pe_ratio": float(parts[39]) if parts[39] else None,
            "amplitude": float(parts[43]) if parts[43] else None,
            "circulating_market_cap": float(parts[44]) if parts[44] else None,
            "total_market_cap": float(parts[45]) if parts[45] else None,
            "pb_ratio": float(parts[46]) if parts[46] else None,
            "timestamp": parts[30] if len(parts) > 30 else "",
        }
    except Exception:
        return None


def get_macro_overview() -> Dict[str, Any]:
    import pandas as pd
    overview = {}

    # 上证指数（实时 via 腾讯）
    try:
        url = "http://qt.gtimg.cn/q=sh000001"
        r = _requests.get(url, timeout=5)
        parts = r.text.split("~")
        if len(parts) > 35:
            overview["shanghai_index"] = float(parts[3])
            overview["shanghai_change"] = float(parts[32])
        else:
            raise ValueError("parse error")
    except Exception:
        try:
            df = ak.stock_zh_index_daily(symbol="sh000001")
            if len(df) > 0:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                overview["shanghai_index"] = round(float(latest["close"]), 2)
                overview["shanghai_change"] = round(
                    (float(latest["close"]) - float(prev["close"])) / float(prev["close"]) * 100, 2
                )
        except Exception:
            overview["shanghai_index"] = 0
            overview["shanghai_change"] = 0

    # CPI（取最新有效值）
    try:
        df = ak.macro_china_cpi_monthly()
        if len(df) > 0:
            # 数据按时间降序排列，取第一个非nan值
            for i in range(len(df) - 1, -1, -1):
                val = pd.to_numeric(df.iloc[i].get("今值"), errors="coerce")
                if not pd.isna(val):
                    overview["cpi"] = round(float(val), 2)
                    overview["cpi_period"] = str(df.iloc[i].get("日期", ""))
                    break
            if "cpi" not in overview:
                overview["cpi"] = 0
    except Exception:
        overview["cpi"] = 0

    # PMI（取最新有效值）
    try:
        df = ak.macro_china_pmi()
        if len(df) > 0:
            # 按月份列排序找最新
            df_sorted = df.sort_values("月份", ascending=False)
            for _, row in df_sorted.iterrows():
                val = pd.to_numeric(row.get("制造业-指数"), errors="coerce")
                if not pd.isna(val):
                    overview["pmi"] = round(float(val), 2)
                    overview["pmi_period"] = str(row.get("月份", ""))
                    break
    except Exception:
        overview["pmi"] = 0

    # GDP（取最新有效值）
    try:
        df = ak.macro_china_gdp()
        if len(df) > 0:
            df_sorted = df.sort_values("季度", ascending=False)
            for _, row in df_sorted.iterrows():
                val = pd.to_numeric(row.get("国内生产总值-同比增长"), errors="coerce")
                if not pd.isna(val):
                    overview["gdp_growth"] = round(float(val), 2)
                    overview["gdp_period"] = str(row.get("季度", ""))
                    break
    except Exception:
        overview["gdp_growth"] = 0

    # M2（取最新有效值）
    try:
        df = ak.macro_china_money_supply()
        if len(df) > 0:
            df_sorted = df.sort_values("月份", ascending=False)
            for _, row in df_sorted.iterrows():
                val = pd.to_numeric(row.get("货币和准货币(M2)-同比增长"), errors="coerce")
                if not pd.isna(val):
                    overview["m2_growth"] = round(float(val), 2)
                    overview["m2_period"] = str(row.get("月份", ""))
                    break
    except Exception:
        overview["m2_growth"] = 0

    # LPR（直接爬取央行最新数据）
    try:
        df = ak.rate_interbank(market="中国", symbol="LPR", indicator="1年")
        if df is not None and len(df) > 0:
            for i in range(len(df) - 1, -1, -1):
                val = pd.to_numeric(df.iloc[i].get("利率"), errors="coerce")
                if not pd.isna(val) and val > 0:
                    overview["lpr"] = round(float(val), 2)
                    break
    except Exception:
        pass
    if "lpr" not in overview:
        overview["lpr"] = 0

    return overview


def get_chart_data(indicator: str) -> Dict[str, Any]:
    import pandas as pd
    try:
        if indicator == "shanghai":
            df = ak.stock_zh_index_daily(symbol="sh000001")
            df = df.tail(120)
            return {
                "dates": df["date"].astype(str).tolist(),
                "values": df["close"].astype(float).tolist(),
                "indicator": "上证指数",
            }
        elif indicator == "cpi":
            df = ak.macro_china_cpi_monthly()
            # 取最新24条有效数据
            valid = df[df["今值"].apply(lambda x: pd.notna(pd.to_numeric(x, errors="coerce")))]
            valid = valid.tail(24)
            return {
                "dates": valid["日期"].astype(str).tolist(),
                "values": pd.to_numeric(valid["今值"], errors="coerce").tolist(),
                "indicator": "CPI当月同比",
            }
        elif indicator == "pmi":
            df = ak.macro_china_pmi()
            df = df.sort_values("月份", ascending=False).head(24).sort_values("月份")
            return {
                "dates": df["月份"].astype(str).tolist(),
                "values": pd.to_numeric(df["制造业-指数"], errors="coerce").tolist(),
                "indicator": "PMI",
            }
        elif indicator == "m2":
            df = ak.macro_china_money_supply()
            df = df.sort_values("月份", ascending=False).head(24).sort_values("月份")
            return {
                "dates": df["月份"].astype(str).tolist(),
                "values": pd.to_numeric(df["货币和准货币(M2)-同比增长"], errors="coerce").tolist(),
                "indicator": "M2同比增速",
            }
        else:
            return {"dates": [], "values": [], "indicator": indicator}
    except Exception as e:
        fallback = _get_fallback_chart(indicator)
        if fallback:
            return fallback
        return {"dates": [], "values": [], "indicator": indicator, "error": str(e)}


def _get_fallback_chart(indicator: str) -> Optional[Dict[str, Any]]:
    """当AKShare失败时返回备用数据"""
    if indicator == "shanghai":
        import numpy as np
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=60, freq="B").strftime("%Y-%m-%d").tolist()
        base = 3200
        values = [round(base + np.cumsum(np.random.randn(60) * 10)[i], 2) for i in range(60)]
        return {"dates": dates, "values": values, "indicator": "上证指数", "note": "备用数据"}
    elif indicator == "cpi":
        return {
            "dates": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"],
            "values": [0.5, 0.7, 0.1, -0.1, 0.2],
            "indicator": "CPI当月同比", "note": "备用数据",
        }
    elif indicator == "pmi":
        return {
            "dates": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"],
            "values": [49.1, 50.2, 50.5, 50.1, 49.8],
            "indicator": "PMI", "note": "备用数据",
        }
    elif indicator == "m2":
        return {
            "dates": ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05"],
            "values": [7.0, 7.2, 7.1, 7.3, 7.4],
            "indicator": "M2同比增速", "note": "备用数据",
        }
    return None


def get_stock_list(pool: str = "hs300") -> List[str]:
    try:
        if pool == "hs300":
            df = ak.index_stock_cons(symbol="000300")
            return df["品种代码"].tolist()[:50]
        elif pool == "zz500":
            df = ak.index_stock_cons(symbol="000905")
            return df["品种代码"].tolist()[:50]
        elif pool == "sz50":
            df = ak.index_stock_cons(symbol="000016")
            return df["品种代码"].tolist()[:30]
    except Exception:
        pass
    return ["600519", "000858", "601318", "600036", "000333"]


def get_stock_history(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    import time as _time
    # 主数据源：网易 stock_zh_a_daily（稳定且数据最新）
    try:
        prefix = "sh" if symbol.startswith("6") else "sz"
        df = ak.stock_zh_a_daily(symbol=f"{prefix}{symbol}", adjust="qfq")
        if df is not None and len(df) > 0:
            df["date"] = pd.to_datetime(df["date"])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
            if len(df) > 0:
                df = df.rename(columns={"date": "日期", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量", "amount": "成交额"})
                return df
    except Exception:
        pass

    # 备用数据源：东方财富 stock_zh_a_hist（不稳定，带重试）
    for attempt in range(2):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if df is not None and len(df) > 0:
                return df
        except Exception:
            if attempt < 1:
                _time.sleep(1)
            continue

    return None
