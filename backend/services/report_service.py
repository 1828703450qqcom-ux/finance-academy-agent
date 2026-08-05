import fitz
import pdfplumber
import re
import json
from typing import Dict, Any, Optional


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception:
        pass
    if len(text.strip()) < 100:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t
        except Exception:
            pass
    return text


def extract_numbers(text: str, patterns: list) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                val = match.group(1).replace(",", "").replace("，", "")
                return float(val)
            except (ValueError, IndexError):
                continue
    return None


def parse_financial_report(file_path: str) -> Dict[str, Any]:
    text = extract_text_from_pdf(file_path)
    result = {"raw_text_length": len(text), "sections": []}

    keywords = [
        "营业收入", "净利润", "总资产", "净资产", "每股收益",
        "毛利率", "净利率", "资产负债率", "流动比率", "速动比率",
        "经营现金流", "投资现金流", "筹资现金流",
    ]
    found = {}
    for kw in keywords:
        val = extract_numbers(
            text,
            [
                rf"{kw}[^0-9\-]*?([\d,，.]+)",
                rf"{kw}[^0-9\-]*?([\d,，.]+)\s*万",
                rf"{kw}[^0-9\-]*?([\d,，.]+)\s*亿",
            ],
        )
        if val is not None:
            found[kw] = val
    result["extracted_data"] = found

    dupont = {}
    net_profit = found.get("净利润")
    revenue = found.get("营业收入")
    total_assets = found.get("总资产")
    equity = found.get("净资产")

    if net_profit and revenue and revenue > 0:
        dupont["net_margin"] = round(net_profit / revenue * 100, 2)
    if revenue and total_assets and total_assets > 0:
        dupont["asset_turnover"] = round(revenue / total_assets, 4)
    if total_assets and equity and equity > 0:
        dupont["equity_multiplier"] = round(total_assets / equity, 4)
    if (
        dupont.get("net_margin")
        and dupont.get("asset_turnover")
        and dupont.get("equity_multiplier")
    ):
        dupont["roe"] = round(
            dupont["net_margin"]
            * dupont["asset_turnover"]
            * dupont["equity_multiplier"]
            / 100,
            2,
        )

    result["dupont"] = dupont

    result["summary"] = (
        f"已从财报中提取到 {len(found)} 项关键财务数据。"
        + (f"杜邦分析ROE为 {dupont.get('roe', '未知')}%" if dupont.get("roe") else "")
    )

    return result


def analyze_report(file_path: str, dimensions: list) -> Dict[str, Any]:
    data = parse_financial_report(file_path)
    result = {
        "company_name": "未知公司",
        "year": 2024,
        "extracted_data": data.get("extracted_data", {}),
        "dupont": data.get("dupont", {}),
        "summary": data.get("summary", ""),
        "dimensions_analyzed": dimensions,
    }

    extracted = data.get("extracted_data", {})
    if "营业收入" in extracted:
        result["revenue_analysis"] = {
            "revenue": extracted["营业收入"],
            "note": "营收数据已提取",
        }
    if "净利润" in extracted:
        result["profitability"] = {
            "net_profit": extracted["净利润"],
            "net_margin": data.get("dupont", {}).get("net_margin"),
        }
    if "资产负债率" in extracted:
        result["solvency"] = {"debt_ratio": extracted["资产负债率"]}
    if "经营现金流" in extracted:
        result["cashflow"] = {"operating_cf": extracted["经营现金流"]}

    return result
