from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# Chat
class ChatMessage(BaseModel):
    session_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage]


# Empirical
class EmpiricalRequest(BaseModel):
    project_name: str
    dependent_var: str
    independent_vars: List[str]
    control_vars: Optional[List[str]] = []
    model_type: str = "ols"
    robust_std: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None


class EmpiricalResult(BaseModel):
    coefficients: Dict[str, Dict[str, float]]
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    p_value_f: float
    n_obs: int
    model_type: str
    robustness_suggestions: List[str]


# Quant
class QuantRequest(BaseModel):
    strategy_type: str
    stock_pool: str
    start_date: str
    end_date: str
    initial_capital: float = 1000000
    rebalance_freq: str = "monthly"
    params: Optional[Dict[str, Any]] = None


class QuantResult(BaseModel):
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    equity_curve: List[Dict[str, Any]]
    trade_count: int


# Report
class ReportAnalysisRequest(BaseModel):
    report_id: int
    dimensions: List[str]


class ReportAnalysisResult(BaseModel):
    dupont: Optional[Dict[str, float]] = None
    revenue_growth: Optional[float] = None
    profitability: Optional[Dict[str, float]] = None
    solvency: Optional[Dict[str, float]] = None
    cashflow: Optional[Dict[str, float]] = None
    summary: str = ""


# Paper
class PaperSearchRequest(BaseModel):
    query: str
    sources: List[str] = ["openalex", "arxiv"]
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    fields: Optional[List[str]] = None


class PaperResult(BaseModel):
    title: str
    authors: str
    year: int
    source: str
    citation_count: int
    url: str
    abstract: str


# Macro
class MacroOverview(BaseModel):
    gdp_growth: Optional[float] = None
    cpi: Optional[float] = None
    pmi: Optional[float] = None
    social_financing: Optional[str] = None
    m2_growth: Optional[float] = None
    lpr: Optional[float] = None
    shanghai_index: Optional[float] = None
    shanghai_change: Optional[float] = None


class MacroChartData(BaseModel):
    dates: List[str]
    values: List[float]
    indicator: str
