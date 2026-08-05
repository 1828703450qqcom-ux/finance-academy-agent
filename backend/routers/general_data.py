"""
通用数据搜索路由
支持任意行业/技术/宏观数据检索
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/data", tags=["general-data"])


class GeneralSearchRequest(BaseModel):
    topic: str
    keywords: Optional[str] = ""


@router.post("/search")
async def search_general_data(req: GeneralSearchRequest):
    """通用数据搜索 - 支持任意主题"""
    from crawlers.general_data_crawler import get_general_crawler

    crawler = get_general_crawler()
    result = crawler.search_data(req.topic)

    # 如果有附加关键词，也搜索
    if req.keywords:
        for kw in req.keywords.split(","):
            kw = kw.strip()
            if kw:
                extra = crawler.search_data(kw)
                if extra.get("data"):
                    result["data"].update(extra["data"])
                if extra.get("sources"):
                    result["sources"].extend(extra["sources"])

    # 去重
    result["sources"] = list(set(result["sources"]))

    return result


@router.get("/indicators")
async def get_indicators():
    """获取所有可用数据指标分类"""
    from crawlers.general_data_crawler import get_general_crawler

    crawler = get_general_crawler()
    return crawler.get_available_indicators()


@router.post("/search-ai")
async def search_with_ai(req: GeneralSearchRequest):
    """AI辅助数据搜索 - 用LLM分析数据需求并推荐数据源"""
    from services.llm_service import call_minimax

    system_prompt = """你是金融数据专家，帮助研究者找到所需数据。

## 你的能力
1. 推荐合适的数据源（官方统计、数据库、API）
2. 提供具体的数据获取方法
3. 说明数据的局限性和注意事项

## 输出格式
用Markdown格式输出：
- 数据源名称和链接
- 具体指标名称
- 数据频率和时间范围
- 获取方法（API/手动下载）
- 数据质量评估"""

    user_msg = f"我需要找到关于「{req.topic}」的数据"
    if req.keywords:
        user_msg += f"\n关键词：{req.keywords}"
    user_msg += "\n\n请推荐最合适的数据源和获取方法。"

    def _call():
        return call_minimax(
            system_prompt=system_prompt,
            user_message=user_msg,
            temperature=0.5,
            max_tokens=2000,
        )

    import asyncio
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    # 同时获取爬虫数据
    from crawlers.general_data_crawler import get_general_crawler
    crawler = get_general_crawler()
    crawler_data = crawler.search_data(req.topic)

    return {
        "ai_recommendation": response,
        "crawler_data": crawler_data,
        "topic": req.topic,
    }
