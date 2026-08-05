"""
实证研究数据模块 - 获取真实A股财务数据用于回归分析
数据源：AKShare (东方财富、国家统计局)
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class ResearchCrawler:
    """获取真实A股财务数据用于实证研究"""

    @staticmethod
    def _parse_number(val) -> Optional[float]:
        """解析AKShare返回的数值，处理百分号、亿等后缀"""
        if val is None:
            return None
        s = str(val).strip()
        if not s or s == '--' or s == '-':
            return None
        # 去掉常见后缀
        s = s.replace('%', '').replace('亿', '').replace('万', '').replace(',', '')
        try:
            return float(s)
        except (ValueError, TypeError):
            return None

    # 变量名映射到AKShare字段
    VARIABLE_FIELD_MAP = {
        # 被解释变量
        "融资成本": "cost_of_debt",
        "企业价值": "tbq",
        "托宾Q": "tbq",
        "ROE": "roe",
        "净资产收益率": "roe",
        "ROA": "roa",
        "总资产收益率": "roa",
        "净利润增速": "profit_growth",
        "营业收入增速": "revenue_growth",
        "股价收益率": "return",
        "股票收益": "return",
        # 解释变量
        "ESG评级": "esg_score",
        "ESG": "esg_score",
        "机构投资者持股": "institutional_pct",
        "股权集中度": "top10_pct",
        "独立董事比例": "independent_ratio",
        "董事会规模": "board_size",
        "审计质量": "audit_quality",
        "信息披露质量": "disclosure_score",
        "数字化转型": "digital_score",
        "绿色创新": "green_patent",
        # 控制变量
        "企业规模": "ln_assets",
        "资产负债率": "debt_ratio",
        "盈利能力": "profitability",
        "成长性": "growth_rate",
        "现金流": "cashflow_ratio",
        "公司年龄": "firm_age",
        "企业规模(ln)": "ln_assets",
        "资产规模": "ln_assets",
        "总资产对数": "ln_assets",
    }

    # A股真实股票代码池（覆盖各行业龙头）
    STOCK_POOL = [
        # 金融
        "601318", "600036", "601166", "600016", "601328",
        # 消费
        "600519", "000858", "000568", "603288", "002304",
        # 医药
        "600276", "000538", "300760", "600196", "002007",
        # 科技
        "002415", "300059", "600845", "002230", "300033",
        # 制造
        "600031", "000333", "601633", "600585", "002475",
        # 能源
        "601857", "600028", "601088", "600900", "600886",
        # 地产/基建
        "001979", "600048", "600606", "000002", "601668",
        # 其他
        "601012", "600309", "601225", "002352", "600030",
    ]

    def _get_stock_financial_data(self, symbol: str) -> Optional[Dict]:
        """获取单只股票的财务数据（使用同花顺接口，东方财富接口在服务器被封）"""
        try:
            import akshare as ak
            # 使用同花顺财务摘要
            df = ak.stock_financial_abstract_ths(symbol=symbol, indicator='按报告期')
            if df is None or len(df) == 0:
                return None

            latest = df.iloc[-1]  # 最新一期（数据按时间升序排列）
            result = {}

            # ROE
            roe = self._parse_number(latest.get('净资产收益率'))
            if roe is not None:
                result["roe"] = round(float(roe), 4)

            # 销售净利率（近似ROA）
            net_margin = self._parse_number(latest.get('销售净利率'))
            if net_margin is not None:
                result["roa"] = round(float(net_margin), 4)

            # 资产负债率
            debt_ratio = self._parse_number(latest.get('资产负债率'))
            if debt_ratio is not None:
                result["debt_ratio"] = round(float(debt_ratio), 4)

            # 每股收益
            eps = self._parse_number(latest.get('基本每股收益'))
            if eps is not None:
                result["earnings_per_share"] = round(float(eps), 4)

            # 成长性
            rev_growth = self._parse_number(latest.get('营业总收入同比增长率'))
            if rev_growth is not None:
                result["revenue_growth"] = round(float(rev_growth), 4)

            # 流动比率
            current_ratio = self._parse_number(latest.get('流动比率'))
            if current_ratio is not None:
                result["current_ratio"] = round(float(current_ratio), 4)

            return result if result else None
        except Exception:
            return None

    def _get_stock_price_data(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票价格数据（优先网易源，东方财富在服务器不稳定）"""
        try:
            import akshare as ak
            # 主数据源：网易
            try:
                prefix = "sh" if symbol.startswith("6") else "sz"
                df = ak.stock_zh_a_daily(symbol=f"{prefix}{symbol}", adjust="qfq")
                if df is not None and len(df) > 0:
                    df["date"] = pd.to_datetime(df["date"])
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
                    if len(df) > 0:
                        df = df.rename(columns={"date": "date", "close": "close", "open": "open", "high": "high", "low": "low", "volume": "volume"})
                        df["return"] = df["close"].pct_change()
                        return df
            except Exception:
                pass
            # 备用：东方财富
            df = ak.stock_zh_a_hist(
                symbol=symbol, period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
            if df is not None and len(df) > 0:
                df = df.rename(columns={"日期": "date", "收盘": "close", "开盘": "open", "最高": "high", "最低": "low", "成交量": "volume"})
                df["return"] = df["close"].pct_change()
                return df
        except Exception:
            pass
        return None

    def _get_index_data(self) -> Optional[pd.DataFrame]:
        """获取沪深300指数数据作为市场因子"""
        try:
            import akshare as ak
            df = ak.stock_zh_index_daily(symbol="sh000300")
            if df is not None and len(df) > 0:
                df = df.rename(columns={"date": "date", "close": "market_close"})
                df["market_return"] = df["market_close"].pct_change()
                return df[["date", "market_return"]].dropna()
        except Exception:
            pass
        return None

    def auto_detect_variables(self, project_name: str) -> Dict[str, Any]:
        """根据课题名称自动识别变量和推荐模型"""
        detected = {
            "dependent_var": "",
            "independent_vars": [],
            "control_vars": [],
            "data_sources": ["AKShare/东方财富"],
            "suggested_model": "fixed",
        }

        name = project_name

        # 被解释变量
        dep_map = {
            "融资成本": "融资成本", "企业价值": "企业价值", "托宾Q": "托宾Q",
            "ROE": "ROE", "净资产收益率": "ROE", "ROA": "ROA",
            "公司绩效": "ROE", "企业绩效": "ROE", "绩效": "ROE",
            "股价": "股价收益率", "收益": "股价收益率", "回报": "股价收益率",
            "创新": "ROE", "价值": "企业价值",
        }
        for kw, var in dep_map.items():
            if kw in name:
                detected["dependent_var"] = var
                break
        if not detected["dependent_var"]:
            detected["dependent_var"] = "ROE"

        # 解释变量
        ind_map = {
            "ESG": "ESG评级", "绿色": "ESG评级", "可持续": "ESG评级",
            "机构投资": "机构投资者持股", "机构持股": "机构投资者持股",
            "股权集中": "股权集中度", "控股": "股权集中度",
            "独立董事": "独立董事比例", "治理": "独立董事比例",
            "数字化": "数字化转型", "数字": "数字化转型",
            "创新": "绿色创新", "研发": "绿色创新", "专利": "绿色创新",
            "审计": "审计质量", "信息披露": "信息披露质量",
        }
        for kw, var in ind_map.items():
            if kw in name and var not in detected["independent_vars"]:
                detected["independent_vars"].append(var)
        if not detected["independent_vars"]:
            detected["independent_vars"] = ["ESG评级"]

        # 控制变量
        detected["control_vars"] = ["企业规模", "资产负债率", "盈利能力"]

        # 模型推荐
        if "政策" in name or "双重差分" in name or "DID" in name:
            detected["suggested_model"] = "fixed"
        elif "内生" in name or "工具变量" in name or "IV" in name:
            detected["suggested_model"] = "gmm"
        else:
            detected["suggested_model"] = "fixed"

        return detected

    def generate_research_data(
        self,
        dependent_var: str,
        independent_vars: List[str],
        control_vars: List[str],
        n_firms: int = 40,
        n_years: int = 5,
    ) -> Dict[str, Any]:
        """
        基于真实A股数据构建面板数据集
        优先用AKShare获取真实财务数据，失败时用基于行业特征的模拟数据
        返回 dict: {"data": [...], "data_source": "real_akshare"|"simulated", "data_note": "..."}
        """
        all_vars = list(set([dependent_var] + independent_vars + control_vars))

        # 尝试获取真实数据
        real_data = self._try_real_data(dependent_var, independent_vars, control_vars, n_firms)
        if real_data and len(real_data) >= 20:
            return {
                "data": real_data,
                "data_source": "real_akshare",
                "data_note": "数据来自AKShare(东方财富)，为真实A股上市公司财务数据",
                "n_obs": len(real_data),
            }

        # fallback: 基于真实统计分布的模拟数据
        sim_data = self._generate_statistical_data(dependent_var, independent_vars, control_vars, n_firms, n_years)
        return {
            "data": sim_data,
            "data_source": "simulated",
            "data_note": "⚠️ 当前为模拟数据（基于A股统计分布生成），仅供方法演示。正式研究请使用CSMAR/Wind/AKShare获取真实数据后上传CSV。",
            "n_obs": len(sim_data),
        }

    def _try_real_data(
        self, dependent_var: str, independent_vars: List[str], control_vars: List[str], n_firms: int
    ) -> List[Dict]:
        """尝试从AKShare获取真实财务数据（使用同花顺接口，东方财富接口在服务器被封）"""
        try:
            import akshare as ak

            # 获取少量股票
            try:
                symbols = self.STOCK_POOL[:min(n_firms, 15)]
            except Exception:
                symbols = self.STOCK_POOL[:15]

            all_data = []
            for symbol in symbols[:10]:  # limit to 10 stocks for speed
                try:
                    # 使用同花顺财务摘要（东方财富接口在服务器被封）
                    fin_df = ak.stock_financial_abstract_ths(symbol=symbol, indicator='按报告期')
                    if fin_df is None or len(fin_df) < 3:
                        continue

                    for i, row in fin_df.tail(n_years).iterrows():
                        report_date = str(row.get('报告期', ''))
                        # 从报告期提取年份
                        try:
                            year = int(report_date[:4]) if report_date else 2024
                        except Exception:
                            year = 2024

                        record = {"firm_id": symbol, "year": year}

                        # ROE
                        roe = self._parse_number(row.get('净资产收益率'))
                        if roe is not None:
                            record["ROE"] = round(float(roe), 4)
                            record["盈利能力"] = round(float(roe), 4)

                        # 销售净利率
                        net_margin = self._parse_number(row.get('销售净利率'))
                        if net_margin is not None:
                            record["销售净利率"] = round(float(net_margin), 4)

                        # 资产负债率
                        debt_ratio = self._parse_number(row.get('资产负债率'))
                        if debt_ratio is not None:
                            record["资产负债率"] = round(float(debt_ratio), 4)

                        # 基本每股收益
                        eps = self._parse_number(row.get('基本每股收益'))
                        if eps is not None:
                            record["每股收益"] = round(float(eps), 4)

                        # 每股净资产
                        bvps = self._parse_number(row.get('每股净资产'))
                        if bvps is not None:
                            record["每股净资产"] = round(float(bvps), 4)

                        # 营业总收入同比增长率 → 成长性
                        rev_growth = self._parse_number(row.get('营业总收入同比增长率'))
                        if rev_growth is not None:
                            record["成长性"] = round(float(rev_growth), 4)
                            record["营业收入增长率"] = round(float(rev_growth), 4)

                        # 净利润同比增长率
                        profit_growth = self._parse_number(row.get('净利润同比增长率'))
                        if profit_growth is not None:
                            record["净利润增长率"] = round(float(profit_growth), 4)

                        # 流动比率
                        current_ratio = self._parse_number(row.get('流动比率'))
                        if current_ratio is not None:
                            record["流动比率"] = round(float(current_ratio), 4)

                        # 速动比率
                        quick_ratio = self._parse_number(row.get('速动比率'))
                        if quick_ratio is not None:
                            record["速动比率"] = round(float(quick_ratio), 4)

                        # 每股经营现金流
                        ocfps = self._parse_number(row.get('每股经营现金流'))
                        if ocfps is not None:
                            record["每股经营现金流"] = round(float(ocfps), 4)

                        # 营业总收入
                        revenue = self._parse_number(row.get('营业总收入'))
                        if revenue is not None:
                            record["营业总收入"] = round(float(revenue), 4)

                        # 净利润
                        net_profit = self._parse_number(row.get('净利润'))
                        if net_profit is not None:
                            record["净利润"] = round(float(net_profit), 4)

                        if len(record) > 2:
                            all_data.append(record)

                    if len(all_data) >= 20:
                        break
                except Exception:
                    continue

            if len(all_data) >= 20:
                df = pd.DataFrame(all_data)
                # 检查所需变量是否都有真实数据
                required_vars = [dependent_var] + independent_vars + control_vars
                missing_vars = [v for v in required_vars if v not in df.columns]
                if missing_vars:
                    # 有变量缺失真实数据，不填充假数据，返回空让调用方用模拟数据
                    return []
                return df.to_dict("records")

        except Exception:
            pass
        return []

    def _generate_statistical_data(
        self, dependent_var: str, independent_vars: List[str], control_vars: List[str],
        n_firms: int, n_years: int,
    ) -> List[Dict]:
        """基于A股真实统计分布生成合理面板数据"""
        np.random.seed(42)
        all_vars = list(set([dependent_var] + independent_vars + control_vars))

        # A股典型财务指标分布
        STAT_DIST = {
            "ROE": {"mean": 8.5, "std": 12.0, "min": -30, "max": 50},
            "ROA": {"mean": 4.2, "std": 6.0, "min": -15, "max": 25},
            "企业价值": {"mean": 2.1, "std": 1.5, "min": 0.3, "max": 8.0},
            "托宾Q": {"mean": 2.1, "std": 1.5, "min": 0.3, "max": 8.0},
            "融资成本": {"mean": 5.5, "std": 2.0, "min": 1.0, "max": 15.0},
            "ESG评级": {"mean": 60, "std": 15, "min": 20, "max": 95},
            "ESG": {"mean": 60, "std": 15, "min": 20, "max": 95},
            "机构投资者持股": {"mean": 35, "std": 20, "min": 0, "max": 85},
            "股权集中度": {"mean": 55, "std": 15, "min": 15, "max": 90},
            "独立董事比例": {"mean": 33, "std": 8, "min": 10, "max": 55},
            "董事会规模": {"mean": 9, "std": 2.5, "min": 5, "max": 15},
            "审计质量": {"mean": 0.7, "std": 0.3, "min": 0, "max": 1},
            "信息披露质量": {"mean": 70, "std": 20, "min": 20, "max": 100},
            "数字化转型": {"mean": 50, "std": 25, "min": 0, "max": 100},
            "绿色创新": {"mean": 3, "std": 5, "min": 0, "max": 30},
            "企业规模": {"mean": 22, "std": 1.5, "min": 18, "max": 28},
            "企业规模(ln)": {"mean": 22, "std": 1.5, "min": 18, "max": 28},
            "资产负债率": {"mean": 42, "std": 18, "min": 5, "max": 90},
            "盈利能力": {"mean": 8.5, "std": 12.0, "min": -30, "max": 50},
            "成长性": {"mean": 12, "std": 25, "min": -50, "max": 100},
            "现金流": {"mean": 0.08, "std": 0.12, "min": -0.3, "max": 0.5},
            "公司年龄": {"mean": 15, "std": 8, "min": 2, "max": 35},
        }

        # 行业效应 (firm-level固定效应)
        industry_effects = {
            "金融": 1.2, "消费": 0.8, "医药": 1.0, "科技": 0.6,
            "制造": 0.3, "能源": 0.5, "地产": -0.2,
        }
        industries = list(industry_effects.keys())

        all_data = []
        for firm_id in range(n_firms):
            industry = industries[firm_id % len(industries)]
            firm_effect = industry_effects[industry] + np.random.normal(0, 0.3)
            sector = np.random.choice(["金融", "消费", "医药", "科技", "制造"])

            for year_offset in range(n_years):
                year = 2024 - year_offset
                row = {"firm_id": f"firm_{firm_id:03d}", "year": year, "industry": industry}

                # 生成各变量
                for var in all_vars:
                    if var in STAT_DIST:
                        d = STAT_DIST[var]
                        val = np.random.normal(d["mean"], d["std"])
                        val = np.clip(val, d["min"], d["max"])
                        row[var] = round(float(val), 4)
                    else:
                        row[var] = round(float(np.random.normal(0, 1)), 4)

                # 添加合理的相关性
                if dependent_var in row and independent_vars:
                    for i, ind_var in enumerate(independent_vars):
                        if ind_var in row:
                            coef = 0.15 * (i + 1) * np.random.choice([-1, 1])
                            row[dependent_var] += coef * row[ind_var]
                    row[dependent_var] += firm_effect
                    row[dependent_var] = round(float(row[dependent_var]), 4)

                all_data.append(row)

        return all_data

    def _resolve_stock_code(self, code_or_name: str) -> str:
        """将股票名称或代码解析为纯数字代码（支持中文名/拼音/代码）"""
        import re
        # 如果已经是纯数字，直接返回
        if re.match(r'^\d{6}$', code_or_name):
            return code_or_name
        # 腾讯智能搜索API（支持中文名、拼音、代码模糊搜索）
        try:
            import requests
            url = f'http://smartbox.gtimg.cn/s3/?v=2&q={code_or_name}&t=all&c=1'
            r = requests.get(url, timeout=5)
            text = r.text
            # 解析返回格式: v_hint="sh~600519~贵州茅台~gzmt~GP-A^sz~..."
            if 'v_hint="' in text:
                hint = text.split('v_hint="')[1].rstrip('";\n')
                entries = hint.split('^')
                for entry in entries:
                    parts = entry.split('~')
                    if len(parts) >= 3:
                        market = parts[0]  # sh or sz
                        code = parts[1]
                        name = parts[2]
                        # 优先匹配A股
                        if parts[-1] in ('GP-A', 'GP-A-KCB') and len(code) == 6 and code.isdigit():
                            return code
                # 如果没找到A股，取第一个结果
                for entry in entries:
                    parts = entry.split('~')
                    if len(parts) >= 3:
                        code = parts[1]
                        if len(code) == 6 and code.isdigit():
                            return code
        except Exception:
            pass
        return code_or_name

    def search_stock_data(self, stock_code: str) -> Dict[str, Any]:
        """搜索个股财务数据（使用同花顺接口，东方财富接口在服务器被封）"""
        try:
            import akshare as ak
            # 解析股票代码（支持中文名搜索）
            resolved_code = self._resolve_stock_code(stock_code)
            result = {"code": resolved_code, "query": stock_code, "financials": {}, "valuation": {}, "info": {}}

            # 使用同花顺财务摘要获取财务数据
            try:
                fin_df = ak.stock_financial_abstract_ths(symbol=resolved_code, indicator='按报告期')
                if fin_df is not None and len(fin_df) > 0:
                    latest = fin_df.iloc[-1]
                    # 报告期
                    report_date = str(latest.get('报告期', ''))
                    if report_date:
                        result["info"]["report_date"] = report_date

                    # ROE
                    roe = self._parse_number(latest.get('净资产收益率'))
                    if roe is not None:
                        result["financials"]["roe"] = round(float(roe), 2)

                    # ROA = 销售净利率 × 总资产周转率（近似用销售净利率）
                    net_margin = self._parse_number(latest.get('销售净利率'))
                    if net_margin is not None:
                        result["financials"]["net_profit_margin"] = round(float(net_margin), 2)

                    # 毛利率
                    gross_margin = self._parse_number(latest.get('销售毛利率'))
                    if gross_margin is not None:
                        result["financials"]["gross_margin"] = round(float(gross_margin), 2)

                    # 资产负债率
                    debt_ratio = self._parse_number(latest.get('资产负债率'))
                    if debt_ratio is not None:
                        result["financials"]["debt_ratio"] = round(float(debt_ratio), 2)

                    # 流动比率
                    current_ratio = self._parse_number(latest.get('流动比率'))
                    if current_ratio is not None:
                        result["financials"]["current_ratio"] = round(float(current_ratio), 2)

                    # 速动比率
                    quick_ratio = self._parse_number(latest.get('速动比率'))
                    if quick_ratio is not None:
                        result["financials"]["quick_ratio"] = round(float(quick_ratio), 2)

                    # 基本每股收益
                    eps = self._parse_number(latest.get('基本每股收益'))
                    if eps is not None:
                        result["financials"]["eps"] = round(float(eps), 2)

                    # 每股净资产
                    bvps = self._parse_number(latest.get('每股净资产'))
                    if bvps is not None:
                        result["financials"]["bvps"] = round(float(bvps), 2)

                    # 营业总收入同比增长率
                    rev_growth = self._parse_number(latest.get('营业总收入同比增长率'))
                    if rev_growth is not None:
                        result["financials"]["revenue_growth"] = round(float(rev_growth), 2)

                    # 净利润同比增长率
                    profit_growth = self._parse_number(latest.get('净利润同比增长率'))
                    if profit_growth is not None:
                        result["financials"]["profit_growth"] = round(float(profit_growth), 2)

                    # 营业总收入
                    revenue = self._parse_number(latest.get('营业总收入'))
                    if revenue is not None:
                        result["financials"]["revenue"] = round(float(revenue), 2)

                    # 净利润
                    net_profit = self._parse_number(latest.get('净利润'))
                    if net_profit is not None:
                        result["financials"]["net_profit"] = round(float(net_profit), 2)

                    # 每股经营现金流
                    ocfps = self._parse_number(latest.get('每股经营现金流'))
                    if ocfps is not None:
                        result["financials"]["ocfps"] = round(float(ocfps), 2)

                    # 产权比率
                    equity_ratio = self._parse_number(latest.get('产权比率'))
                    if equity_ratio is not None:
                        result["financials"]["equity_ratio"] = round(float(equity_ratio), 2)

                    # 存货周转率
                    inv_turnover = self._parse_number(latest.get('存货周转率'))
                    if inv_turnover is not None:
                        result["financials"]["inventory_turnover"] = round(float(inv_turnover), 2)

                    # 应收账款周转天数
                    ar_days = self._parse_number(latest.get('应收账款周转天数'))
                    if ar_days is not None:
                        result["financials"]["ar_turnover_days"] = round(float(ar_days), 2)

                    # 保存原始列名供前端展示
                    result["raw_columns"] = list(fin_df.columns)
                    result["raw_data_count"] = len(fin_df)
            except Exception:
                pass

            # 获取资金流向数据
            try:
                market = 'sh' if resolved_code.startswith('6') else 'sz'
                flow_df = ak.stock_individual_fund_flow(stock=resolved_code, market=market)
                if flow_df is not None and len(flow_df) > 0:
                    latest_flow = flow_df.iloc[-1]
                    for col in flow_df.columns:
                        col_str = str(col)
                        val = self._parse_number(latest_flow.get(col))
                        if val is None:
                            continue
                        if "主力" in col_str and "净流入" in col_str:
                            result["valuation"]["main_net_inflow"] = round(float(val), 2)
                        elif "超大单" in col_str and "净流入" in col_str:
                            result["valuation"]["super_large_net_inflow"] = round(float(val), 2)
            except Exception:
                pass

            # 获取实时行情（腾讯数据源）
            try:
                from services.akshare_service import get_realtime_quote
                quote = get_realtime_quote(resolved_code)
                if quote:
                    result["realtime"] = {
                        "name": quote.get("name"),
                        "price": quote.get("price"),
                        "change": quote.get("change"),
                        "change_pct": quote.get("change_pct"),
                        "open": quote.get("open"),
                        "high": quote.get("high"),
                        "low": quote.get("low"),
                        "yesterday_close": quote.get("yesterday_close"),
                        "volume": quote.get("volume"),
                        "turnover": quote.get("turnover"),
                        "pe_ratio": quote.get("pe_ratio"),
                        "pb_ratio": quote.get("pb_ratio"),
                        "total_market_cap": quote.get("total_market_cap"),
                        "circulating_market_cap": quote.get("circulating_market_cap"),
                        "amplitude": quote.get("amplitude"),
                        "timestamp": quote.get("timestamp"),
                    }
            except Exception:
                pass

            return result
        except Exception as e:
            return {"code": stock_code, "error": str(e)}

    def search_variable_data(self, variable_name: str) -> Dict[str, Any]:
        """按变量名搜索可用数据源"""
        var_sources = {
            "ROE": {"name": "净资产收益率", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "净资产收益率", "description": "企业净资产的收益率，衡量股东权益的收益水平"},
            "ROA": {"name": "销售净利率", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "销售净利率", "description": "净利润占营业收入比例，衡量盈利能力"},
            "资产负债率": {"name": "资产负债率", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "资产负债率", "description": "总负债/总资产，衡量企业偿债能力"},
            "企业规模": {"name": "企业规模(ln总资产)", "source": "CSMAR/Wind", "function": "需手动计算ln(总资产)", "description": "取总资产的自然对数，控制企业规模效应"},
            "盈利能力": {"name": "盈利能力(ROE)", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "净资产收益率", "description": "通常用ROE衡量"},
            "成长性": {"name": "营业收入增长率", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "营业总收入同比增长率", "description": "衡量企业成长能力"},
            "现金流": {"name": "每股经营现金流", "source": "AKShare", "function": "stock_financial_abstract_ths", "field": "每股经营现金流", "description": "经营活动产生的每股现金流"},
            "ESG评级": {"name": "ESG评级", "source": "非AKShare", "description": "需要CSMAR/Wind/Bloomberg等专业数据库，AKShare暂不支持"},
            "ESG": {"name": "ESG评级", "source": "非AKShare", "description": "需要CSMAR/Wind/Bloomberg等专业数据库"},
            "机构投资者持股": {"name": "机构投资者持股比例", "source": "AKShare", "function": "stock_report_fund_hold_detail", "description": "基金持仓占流通股比例"},
            "股权集中度": {"name": "前十大股东持股比例", "source": "AKShare", "function": "stock_gdfx_free_holding_detail_em", "description": "前十大股东合计持股占总股本比例"},
            "独立董事比例": {"name": "独立董事比例", "source": "非AKShare", "description": "需要CSMAR公司治理模块，AKShare暂不支持"},
            "董事会规模": {"name": "董事会人数", "source": "非AKShare", "description": "需要CSMAR公司治理模块"},
            "股价收益率": {"name": "股票收益率", "source": "AKShare", "function": "stock_individual_fund_flow", "field": "资金流向", "description": "主力/超大单资金净流入"},
        }

        # 模糊匹配
        for key, info in var_sources.items():
            if key in variable_name or variable_name in key:
                return {"variable": variable_name, "matched": key, **info}

        # 未匹配
        return {
            "variable": variable_name,
            "matched": None,
            "description": f"未找到'{variable_name}'的专用数据源，可尝试在AKShare财务指标中搜索",
            "suggestion": "建议使用以下变量：ROE、ROA、资产负债率、企业规模、盈利能力、成长性等",
        }

    def fetch_macro_data(self, indicators: List[str]) -> Dict[str, Any]:
        """获取宏观经济指标"""
        result = {}
        for indicator in indicators:
            try:
                import akshare as ak
                if indicator in ["GDP增速", "gdp"]:
                    df = ak.macro_china_gdp()
                    if len(df) > 0:
                        result["gdp"] = {
                            "dates": df["季度"].astype(str).tolist()[-8:],
                            "values": df["同比增长"].astype(float).tolist()[-8:],
                            "name": "GDP同比增速(%)",
                        }
                elif indicator in ["CPI", "cpi"]:
                    df = ak.macro_china_cpi_monthly()
                    if len(df) > 0:
                        result["cpi"] = {
                            "dates": df["月份"].astype(str).tolist()[-24:],
                            "values": df["全国-当月"].astype(float).tolist()[-24:],
                            "name": "CPI当月同比(%)",
                        }
                elif indicator in ["PMI", "pmi"]:
                    df = ak.macro_china_pmi()
                    if len(df) > 0:
                        result["pmi"] = {
                            "dates": df["日期"].astype(str).tolist()[-24:],
                            "values": df["制造业采购经理指数"].astype(float).tolist()[-24:],
                            "name": "PMI制造业",
                        }
                elif indicator in ["M2增速", "m2"]:
                    df = ak.macro_china_money_supply()
                    if len(df) > 0:
                        result["m2"] = {
                            "dates": df["月份"].astype(str).tolist()[-24:],
                            "values": df["M2-同比增长"].astype(float).tolist()[-24:],
                            "name": "M2同比增速(%)",
                        }
            except Exception:
                continue
        return result


research_crawler = ResearchCrawler()
