"""
财报研报解析路由 - 基于AI的智能金融研报生成
使用东方财富直接HTTP接口获取数据
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import os
import json
import requests
from datetime import datetime

router = APIRouter(prefix="/api/finance-report", tags=["finance-report"])

REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report_outputs")
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class GenerateReportRequest(BaseModel):
    stock_code: str
    market: str = "A"
    company_name: Optional[str] = None
    report_type: str = "comprehensive"
    include_charts: bool = True
    analysis_depth: str = "standard"


class CompareRequest(BaseModel):
    stock_codes: List[str]
    market: str = "A"
    compare_metrics: List[str] = ["revenue", "profit", "pe_ratio", "roe"]


def _get_market_prefix(stock_code: str, market: str) -> str:
    if market == "HK":
        return "HK"
    code = str(stock_code)
    if code.startswith("6") or code.startswith("SH"):
        return "SH"
    return "SZ"


def _get_full_code(stock_code: str, market: str) -> str:
    code = str(stock_code).replace("SH", "").replace("SZ", "")
    prefix = _get_market_prefix(code, market)
    return f"{prefix}{code}"


def _fetch_balance_sheet(stock_code: str, market: str) -> list:
    try:
        url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_DMSK_FN_BALANCE",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "pageNumber": "1",
            "pageSize": "5",
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
        }
        r = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = r.json()
        if data.get("result") and data["result"].get("data"):
            return data["result"]["data"]
    except Exception as e:
        print(f"Balance sheet error: {e}")
    return []


def _fetch_income_statement(stock_code: str, market: str) -> list:
    try:
        url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_DMSK_FN_INCOME",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "pageNumber": "1",
            "pageSize": "5",
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
        }
        r = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = r.json()
        if data.get("result") and data["result"].get("data"):
            return data["result"]["data"]
    except Exception as e:
        print(f"Income statement error: {e}")
    return []


def _fetch_cash_flow(stock_code: str, market: str) -> list:
    try:
        url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_DMSK_FN_CASHFLOW",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "pageNumber": "1",
            "pageSize": "5",
            "sortTypes": "-1",
            "sortColumns": "REPORT_DATE",
        }
        r = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = r.json()
        if data.get("result") and data["result"].get("data"):
            return data["result"]["data"]
    except Exception as e:
        print(f"Cash flow error: {e}")
    return []


def _fetch_company_profile(stock_code: str, market: str) -> dict:
    full_code = _get_full_code(stock_code, market)
    info = {"code": stock_code, "market": market, "name": "", "industry": "", "description": ""}
    try:
        url = "https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax"
        params = {"code": full_code}
        r = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = r.json()
        if isinstance(data, dict):
            if "jbzl" in data and data["jbzl"]:
                jbzl = data["jbzl"][0] if isinstance(data["jbzl"], list) else data["jbzl"]
                info["name"] = jbzl.get("ORG_NAME_ABBR", "") or jbzl.get("ORG_NAME", "")
                info["industry"] = jbzl.get("INDUSTRYCSRC1", "") or jbzl.get("INDUSTRY_NAME", "")
            if "jygd" in data and data["jygd"]:
                jygd = data["jygd"]
                if isinstance(jygd, list) and len(jygd) > 0:
                    info["description"] = f"主营业务相关数据共{len(jygd)}条"
    except Exception as e:
        print(f"Company profile error: {e}")
    return info


def _fetch_main_financial_data(stock_code: str) -> dict:
    try:
        url = "https://datacenter.eastmoney.com/securities/api/data/get"
        params = {
            "type": "RPT_F10_FINANCE_MAINFINADATA",
            "sty": "ALL",
            "filter": f'(SECURITY_CODE="{stock_code}")',
            "p": "1",
            "ps": "5",
        }
        r = requests.get(url, params=params, timeout=15, headers=HEADERS)
        data = r.json()
        if data.get("result") and data["result"].get("data"):
            return data["result"]["data"]
    except Exception as e:
        print(f"Main financial data error: {e}")
    return []


def _format_balance_sheet(raw: list) -> list:
    result = []
    for item in raw:
        row = {
            "报告日期": item.get("REPORT_DATE_NAME", item.get("REPORT_DATE", "")),
            "总资产(万元)": item.get("TOTAL_ASSETS"),
            "总负债(万元)": item.get("TOTAL_LIABILITIES"),
            "股东权益(万元)": item.get("TOTAL_EQUITY"),
            "货币资金(万元)": item.get("MONETARYFUNDS"),
            "应收账款(万元)": item.get("ACCOUNTS_RECE"),
            "存货(万元)": item.get("INVENTORY"),
            "固定资产(万元)": item.get("FIXED_ASSET"),
            "流动资产(万元)": item.get("TOTAL_CURRENT_ASSETS"),
            "流动负债(万元)": item.get("TOTAL_CURRENT_LIAB"),
        }
        result.append(row)
    return result


def _format_income_statement(raw: list) -> list:
    result = []
    for item in raw:
        row = {
            "报告日期": item.get("REPORT_DATE_NAME", item.get("REPORT_DATE", "")),
            "营业总收入(万元)": item.get("TOTAL_OPERATE_INCOME"),
            "营业总成本(万元)": item.get("TOTAL_OPERATE_COST"),
            "营业利润(万元)": item.get("OPERATE_PROFIT"),
            "净利润(万元)": item.get("NETPROFIT"),
            "归母净利润(万元)": item.get("PARENT_NETPROFIT"),
            "毛利率": item.get("XSMLL"),
            "净利率": item.get("XSJLL"),
        }
        result.append(row)
    return result


def _format_cash_flow(raw: list) -> list:
    result = []
    for item in raw:
        row = {
            "报告日期": item.get("REPORT_DATE_NAME", item.get("REPORT_DATE", "")),
            "经营活动现金流入(万元)": item.get("TOTAL_OPERATE_INFLOW"),
            "经营活动现金流出(万元)": item.get("TOTAL_OPERATE_OUTFLOW"),
            "经营活动现金流净额(万元)": item.get("NETCASH_OPERATE"),
            "投资活动现金流净额(万元)": item.get("NETCASH_INVEST"),
            "筹资活动现金流净额(万元)": item.get("NETCASH_FINANCE"),
            "现金及等价物净增加额(万元)": item.get("CCE_ADD"),
        }
        result.append(row)
    return result


async def _fetch_financial_data(stock_code: str, market: str) -> dict:
    """获取完整财务数据"""
    balance = await asyncio.get_event_loop().run_in_executor(
        None, _fetch_balance_sheet, stock_code, market
    )
    income = await asyncio.get_event_loop().run_in_executor(
        None, _fetch_income_statement, stock_code, market
    )
    cashflow = await asyncio.get_event_loop().run_in_executor(
        None, _fetch_cash_flow, stock_code, market
    )
    return {
        "balance_sheet": _format_balance_sheet(balance) if balance else [],
        "income_statement": _format_income_statement(income) if income else [],
        "cash_flow": _format_cash_flow(cashflow) if cashflow else [],
        "raw_counts": {
            "balance_sheet": len(balance),
            "income_statement": len(income),
            "cash_flow": len(cashflow),
        }
    }


async def _fetch_company_info(stock_code: str, market: str) -> dict:
    """获取公司信息"""
    return await asyncio.get_event_loop().run_in_executor(
        None, _fetch_company_profile, stock_code, market
    )


def _safe_format(val, decimals=2, suffix=""):
    """安全格式化数字，N/A返回占位符"""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):,.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def _compute_key_metrics(financial_data: dict, main_data: list) -> dict:
    """预计算关键财务指标，供AI分析使用"""
    metrics = {}
    income = financial_data.get("income_statement", [])
    balance = financial_data.get("balance_sheet", [])
    cashflow = financial_data.get("cash_flow", [])

    # 从利润表提取数据
    if income and len(income) >= 1:
        latest = income[0]
        metrics["最新报告期"] = latest.get("报告日期", "N/A")
        metrics["营业总收入(万元)"] = latest.get("营业总收入(万元)")
        metrics["净利润(万元)"] = latest.get("净利润(万元)")
        metrics["归母净利润(万元)"] = latest.get("归母净利润(万元)")
        metrics["毛利率(%)"] = latest.get("毛利率")
        metrics["净利率(%)"] = latest.get("净利率")

        # 计算营收同比增长率
        if len(income) >= 2:
            prev = income[1]
            curr_rev = latest.get("营业总收入(万元)")
            prev_rev = prev.get("营业总收入(万元)")
            if curr_rev and prev_rev and prev_rev != 0:
                metrics["营收同比增长率(%)"] = round((curr_rev - prev_rev) / abs(prev_rev) * 100, 2)

            curr_profit = latest.get("归母净利润(万元)")
            prev_profit = prev.get("归母净利润(万元)")
            if curr_profit and prev_profit and prev_profit != 0:
                metrics["归母净利润同比增长率(%)"] = round((curr_profit - prev_profit) / abs(prev_profit) * 100, 2)

    # 从资产负债表提取数据
    if balance and len(balance) >= 1:
        latest_b = balance[0]
        total_assets = latest_b.get("总资产(万元)")
        total_liab = latest_b.get("总负债(万元)")
        equity = latest_b.get("股东权益(万元)")
        current_assets = latest_b.get("流动资产(万元)")
        current_liab = latest_b.get("流动负债(万元)")

        if total_assets and total_liab and total_assets != 0:
            metrics["资产负债率(%)"] = round(total_liab / total_assets * 100, 2)
        if current_assets and current_liab and current_liab != 0:
            metrics["流动比率"] = round(current_assets / current_liab, 2)

        # ROE = 归母净利润 / 股东权益
        if equity and equity != 0 and metrics.get("归母净利润(万元)"):
            metrics["ROE(%)"] = round(metrics["归母净利润(万元)"] / equity * 100, 2)

        # ROA = 净利润 / 总资产
        if total_assets and total_assets != 0 and metrics.get("净利润(万元)"):
            metrics["ROA(%)"] = round(metrics["净利润(万元)"] / total_assets * 100, 2)

    # 从现金流量表提取数据
    if cashflow and len(cashflow) >= 1:
        latest_cf = cashflow[0]
        ocf = latest_cf.get("经营活动现金流净额(万元)")
        metrics["经营活动现金流净额(万元)"] = ocf
        if ocf and metrics.get("归母净利润(万元)") and metrics["归母净利润(万元)"] != 0:
            metrics["经营现金流/净利润(%)"] = round(ocf / metrics["归母净利润(万元)"] * 100, 2)

    # 毛利率趋势
    if income and len(income) >= 2:
        margins = [item.get("毛利率") for item in income if item.get("毛利率") is not None]
        if len(margins) >= 2:
            metrics["毛利率趋势"] = "上升" if margins[0] > margins[-1] else "下降" if margins[0] < margins[-1] else "稳定"
            metrics["毛利率变化(百分点)"] = round(margins[0] - margins[-1], 2)

    # 3年复合增长率CAGR
    if income and len(income) >= 4:
        try:
            latest_rev = income[0].get("营业总收入(万元)")
            oldest_rev = income[-1].get("营业总收入(万元)")
            if latest_rev and oldest_rev and oldest_rev > 0:
                years = len(income) - 1
                metrics["营收3年CAGR(%)"] = round((pow(latest_rev / oldest_rev, 1 / years) - 1) * 100, 2)
        except Exception:
            pass

    return metrics


def _build_analysis_prompt(report_type: str, depth: str) -> str:
    """构建专业的金融分析师提示词"""
    base = """你是一位资深的A股卖方金融分析师，拥有CFA/CPA资格，擅长撰写专业的股票研究报告。

## 报告撰写准则
1. 数据驱动：所有分析必须基于提供的财务数据，引用具体数字，不做空泛描述
2. 逻辑严密：每个结论都要有数据支撑，分析要有因果关系和逻辑链条
3. 观点明确：给出明确的投资评级（买入/增持/中性/减持/卖出）和目标价区间
4. 风险导向：充分揭示风险，按概率和影响程度排序
5. 专业规范：符合券商研报的行业标准格式

## 报告结构（必须严格按此结构输出）

### 一、投资摘要（Executive Summary）
- 投资评级：[买入/增持/中性/减持/卖出]
- 核心逻辑：用1-2句话概括投资核心观点
- 关键催化剂：未来3-6个月的关键事件
- 风险提示：最主要的1-2个风险

### 二、公司概况
- 主营业务与商业模式
- 行业地位与竞争格局
- 核心竞争力分析

### 三、财务深度分析
- 盈利能力：毛利率、净利率、ROE、ROA趋势分析
- 成长能力：营收和利润增长趋势、增长驱动因素
- 偿债能力：资产负债率、流动比率、速动比率
- 运营效率：应收账款周转、存货周转、总资产周转
- 现金流质量：经营现金流与净利润的匹配度

### 四、估值分析
- 相对估值：PE/PB/PS与行业均值、历史均值对比
- 估值区间：合理PE范围、目标价计算逻辑
- 安全边际：当前价格相对合理估值的折价/溢价

### 五、风险因素（按重要性排序）
1. [高概率/高影响风险]
2. [中等风险]
3. [低概率但需关注的风险]

### 六、投资建议与目标价
- 综合评级及理由
- 12个月目标价区间
- 投资时间框架"""

    if report_type == "valuation":
        base += """

## 估值分析重点
请重点展开估值分析部分：
- DCF估值模型的关键假设与计算
- 可比公司法：选取同行业可比公司，对比PE/PB/EV/EBITDA
- 历史估值区间分析
- 分部估值法（如适用）
- 给出明确的合理价值区间和安全边际"""
    elif report_type == "risk":
        base += """

## 风险分析重点
请重点展开风险分析部分：
- 财务风险：偿债能力、现金流压力、应收账款质量
- 经营风险：客户集中度、供应链依赖、管理层变动
- 行业风险：政策变化、技术替代、竞争加剧
- 市场风险：估值泡沫、流动性、大股东减持
- 每个风险给出发生概率和影响程度评级"""
    else:
        base += "\n请综合分析：公司概况、财务状况、行业地位、估值分析、风险提示、投资建议。"

    if depth == "detailed":
        base += """

## 深度分析要求
- 3-5年财务趋势分析，识别长期增长动力
- 同业横向对比，评估竞争地位
- 关键财务指标的驱动因素分解
- 未来3年盈利预测与估值
- 情景分析（乐观/中性/悲观）"""

    return base


def _build_compare_prompt() -> str:
    """构建同业对比分析提示词"""
    return """你是专业的金融分析师，擅长进行公司间的横向对比分析。

## 对比分析框架
请从以下维度进行深度对比，每个维度给出明确的优劣势判断：

### 1. 规模与成长性
- 营收规模对比、营收增长率对比
- 净利润规模对比、利润增长率对比
- 市值规模与行业排名

### 2. 盈利能力
- 毛利率、净利率对比
- ROE、ROA对比
- 盈利质量（经营现金流/净利润）

### 3. 偿债能力与财务健康度
- 资产负债率对比
- 流动比率对比
- 利息保障倍数

### 4. 估值水平
- PE/PB/PS对比
- EV/EBITDA对比
- 估值合理性判断

### 5. 综合评分
请对每家公司给出1-10分的综合评分，并说明理由。

### 6. 投资建议
- 明确推荐哪家公司，为什么
- 各公司的适合投资者类型"""


@router.post("/generate")
async def generate_finance_report(req: GenerateReportRequest):
    """生成金融研报"""
    from services.llm_service import call_minimax

    try:
        financial_data = await _fetch_financial_data(req.stock_code, req.market)
        company_info = await _fetch_company_info(req.stock_code, req.market)
        main_data = await asyncio.get_event_loop().run_in_executor(
            None, _fetch_main_financial_data, req.stock_code
        )

        # 预计算关键指标
        key_metrics = _compute_key_metrics(financial_data, main_data if isinstance(main_data, list) else [])

        system_prompt = _build_analysis_prompt(req.report_type, req.analysis_depth)

        # 构建结构化的用户消息
        metrics_text = "\n".join([f"- {k}: {_safe_format(v) if isinstance(v, (int, float)) else v}" for k, v in key_metrics.items()])

        user_msg = f"""请为以下公司生成一份专业的金融研究报告（遵循系统提示词的报告结构）。

## 一、公司基本信息
{json.dumps(company_info, ensure_ascii=False, indent=2)}

## 二、预计算关键财务指标
{metrics_text}

## 三、详细财务数据（仅最新2期）

### 资产负债表
{json.dumps(financial_data.get('balance_sheet', [])[:2], ensure_ascii=False, indent=2)}

### 利润表
{json.dumps(financial_data.get('income_statement', [])[:2], ensure_ascii=False, indent=2)}

### 现金流量表
{json.dumps(financial_data.get('cash_flow', [])[:2], ensure_ascii=False, indent=2)}

### 主要财务指标
{json.dumps(main_data[:2] if main_data else [], ensure_ascii=False, indent=2)}

## 四、报告要求
请严格按照系统提示词中的报告结构生成完整报告。每个部分必须包含具体数字和数据分析，不要泛泛而谈。"""

        def _call():
            return call_minimax(
                system_prompt=system_prompt,
                user_message=user_msg,
                temperature=0.5,
                max_tokens=8000,
                timeout=300,
            )

        loop = asyncio.get_event_loop()
        report_content = await loop.run_in_executor(None, _call)

        import logging
        logger = logging.getLogger("finance_report")
        logger.warning(f"REPORT_CONTENT_LENGTH: {len(report_content)}, FIRST_200: {report_content[:200]}")

        report_id = f"{req.stock_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_path = os.path.join(REPORT_OUTPUT_DIR, f"{report_id}.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        return {
            "success": True,
            "report_id": report_id,
            "content": report_content,
            "company_name": company_info.get("name", req.stock_code),
            "generated_at": datetime.now().isoformat(),
            "key_metrics": key_metrics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研报失败: {str(e)}")


@router.post("/compare")
async def compare_companies(req: CompareRequest):
    """同业对比分析"""
    from services.llm_service import call_minimax

    try:
        companies_data = []
        for code in req.stock_codes[:5]:
            financial_data = await _fetch_financial_data(code, req.market)
            company_info = await _fetch_company_info(code, req.market)
            main_data = await asyncio.get_event_loop().run_in_executor(
                None, _fetch_main_financial_data, code
            )
            key_metrics = _compute_key_metrics(financial_data, main_data if isinstance(main_data, list) else [])
            companies_data.append({
                "code": code,
                "info": company_info,
                "financials": financial_data,
                "key_metrics": key_metrics,
            })

        system_prompt = _build_compare_prompt()

        user_msg = f"""请对比分析以下{len(companies_data)}家公司：

{json.dumps(companies_data, ensure_ascii=False, indent=2)}

请严格按照对比框架进行分析，给出综合评分和投资建议。"""

        def _call():
            return call_minimax(system_prompt=system_prompt, user_message=user_msg, temperature=0.5, max_tokens=6000, timeout=300)

        loop = asyncio.get_event_loop()
        report = await loop.run_in_executor(None, _call)

        return {"success": True, "report": report, "companies": [d["code"] for d in companies_data]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")


@router.get("/financial-data/{stock_code}")
async def get_financial_data(stock_code: str, market: str = "A"):
    """获取公司财务数据"""
    try:
        data = await _fetch_financial_data(stock_code, market)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/company-info/{stock_code}")
async def get_company_info(stock_code: str, market: str = "A"):
    """获取公司基本信息"""
    try:
        info = await _fetch_company_info(stock_code, market)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")
