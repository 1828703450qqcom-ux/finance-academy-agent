from fastapi import APIRouter
from services.akshare_service import get_macro_overview, get_chart_data
from crawlers.macro_crawler import macro_crawler
import asyncio
from functools import partial

router = APIRouter(prefix="/api/macro", tags=["macro"])


@router.get("/overview")
async def macro_overview():
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, get_macro_overview)
    return data


@router.get("/chart/{indicator}")
async def macro_chart(indicator: str):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, partial(get_chart_data, indicator))
    return data


@router.get("/indicators")
async def list_indicators():
    return {
        "indicators": [
            {"key": "shanghai", "name": "上证指数", "category": "国内宏观", "source": "AKShare"},
            {"key": "cpi", "name": "CPI当月同比", "category": "国内宏观", "source": "AKShare"},
            {"key": "pmi", "name": "PMI制造业", "category": "国内宏观", "source": "AKShare"},
            {"key": "m2", "name": "M2同比增速", "category": "国内宏观", "source": "AKShare"},
            {"key": "ppi", "name": "PPI", "category": "国内宏观", "source": "统计局"},
            {"key": "lpr", "name": "LPR利率", "category": "货币政策", "source": "央行"},
            {"key": "social_financing", "name": "社会融资规模", "category": "货币政策", "source": "央行"},
            {"key": "trade", "name": "进出口数据", "category": "外贸", "source": "海关总署"},
        ]
    }


@router.get("/crawler/all")
async def crawler_all():
    """获取所有爬虫数据"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, macro_crawler.get_all_macro_data)


@router.get("/crawler/{indicator}")
async def crawler_data(indicator: str):
    """从权威数据源爬取数据"""
    crawlers = {
        "gdp": macro_crawler.get_gdp_stats,
        "cpi_stats": macro_crawler.get_cpi_stats,
        "ppi": macro_crawler.get_ppi_stats,
        "pmi_stats": macro_crawler.get_pmi_stats,
        "social_financing": macro_crawler.get_social_financing,
        "m2_crawler": macro_crawler.get_m2_data,
        "lpr": macro_crawler.get_lpr_rate,
        "trade": macro_crawler.get_trade_data,
    }
    func = crawlers.get(indicator)
    if func:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func)
    return {"error": f"未知指标: {indicator}"}
