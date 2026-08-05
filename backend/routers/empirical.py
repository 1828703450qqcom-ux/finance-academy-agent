import json
import numpy as np
import pandas as pd
from fastapi import APIRouter, UploadFile, File
from schemas import EmpiricalRequest
from database import SessionLocal, ResearchProject
from crawlers.research_crawler import research_crawler

router = APIRouter(prefix="/api/empirical", tags=["empirical"])


def run_regression(data: list, dependent: str, independent: list, model_type: str,
                   robust_std: str = None, entity_col: str = None, time_col: str = None):
    """
    真实回归分析：OLS、固定效应、随机效应、GMM(2SLS)
    从真实残差计算诊断统计量
    """
    try:
        import statsmodels.api as sm
        from statsmodels.stats.stattools import durbin_watson, jarque_bera
        from statsmodels.stats.diagnostic import het_white

        df = pd.DataFrame(data)

        if dependent not in df.columns:
            return {"error": f"被解释变量 '{dependent}' 不在数据中"}
        for var in independent:
            if var not in df.columns:
                return {"error": f"变量 '{var}' 不在数据中"}

        y = df[dependent].astype(float)
        X = df[independent].astype(float)

        # ==================== 固定效应 ====================
        if model_type == "fixed":
            # 个体固定效应：加入firm_id虚拟变量
            entity_col_name = entity_col or "firm_id"
            if entity_col_name in df.columns:
                dummies = pd.get_dummies(df[entity_col_name], prefix="fe", drop_first=True).astype(float)
                X = pd.concat([X, dummies], axis=1)
            # 时间固定效应
            time_col_name = time_col or "year"
            if time_col_name in df.columns:
                time_dummies = pd.get_dummies(df[time_col_name], prefix="te", drop_first=True).astype(float)
                X = pd.concat([X, time_dummies], axis=1)

        # ==================== GMM/IV (2SLS近似) ====================
        elif model_type == "gmm":
            # 用第一个解释变量的滞后项作为工具变量
            if len(independent) >= 2 and entity_col and entity_col in df.columns:
                df_sorted = df.sort_values([entity_col, time_col or "year"])
                for var in independent[:1]:
                    df_sorted[f"{var}_lag1"] = df_sorted.groupby(entity_col)[var].shift(1)
                df_sorted = df_sorted.dropna(subset=[f"{independent[0]}_lag1"])
                if len(df_sorted) > 20:
                    iv_var = f"{independent[0]}_lag1"
                    # 2SLS: first stage
                    X_first = sm.add_constant(df_sorted[[iv_var] + independent[1:]].astype(float))
                    first_stage = sm.OLS(df_sorted[independent[0]].astype(float), X_first).fit()
                    df_sorted[f"{independent[0]}_hat"] = first_stage.fittedvalues
                    # 2SLS: second stage
                    X_iv = sm.add_constant(
                        df_sorted[[f"{independent[0]}_hat"] + independent[1:]].astype(float)
                    )
                    y = df_sorted[dependent].astype(float)
                    X = X_iv
            # fallback to OLS if IV fails
            if "X_iv" not in dir():
                X = sm.add_constant(X)

        # ==================== 随机效应/OLS ====================
        if model_type in ("ols", "random"):
            X = sm.add_constant(X)

        # 如果X还没加const
        if "const" not in X.columns and X.columns[0] != "const":
            X = sm.add_constant(X)

        # ==================== 拟合模型 ====================
        if robust_std and robust_std != "none":
            model = sm.OLS(y, X).fit(cov_type=robust_std)
        else:
            model = sm.OLS(y, X).fit()

        # ==================== 真实诊断统计量 ====================
        residuals = model.resid

        # Durbin-Watson (残差自相关)
        dw = float(durbin_watson(residuals))

        # Jarque-Bera (残差正态性)
        jb_stat, jb_pvalue, skew, kurtosis = jarque_bera(residuals)
        jb_pvalue = float(jb_pvalue)

        # White异方差检验
        try:
            white_stat, white_pvalue, _, _ = het_white(residuals, model.model.exog)
            white_pvalue = float(white_pvalue)
        except Exception:
            white_pvalue = 1.0

        # ==================== 系数结果 ====================
        coefficients = {}
        confidence_intervals = {}
        for var in model.params.index:
            ci_low, ci_high = model.conf_int().loc[var].tolist()
            coefficients[var] = {
                "coef": round(float(model.params[var]), 4),
                "std_err": round(float(model.bse[var]), 4),
                "t_stat": round(float(model.tvalues[var]), 4),
                "p_value": round(float(model.pvalues[var]), 4),
            }
            confidence_intervals[var] = {
                "low": round(float(ci_low), 4),
                "high": round(float(ci_high), 4),
            }

        # ==================== VIF检验 ====================
        vif_data = {}
        if len(independent) > 1:
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            X_vif = df[independent].astype(float)
            X_vif = sm.add_constant(X_vif)
            for i, var in enumerate(independent):
                try:
                    vif_val = variance_inflation_factor(X_vif.values, i + 1)
                    vif_data[var] = round(float(vif_val), 2)
                except Exception:
                    vif_data[var] = 0

        # ==================== 稳健性建议 ====================
        robustness = []
        max_vif = max(vif_data.values()) if vif_data else 0
        if max_vif > 10:
            robustness.append(f"VIF最大值为{max_vif}，存在严重多重共线性，建议删除变量或使用岭回归")
        elif max_vif > 5:
            robustness.append(f"VIF最大值为{max_vif}，存在一定程度多重共线性")
        if len(df) < 100:
            robustness.append("样本量较少(<100)，建议增加样本或使用Bootstrap标准误")
        if len(independent) > 3:
            robustness.append("解释变量较多，建议逐步回归或LASSO筛选")
        if white_pvalue < 0.05:
            robustness.append("White检验p<0.05，存在异方差，建议使用稳健标准误(HC0-HC3)")
        if abs(dw - 2) > 0.5:
            robustness.append(f"Durbin-Watson={dw:.2f}，可能存在残差自相关")
        robustness.append("建议进行替换变量稳健性检验")
        robustness.append("建议进行缩尾处理(1%/99%)后重新回归")
        robustness.append("建议进行Bootstrap重抽样(1000次)检验系数稳定性")

        # ==================== 残差数据（供前端绘图） ====================
        fitted_values = model.fittedvalues.tolist()
        residual_list = residuals.tolist()
        actual_list = y.tolist()

        # 残差分布（直方图用）
        hist_counts, hist_edges = np.histogram(residuals, bins=30)
        residual_hist = [
            {"edge": round(float(hist_edges[i]), 4), "count": int(hist_counts[i])}
            for i in range(len(hist_counts))
        ]

        return {
            "coefficients": coefficients,
            "confidence_intervals": confidence_intervals,
            "r_squared": round(float(model.rsquared), 4),
            "adj_r_squared": round(float(model.rsquared_adj), 4),
            "f_statistic": round(float(model.fvalue), 4),
            "p_value_f": round(float(model.f_pvalue), 4) if hasattr(model, "f_pvalue") else 0.0,
            "n_obs": int(model.nobs),
            "model_type": model_type,
            "robust_std": robust_std or "none",
            "vif": vif_data,
            "robustness_suggestions": robustness,
            "diagnostics": {
                "durbin_watson": round(dw, 4),
                "jarque_bera": round(jb_pvalue, 4),
                "white_test": round(white_pvalue, 4),
                "skewness": round(float(skew), 4),
                "kurtosis": round(float(kurtosis), 4),
            },
            "plot_data": {
                "fitted": [round(v, 4) for v in fitted_values],
                "residuals": [round(v, 4) for v in residual_list],
                "actual": [round(v, 4) for v in actual_list],
                "residual_hist": residual_hist,
            },
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/run")
async def run_empirical(req: EmpiricalRequest):
    import asyncio

    def _run():
        data_source_info = {"data_source": "user_upload", "data_note": "使用用户上传的数据"}
        if not req.data:
            data_result = research_crawler.generate_research_data(
                req.dependent_var,
                req.independent_vars,
                req.control_vars or [],
            )
            req.data = data_result["data"]
            data_source_info = {
                "data_source": data_result.get("data_source", "unknown"),
                "data_note": data_result.get("data_note", ""),
            }

        all_vars = req.independent_vars + (req.control_vars or [])
        result = run_regression(
            req.data, req.dependent_var, all_vars,
            req.model_type,
            robust_std=getattr(req, "robust_std", None),
            entity_col="firm_id",
            time_col="year",
        )

        result["data_source"] = data_source_info.get("data_source", "unknown")
        result["data_note"] = data_source_info.get("data_note", "")

        db = SessionLocal()
        try:
            project = ResearchProject(
                name=req.project_name,
                variables=json.dumps({
                    "dependent": req.dependent_var,
                    "independent": req.independent_vars,
                    "control": req.control_vars,
                }),
                model_type=req.model_type,
                results=json.dumps(result),
            )
            db.add(project)
            db.commit()
        finally:
            db.close()

        return result

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)


@router.post("/auto-detect")
async def auto_detect(project_name: str):
    """根据课题名称自动识别变量和推荐模型"""
    return research_crawler.auto_detect_variables(project_name)


@router.post("/fetch-data")
async def fetch_data(dependent_var: str, independent_vars: list, control_vars: list = None):
    """根据变量名获取数据"""
    data_result = research_crawler.generate_research_data(
        dependent_var, independent_vars, control_vars or [],
    )
    data = data_result["data"]
    # 返回前20行预览 + 统计摘要
    df = pd.DataFrame(data)
    preview = df.head(20).to_dict("records")
    desc = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        desc[col] = {
            "mean": round(float(df[col].mean()), 4),
            "std": round(float(df[col].std()), 4),
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "count": int(df[col].count()),
        }
    return {
        "data": data, "n_obs": len(data),
        "preview": preview, "description": desc,
        "columns": list(df.columns),
        "firms": int(df["firm_id"].nunique()) if "firm_id" in df.columns else 0,
        "years": sorted(df["year"].unique().tolist()) if "year" in df.columns else [],
        "data_source": data_result.get("data_source", "unknown"),
        "data_note": data_result.get("data_note", ""),
    }


@router.post("/search-stock")
async def search_stock(stock_code: str):
    """搜索个股财务数据"""
    import asyncio
    from cache import stock_cache

    cache_key = f"stock:{stock_code}"
    cached = stock_cache.get(cache_key)
    if cached is not None:
        return cached

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, research_crawler.search_stock_data, stock_code)
    if result:
        stock_cache.set(cache_key, result)
    return result


@router.post("/search-variable")
async def search_variable(variable_name: str):
    """按变量名搜索可用数据源"""
    return research_crawler.search_variable_data(variable_name)


@router.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    """上传CSV/Excel数据文件"""
    import io
    content = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            return {"error": "不支持的文件格式，请上传CSV或Excel"}
    except Exception as e:
        return {"error": f"文件解析失败: {str(e)}"}

    data = df.head(500).to_dict("records")
    preview = df.head(20).to_dict("records")
    desc = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        desc[col] = {
            "mean": round(float(df[col].mean()), 4),
            "std": round(float(df[col].std()), 4),
            "min": round(float(df[col].min()), 4),
            "max": round(float(df[col].max()), 4),
            "count": int(df[col].count()),
        }
    return {
        "data": data, "n_obs": len(data),
        "preview": preview, "description": desc,
        "columns": list(df.columns),
        "filename": file.filename,
    }


@router.post("/fetch-macro")
async def fetch_macro(indicators: list):
    """获取宏观经济数据"""
    return research_crawler.fetch_macro_data(indicators)


@router.get("/projects")
async def list_projects():
    db = SessionLocal()
    try:
        projects = db.query(ResearchProject).order_by(ResearchProject.created_at.desc()).all()
        return {
            "projects": [
                {
                    "id": p.id, "name": p.name, "model_type": p.model_type,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in projects
            ]
        }
    finally:
        db.close()


def result_to_latex(result: dict) -> str:
    if "error" in result:
        return f"% Error: {result['error']}"

    lines = [
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{{result.get('model_type', 'OLS')}回归结果}}",
        "\\begin{tabular}{lcccc}",
        "\\hline",
        "变量 & 系数 & 标准误 & t值 & p值 \\\\",
        "\\hline",
    ]
    for var, stats in result.get("coefficients", {}).items():
        sig = ""
        pv = stats.get("p_value", 1)
        if pv < 0.01:
            sig = "^{***}"
        elif pv < 0.05:
            sig = "^{**}"
        elif pv < 0.1:
            sig = "^{*}"
        lines.append(
            f"{var} & {stats['coef']:.4f}{sig} & ({stats['std_err']:.4f}) & [{stats['t_stat']:.4f}] & {stats['p_value']:.4f} \\\\"
        )
    lines.extend([
        "\\hline",
        f"$R^2$ & \\multicolumn{{4}}{{c}}{{{result.get('r_squared', 0):.4f}}} \\\\",
        f"Adj. $R^2$ & \\multicolumn{{4}}{{c}}{{{result.get('adj_r_squared', 0):.4f}}} \\\\",
        f"N & \\multicolumn{{4}}{{c}}{{{result.get('n_obs', 0)}}} \\\\",
        f"Model & \\multicolumn{{4}}{{c}}{{{result.get('model_type', 'OLS').upper()}}} \\\\",
        "\\hline",
        "\\multicolumn{5}{l}{\\footnotesize 注: $^{***}p<0.01, ^{**}p<0.05, ^{*}p<0.1$} \\\\",
        "\\end{tabular}",
        "\\end{table}",
    ])
    return "\n".join(lines)


@router.post("/export-latex")
async def export_latex(req: EmpiricalRequest):
    if not req.data:
        data_result = research_crawler.generate_research_data(
            req.dependent_var, req.independent_vars, req.control_vars or [],
        )
        req.data = data_result["data"]
    result = run_regression(
        req.data, req.dependent_var,
        req.independent_vars + (req.control_vars or []),
        req.model_type,
    )
    return {"latex": result_to_latex(result)}


# ==================== 科研助手端点 ====================

@router.post("/research-design")
async def research_design(
    research_question: str = "",
    data_type: str = "panel",
    unit: str = "enterprise",
    time_span: str = "",
    key_variables: str = "",
):
    """研究设计助手：根据研究问题推荐因果识别策略"""
    from services.research_guide import get_research_design
    return get_research_design(research_question, data_type, unit, time_span, key_variables)


@router.post("/empirical-guide")
async def empirical_guide(
    task: str = "回归代码",
    variables: str = "",
    design: str = "",
    outcome: str = "",
    treatment: str = "",
    controls: str = "",
):
    """实证操作指南：数据推荐/变量构造/描述统计/回归代码"""
    from services.research_guide import get_empirical_guide
    return get_empirical_guide(task, variables, design, outcome, treatment, controls)


@router.post("/paper-section")
async def paper_section(
    section: str = "引言",
    research_info: str = "",
    findings: str = "",
    contributions: str = "",
):
    """论文写作辅助：生成引言/摘要/综述/结论模板"""
    from services.research_guide import get_paper_section
    return get_paper_section(section, research_info, findings, contributions)
