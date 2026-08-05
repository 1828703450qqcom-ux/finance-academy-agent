"""
股票与财务数据爬虫
数据源：巨潮资讯、东方财富、同花顺
"""
import requests
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class StockCrawler:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://finance.eastmoney.com/",
    }
    TIMEOUT = 15

    # ==================== 东方财富 - 实时行情 ====================

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取个股实时行情"""
        try:
            # 判断市场代码
            if symbol.startswith("6"):
                secid = f"1.{symbol}"
            else:
                secid = f"0.{symbol}"

            url = "https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f167,f170,f171,f173",
                "ut": "fa5fd1943c7b386f172d6893dbbd4847",
            }
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                if data:
                    return {
                        "symbol": data.get("f57", symbol),
                        "name": data.get("f58", ""),
                        "price": data.get("f43", 0) / 100 if data.get("f43") else 0,
                        "change_pct": data.get("f170", 0) / 100 if data.get("f170") else 0,
                        "high": data.get("f44", 0) / 100 if data.get("f44") else 0,
                        "low": data.get("f45", 0) / 100 if data.get("f45") else 0,
                        "open": data.get("f46", 0) / 100 if data.get("f46") else 0,
                        "volume": data.get("f47", 0),
                        "amount": data.get("f48", 0),
                        "pe_ratio": data.get("f162", 0) / 100 if data.get("f162") else 0,
                        "pb_ratio": data.get("f167", 0) / 100 if data.get("f167") else 0,
                        "market_cap": data.get("f116", 0),
                        "circulating_cap": data.get("f117", 0),
                        "source": "东方财富",
                    }
        except Exception:
            pass
        return {"symbol": symbol, "error": "获取失败"}

    def get_stock_history(self, symbol: str, period: str = "daily", limit: int = 120) -> List[Dict]:
        """获取历史K线数据"""
        try:
            if symbol.startswith("6"):
                secid = f"1.{symbol}"
            else:
                secid = f"0.{symbol}"

            klt_map = {"daily": "101", "weekly": "102", "monthly": "103"}
            url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid,
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57",
                "klt": klt_map.get(period, "101"),
                "fqt": "1",
                "end": "20500101",
                "lmt": str(limit),
                "ut": "fa5fd1943c7b386f172d6893dbbd4847",
            }
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                klines = data.get("klines", [])
                results = []
                for kline in klines:
                    parts = kline.split(",")
                    if len(parts) >= 7:
                        results.append({
                            "date": parts[0],
                            "open": float(parts[1]),
                            "close": float(parts[2]),
                            "high": float(parts[3]),
                            "low": float(parts[4]),
                            "volume": int(parts[5]),
                            "amount": float(parts[6]),
                        })
                return results
        except Exception:
            pass
        return []

    # ==================== 巨潮资讯 - 财务报表 ====================

    def get_financial_report(self, symbol: str, report_type: str = "balance") -> Dict[str, Any]:
        """从巨潮资讯获取财务报表"""
        try:
            # report_type: balance(资产负债表), income(利润表), cashflow(现金流量表)
            type_map = {
                "balance": "资产负债表",
                "income": "利润表",
                "cashflow": "现金流量表",
            }

            org_id = ""
            if symbol.startswith("6"):
                org_id = f"{'SH' + symbol}"
            else:
                org_id = f"{'SZ' + symbol}"

            url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                "reportName": f"RPT_DMSK_FN_{report_type.upper()}",
                "columns": "ALL",
                "filter": f'(SECURITY_CODE="{symbol}")',
                "pageNumber": "1",
                "pageSize": "4",
                "sortTypes": "-1",
                "sortColumns": "REPORT_DATE",
                "source": "WEB",
                "client": "WEB",
                "ut": "fa5fd1943c7b386f172d6893dbbd4847",
            }
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                result_data = data.get("result", {})
                if result_data:
                    items = result_data.get("data", [])
                    if items:
                        return {
                            "source": "巨潮资讯/东方财富",
                            "report_type": type_map.get(report_type, report_type),
                            "symbol": symbol,
                            "data": items[:4],
                            "count": len(items),
                        }
        except Exception:
            pass
        return {"source": "巨潮资讯", "report_type": report_type, "error": "获取失败"}

    def get_stock_list(self, market: str = "all", limit: int = 50) -> List[Dict]:
        """获取股票列表"""
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1",
                "pz": str(limit),
                "po": "1",
                "np": "1",
                "ut": "fa5fd1943c7b386f172d6893dbbd4847",
                "fltt": "2",
                "invt": "2",
                "fid": "f3",
                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                "fields": "f2,f3,f4,f12,f14",
            }
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                diff = data.get("diff", [])
                return [
                    {
                        "symbol": item.get("f12", ""),
                        "name": item.get("f14", ""),
                        "price": item.get("f2", 0),
                        "change_pct": item.get("f3", 0),
                    }
                    for item in diff[:limit]
                ]
        except Exception:
            pass
        return []

    # ==================== 个股公告 ====================

    def get_stock_announcements(self, symbol: str, limit: int = 10) -> List[Dict]:
        """获取个股公告列表"""
        try:
            url = "https://np-anotice-stock.eastmoney.com/api/security/ann"
            params = {
                "sr": "-1",
                "page_size": str(limit),
                "page_index": "1",
                "ann_type": "A",
                "client_source": "web",
                "stock_list": symbol,
                "f_node": "0",
                "s_node": "0",
            }
            resp = requests.get(url, params=params, headers=self.HEADERS, timeout=self.TIMEOUT)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                items = data.get("list", [])
                return [
                    {
                        "title": item.get("title", ""),
                        "date": item.get("notice_date", "")[:10],
                        "type": item.get("ann_type", ""),
                        "url": f"https://data.eastmoney.com/notices/detail/{symbol}/{item.get('art_code', '')}.html",
                    }
                    for item in items[:limit]
                ]
        except Exception:
            pass
        return []


stock_crawler = StockCrawler()
