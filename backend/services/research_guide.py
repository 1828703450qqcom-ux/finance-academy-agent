"""
科研助手知识模板引擎 v2
基于 AcadeMill-Econ 项目的方法论知识，提供研究设计、实证操作、论文写作的结构化指导
优化：模板占位符自动填充、变量模糊匹配、数据源智能推荐、按设计筛选回归代码
"""
from typing import Dict, Any, List, Optional
import re


# ==================== 数据源知识库 ====================
DATA_SOURCES = {
    "CSMAR": {
        "full_name": "国泰安数据库",
        "org": "深圳希施玛数据科技",
        "coverage": "上市公司财务/公司治理/IPO/关联交易/股权结构",
        "years": "1990—至今",
        "access": "高校机构订阅，校园IP内访问",
        "cost": "已订阅时免费",
        "url": "https://www.gtadata.com",
        "tags": ["财务", "公司治理", "IPO", "股权", "上市公司"],
    },
    "Wind": {
        "full_name": "万得数据库",
        "org": "上海万得信息技术",
        "coverage": "宏观/行业/公司/债券/基金/期权全覆盖",
        "years": "1990—至今",
        "access": "高校机构订阅",
        "cost": "已订阅时免费",
        "url": "https://www.wind.com.cn",
        "tags": ["宏观", "行业", "债券", "基金", "全品类"],
    },
    "CFPS": {
        "full_name": "中国家庭追踪调查",
        "org": "北京大学中国社会科学调查中心",
        "coverage": "家庭/个人微观数据（收入/消费/教育/健康/社保）",
        "years": "2010—（每两年一轮）",
        "access": "官网申请",
        "cost": "免费，审批约2周",
        "url": "http://opendata.pku.edu.cn",
        "tags": ["家庭", "个人", "收入", "消费", "教育", "微观"],
    },
    "CGSS": {
        "full_name": "中国综合社会调查",
        "org": "中国人民大学社会学系",
        "coverage": "个人层面（态度/行为/社会结构）",
        "years": "2003—（每两年一轮）",
        "access": "官网申请",
        "cost": "免费，审批约1-2周",
        "url": "http://cgss.ruc.edu.cn",
        "tags": ["个人", "态度", "行为", "社会", "微观"],
    },
    "CHIP": {
        "full_name": "中国家庭收入调查",
        "org": "北京师范大学中国收入分配研究院",
        "coverage": "家庭收入/消费/财产",
        "years": "1988/1995/2002/2007/2013/2018",
        "access": "官网申请",
        "cost": "免费，审批约2-4周",
        "url": "http:// CHIP.ruc.edu.cn",
        "tags": ["家庭", "收入", "财产", "分配"],
    },
    "PSRD": {
        "full_name": "中国县域统计年鉴",
        "org": "国家统计局",
        "coverage": "县级经济/人口/财政/工业",
        "years": "2000—至今",
        "access": "图书馆数据库或纸质版",
        "cost": "图书馆免费",
        "url": "",
        "tags": ["县域", "县级", "经济", "财政"],
    },
    "北大数字金融": {
        "full_name": "北京大学数字普惠金融指数",
        "org": "北京大学数字金融研究中心",
        "coverage": "县级数字金融发展（覆盖/使用/深度）",
        "years": "2011—2022",
        "access": "官网下载",
        "cost": "免费",
        "url": "https://dcf.pku.edu.cn",
        "tags": ["数字金融", "普惠金融", "县级", "金融科技"],
    },
    "专利数据": {
        "full_name": "CNRI专利数据库/国家知识产权局",
        "org": "国家知识产权局",
        "coverage": "专利申请/授权/引用/IPC分类",
        "years": "1985—至今",
        "access": "CNKI专利数据库或官网",
        "cost": "部分免费",
        "url": "https://www.cnipa.gov.cn",
        "tags": ["专利", "创新", "知识产权", "研发"],
    },
    "AKShare": {
        "full_name": "AKShare开源金融数据",
        "org": "开源社区",
        "coverage": "A股行情/财务/宏观/基金/债券/期货/外汇",
        "years": "各指标不同",
        "access": "Python pip install akshare",
        "cost": "免费开源",
        "url": "https://akshare.akfamily.xyz",
        "tags": ["A股", "行情", "财务", "宏观", "开源"],
    },
}


# ==================== 研究设计模板 ====================
IDENTIFICATION_STRATEGIES = {
    "DID": {
        "name": "双重差分法（DID, Difference-in-Differences）",
        "when": "存在外生政策冲击，部分个体受处理（处理组），部分不受（对照组）",
        "keywords": ["政策", "冲击", "改革", "实施", "DID", "双重差分", "before", "after",
                      "自然实验", "外生变化", "准实验", "试点", "规制", "法规"],
        "data_types": ["panel"],
        "requirements": [
            "外生政策冲击（冲击时点明确）",
            "处理组与对照组在冲击前具有可比性",
            "平行趋势假设：无处理时，两组结果变量趋势相同",
        ],
        "model": "Y_{it} = α + β · Treat_i × Post_t + γ X_{it} + μ_i + λ_t + ε_{it}",
        "fixed_effects": "个体固定效应(μ_i) + 时间固定效应(λ_t)",
        "cluster": "通常聚类到个体层级或更高地区层级",
        "tests": [
            "平行趋势检验：事件研究图，处理前各期系数应不显著",
            "安慰剂检验：时间安慰剂（提前处理时点）+ 个体安慰剂（随机处理组）",
            "动态效应：观察处理后各期系数变化趋势",
        ],
        "stata_code": """* 双向固定效应 DID
use "<your_panel.dta>", clear
xtset <id> <year>

* 主回归
reghdfe <outcome> treat_post <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store m1

* 事件研究图（平行趋势检验）
eventdd <outcome> <ctrls>, timevar(event_time) \\
    method(hdfe, absorb(<id> <year>) cluster(<cluster_var>)) \\
    lags(5) leads(5) graph_op(yline(0))""",
        "python_code": """# 双向固定效应 DID
import pandas as pd
from linearmodels.panel import PanelOLS

df = pd.read_stata("<your_panel.dta>")
df = df.set_index(["<id>", "<year>"])

model = PanelOLS.from_formula(
    "<outcome> ~ treat_post + <ctrl1> + <ctrl2> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)
print(model.summary)""",
        "references": [
            "Angrist and Pischke (2009) Mostly Harmless Econometrics, Princeton",
            "Callaway and Sant'Anna (2021) Journal of Econometrics",
            "Goodman-Bacon (2021) Journal of Econometrics",
        ],
    },
    "IV": {
        "name": "工具变量法（IV, Instrumental Variables）",
        "when": "核心解释变量与误差项相关（内生性：遗漏变量/反向因果/测量误差）",
        "keywords": ["内生", "因果", "工具变量", "IV", "遗漏变量", "反向因果",
                      "内生性", "选择偏差", "Heckman", "2SLS", "两阶段"],
        "data_types": ["panel", "cross_section"],
        "requirements": [
            "工具变量Z：与内生变量X相关（相关性条件）",
            "工具变量Z：与误差项ε不相关（排他性约束）",
        ],
        "model": "第一阶段: X_{it} = π Z_{it} + γ X_{it} + μ_i + λ_t + ν_{it}\n第二阶段: Y_{it} = β X̂_{it} + γ X_{it} + μ_i + λ_t + ε_{it}",
        "tests": [
            "第一阶段F统计量 > 10（排除弱工具变量）",
            "Hansen J检验（过度识别检验，若有多个工具变量）",
            "内生性检验：Hausman检验确认X确实内生",
        ],
        "stata_code": """* 工具变量法 (2SLS)
* 需安装: ssc install ivreg2
ivreg2 <outcome> <ctrls> (<endogenous> = <instrument>), \\
    first cluster(<cluster_var>) partial(<ctrls>)

* 检验弱工具变量
ivreg2 <outcome> <ctrls> (<endogenous> = <instrument>), first

* 过度识别检验（多工具变量时）
ivreg2 <outcome> <ctrls> (<endogenous> = <instruments>), cluster(<cluster_var>) orthog(<instruments>)""",
        "python_code": """# 工具变量法 (2SLS)
import statsmodels.api as sm

# 第一阶段
first_stage = sm.OLS(df["<endogenous>"], sm.add_constant(df[["<instrument>", "<ctrl1>"]])).fit()
df["<endogenous>_hat"] = first_stage.fittedvalues

# 第二阶段
second_stage = sm.OLS(df["<outcome>"], sm.add_constant(df[["<endogenous>_hat", "<ctrl1>"]])).fit()
print(second_stage.summary())""",
        "references": [
            "Wooldridge (2010) Econometric Analysis of Cross Section and Panel Data, MIT",
            "Angrist and Pischke (2009) Mostly Harmless Econometrics, Princeton",
        ],
    },
    "RDD": {
        "name": "断点回归（RDD, Regression Discontinuity Design）",
        "when": "处理分配由某个连续变量是否超过阈值决定（如考试分数线、政策门槛）",
        "keywords": ["断点", "门槛", "分数线", "RDD", "cutoff", "断点回归",
                      "阈值", "临界值", "资格", "达标"],
        "data_types": ["cross_section"],
        "requirements": [
            "精确断点：已知断点位置",
            "驱动力在断点处连续（不能在断点处跳跃）",
            "断点附近样本量充足",
        ],
        "model": "Y_i = α + β · D_i + f(X_i - c) + ε_i\n其中 D_i = 1(X_i ≥ c)，f(·) 为断点附近的多项式函数",
        "tests": [
            "McCrary密度检验：断点处密度不应跳跃（排除操纵）",
            "协变量平衡检验：断点处协变量应连续",
            "带宽敏感性：不同带宽下结果是否稳健",
        ],
        "stata_code": """* 断点回归 (RDD)
* 需安装: ssc install rdrobust
rdrobust <outcome> <running_var>, c(<cutoff>)
rdplot <outcome> <running_var>, c(<cutoff>)

* McCrary密度检验
* 需安装: ssc install rddensity
rddensity <running_var>, c(<cutoff>)""",
        "python_code": """# 断点回归 (RDD)
# 需安装: pip install rdrobust
from rdrobust import rdrobust, rdplot

result = rdrobust(df["<outcome>"], df["<running_var>"], c=<cutoff>)
print(result)
plot = rdplot(df["<outcome>"], df["<running_var>"], c=<cutoff>)""",
        "references": [
            "Lee and Lemieux (2010) Journal of Economic Literature",
            "Cattaneo, Idrobo and Titiunik (2020) Cambridge University Press",
        ],
    },
    "SC": {
        "name": "合成控制法（Synthetic Control）",
        "when": "只有一个处理单位（如单个省份/国家），需从多个对照单位中合成反事实",
        "keywords": ["合成控制", "SC", "一个省", "一个国家", "single",
                      "单个地区", "单个个体", "单一处理"],
        "data_types": ["panel"],
        "requirements": [
            "处理前有足够长的时间序列（通常≥10期）",
            "对照单位不受处理影响（SUTVA）",
            "合成控制能较好拟合处理前结果变量",
        ],
        "model": "Y_{1t}^{post} - Ŷ_{1t}^{post} = 处理效应\n其中 Ŷ_{1t} 是用加权对照单位合成的反事实",
        "tests": [
            "处理前拟合度（RMSPE）",
            "安慰剂检验：对每个对照单位做假处理，比较处理效应大小",
            "排列检验（Permutation test）",
        ],
        "stata_code": """* 合成控制法
* 需安装: ssc install synth
synth <outcome> <outcome>(<pre_period>) <ctrl1>(<pre_period>) <ctrl2>(<pre_period>), \\
    trunit(<treated_unit>) trperiod(<treatment_year>) \\
    xperiod(<pre_start> <pre_end>) figure""",
        "python_code": """# 合成控制法
# 需安装: pip install SyntheticControlMethods
from SyntheticControlMethods import Synth

sc = Synth(df, "<outcome>", "<id>", "<year>",
           time_predictor_prior=<pre_periods>,
           time_optimize_ssr=<pre_periods>,
           special_predictors=[("<ctrl1>", <pre_periods>, "mean")])
sc.original_data  # 查看权重""",
        "references": [
            "Abadie and Gardeazabal (2003) American Economic Review",
            "Abadie, Diamond and Hainmueller (2010) Journal of the American Statistical Association",
        ],
    },
    "EventStudy": {
        "name": "事件研究法（Event Study）",
        "when": "需要动态估计处理效应的时间路径（DID的扩展）",
        "keywords": ["动态效应", "事件研究", "event study", "时间路径", "处理效应动态"],
        "data_types": ["panel"],
        "requirements": [
            "同DID，额外需要明确事件窗口期",
        ],
        "model": "Y_{it} = α + Σ_k β_k · D_{i,t-k} + γ X_{it} + μ_i + λ_t + ε_{it}\n其中 D_{i,t-k} 为相对事件时间的虚拟变量",
        "fixed_effects": "个体固定效应(μ_i) + 时间固定效应(λ_t)",
        "cluster": "通常聚类到个体层级",
        "tests": [
            "处理前各期系数β_k应不显著（平行趋势）",
            "处理后系数变化趋势（动态效应）",
        ],
        "stata_code": """* 事件研究图
* 需安装: ssc install eventdd
eventdd <outcome> <ctrls>, timevar(event_time) \\
    method(hdfe, absorb(<id> <year>) cluster(<cluster_var>)) \\
    lags(5) leads(5) graph_op(yline(0))""",
        "python_code": """# 事件研究：手动生成相对时间虚拟变量
import pandas as pd
import numpy as np

df["event_time"] = df["<year>"] - df["<treat_year>"]
for k in range(-5, 6):
    if k != 0:
        df[f"lead_lag_{k}"] = ((df["event_time"] == k) & (df["treat"] == 1)).astype(int)

# 回归（以-1期为基期）
import statsmodels.formula.api as smf
leads_lags = "+".join([f"lead_lag_{k}" for k in range(-5, 6) if k != -1])
model = smf.ols(f"<outcome> ~ {leads_lags} + <ctrls> + C(<id>) + C(<year>)", data=df).fit()
print(model.summary())""",
        "references": [
            "Angrist and Pischke (2009) Mostly Harmless Econometrics",
            "Autor (2003) Journal of Labor Economics",
        ],
    },
}


# ==================== 回归代码模板（按设计类型分类） ====================
REGRESSION_TEMPLATES = {
    "主回归": {
        "stata": """* ========== 主回归 ==========
use "<your_panel.dta>", clear
xtset <id> <year>

* 双向固定效应 OLS
reghdfe <outcome> <treatment> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store m1
esttab m1, b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) stats(N r2_a)""",
        "python": """# ========== 主回归 ==========
import pandas as pd
from linearmodels.panel import PanelOLS

df = pd.read_stata("<your_panel.dta>")
df = df.set_index(["<id>", "<year>"])

model = PanelOLS.from_formula(
    "<outcome> ~ <treatment> + <ctrl1> + <ctrl2> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)
print(model.summary)""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
    "平行趋势检验": {
        "stata": """* ========== 平行趋势检验（事件研究） ==========
* 生成相对事件时间
gen event_time = <year> - <treat_year>

* 事件研究回归
eventdd <outcome> <ctrls>, timevar(event_time) \\
    method(hdfe, absorb(<id> <year>) cluster(<cluster_var>)) \\
    lags(5) leads(5) graph_op(yline(0) xlabel(-5(1)5))""",
        "python": """# ========== 平行趋势检验 ==========
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

df["event_time"] = df["<year>"] - df["<treat_year>"]
for k in range(-5, 6):
    if k != -1:
        df[f"et_{k}"] = ((df["event_time"] == k) & (df["treat"] == 1)).astype(int)

et_vars = "+".join([f"et_{k}" for k in range(-5, 6) if k != -1])
model = smf.ols(f"<outcome> ~ {et_vars} + <ctrls> + C(<id>) + C(<year>)", data=df).fit()
print(model.summary())""",
        "designs": ["DID", "EventStudy"],
    },
    "替换变量稳健性": {
        "stata": """* ========== 稳健性检验：替换变量 ==========
* 替换被解释变量
reghdfe <outcome_alt> <treatment> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store r_y_alt

* 替换核心解释变量度量
reghdfe <outcome> <treatment_alt> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store r_x_alt

esttab m1 r_y_alt r_x_alt, b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) stats(N r2_a)""",
        "python": """# ========== 稳健性检验：替换变量 ==========
model_alt_y = PanelOLS.from_formula(
    "<outcome_alt> ~ <treatment> + <ctrls> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)

model_alt_x = PanelOLS.from_formula(
    "<outcome> ~ <treatment_alt> + <ctrls> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
    "替换样本稳健性": {
        "stata": """* ========== 稳健性检验：替换样本 ==========
* 剔除直辖市
reghdfe <outcome> <treatment> <ctrls> if !inlist(<province>, "北京","上海","天津","重庆"), \\
    absorb(<id> <year>) cluster(<cluster_var>)
est store r_drop_munic

* 剔除金融危机年份
reghdfe <outcome> <treatment> <ctrls> if <year> != 2008 & <year> != 2009, \\
    absorb(<id> <year>) cluster(<cluster_var>)
est store r_drop_crisis

* 缩尾处理后重跑
winsor2 <outcome> <ctrls>, cuts(1 99) replace
reghdfe <outcome> <treatment> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store r_winsor""",
        "python": """# ========== 稳健性检验：替换样本 ==========
from scipy.stats.mstats import winsorize

# 剔除直辖市
mask = ~df["<province>"].isin(["北京", "上海", "天津", "重庆"])
model_drop = PanelOLS.from_formula(
    "<outcome> ~ <treatment> + <ctrls> + EntityEffects + TimeEffects",
    data=df[mask]
).fit(cov_type="clustered", cluster_entity=True)

# 缩尾处理
for col in ["<outcome>", "<ctrl1>"]:
    df[col] = winsorize(df[col], limits=[0.01, 0.01])""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
    "安慰剂检验": {
        "stata": """* ========== 安慰剂检验 ==========
* 时间安慰剂：把处理时点提前3年
gen treat_post_placebo = (<year> >= <treat_year> - 3) & treat == 1
reghdfe <outcome> treat_post_placebo <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store r_placebo_time

* 个体安慰剂：随机抽取"伪处理组"（需安装 randtreat）
* ssc install randtreat
randtreat, generate(placebo_treat) method(random) ///
    setseed(12345) multiple(500)
* 对每次随机分组跑回归，观察系数分布""",
        "python": """# ========== 安慰剂检验 ==========
import numpy as np

# 时间安慰剂：处理时点提前3年
df["treat_post_placebo"] = ((df["<year>"] >= <treat_year> - 3) & (df["treat"] == 1)).astype(int)
model_placebo = PanelOLS.from_formula(
    "<outcome> ~ treat_post_placebo + <ctrls> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)

# 个体安慰剂：随机分组500次
np.random.seed(12345)
placebo_coefs = []
for _ in range(500):
    df["placebo_treat"] = 0
    treated_units = np.random.choice(df["<id>"].unique(), size=n_treated, replace=False)
    df.loc[df["<id>"].isin(treated_units), "placebo_treat"] = 1
    df["placebo_tp"] = df["placebo_treat"] * (df["<year>"] >= <treat_year>).astype(int)
    m = smf.ols("<outcome> ~ placebo_tp + <ctrls> + C(<id>) + C(<year>)", data=df).fit()
    placebo_coefs.append(m.params["placebo_tp"])""",
        "designs": ["DID", "EventStudy"],
    },
    "异质性分析": {
        "stata": """* ========== 异质性分析 ==========
* 交互项法
gen treat_x_group = treat_post * <group_var>
reghdfe <outcome> treat_post treat_x_group <group_var> <ctrls>, \\
    absorb(<id> <year>) cluster(<cluster_var>)
est store r_hetero

* 分样本回归
reghdfe <outcome> <treatment> <ctrls> if <group_var> == 1, absorb(<id> <year>) cluster(<cluster_var>)
est store r_sub1
reghdfe <outcome> <treatment> <ctrls> if <group_var> == 0, absorb(<id> <year>) cluster(<cluster_var>)
est store r_sub2

esttab r_sub1 r_sub2, b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) mtitles("处理组" "对照组")""",
        "python": """# ========== 异质性分析 ==========
df["treat_x_group"] = df["treat_post"] * df["<group_var>"]
model_hetero = PanelOLS.from_formula(
    "<outcome> ~ treat_post + treat_x_group + <group_var> + <ctrls> + EntityEffects + TimeEffects",
    data=df
).fit(cov_type="clustered", cluster_entity=True)

for val in [0, 1]:
    sub = df[df["<group_var>"] == val]
    m = PanelOLS.from_formula(
        "<outcome> ~ <treatment> + <ctrls> + EntityEffects + TimeEffects",
        data=sub
    ).fit(cov_type="clustered", cluster_entity=True)
    print(f"Group {val}: {m.summary}")""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
    "机制检验": {
        "stata": """* ========== 机制检验（中介效应） ==========
* Step 1: X → Y（主回归，已做）
* Step 2: X → M（中介变量）
reghdfe <mediator> <treatment> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store m_mediator

* Step 3: X + M → Y
reghdfe <outcome> <treatment> <mediator> <ctrls>, absorb(<id> <year>) cluster(<cluster_var>)
est store m_full

esttab m1 m_mediator m_full, b(3) se(3) star(* 0.1 ** 0.05 *** 0.01) \\
    mtitles("主回归" "X→M" "X+M→Y")

* Sobel检验（备查）
* ssc install sgmediation
sgmediation <outcome>, mv(<mediator>) iv(<treatment>) cv(<ctrls>)""",
        "python": """# ========== 机制检验（中介效应） ==========
import statsmodels.formula.api as smf

# Step 2: X → M
model_m = smf.ols("<mediator> ~ <treatment> + <ctrls> + C(<id>) + C(<year>)", data=df).fit()
print("Step 2 (X→M):", model_m.summary())

# Step 3: X + M → Y
model_full = smf.ols("<outcome> ~ <treatment> + <mediator> + <ctrls> + C(<id>) + C(<year>)", data=df).fit()
print("Step 3 (X+M→Y):", model_full.summary())""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
    "描述统计": {
        "stata": """* ========== 描述统计 ==========
* 安装: ssc install estout
local yvar <outcome>
local xvar <treatment>
local ctrls <ctrl1> <ctrl2>

* 描述统计表
estpost summarize `yvar' `xvar' `ctrls', detail
esttab using "tab_desc.rtf", ///
    cells("count mean(fmt(3)) sd(fmt(3)) min(fmt(2)) max(fmt(2))") ///
    nomtitle nonumber replace

* 相关系数矩阵
asdoc pwcorr `yvar' `xvar' `ctrls', star(.05) replace

* 处理组vs对照组均值差异
foreach v of varlist `yvar' `ctrls' {
    ttest `v', by(treat)
}""",
        "python": """# ========== 描述统计 ==========
import pandas as pd

cols = ["<outcome>", "<treatment>", "<ctrl1>", "<ctrl2>"]
desc = df[cols].agg(["count", "mean", "std", "min", "max"]).T.round(3)
desc.to_csv("tab_desc.csv")

corr = df[cols].corr().round(3)
corr.to_csv("tab_corr.csv")

for col in cols:
    print(f"\\n=== {col} ===")
    print(df.groupby("treat")[col].describe())""",
        "designs": ["DID", "IV", "RDD", "SC", "EventStudy", "OLS"],
    },
}


# ==================== 论文写作模板 ====================
PAPER_WRITING_TEMPLATES = {
    "引言": {
        "structure": "五段式引言：背景 → 缺口 → 做法 → 发现 → 贡献",
        "template": """一、研究背景（1-2段）
{background}

二、现有文献与研究缺口（1段）
现有文献在以下方面存在不足：
{gap}

三、本文做法（1段）
本文以{unit}为研究对象，采用{method}方法，利用{data_source}数据，
研究{research_question}。

四、主要发现（1-2段）
研究发现：
{findings}

五、边际贡献（1段）
本文的边际贡献体现在以下方面：
{contributions}""",
        "tips": [
            "第一段用宏观背景引入，最后一句点明研究问题",
            "文献综述要指出gap，不能只罗列",
            "做法部分要写具体（处理组定义、模型设定）",
            "发现要有具体数字支撑",
            "贡献要与gap一一对应",
        ],
    },
    "摘要": {
        "structure": "背景(1句) → 问题(1句) → 方法(1-2句) → 发现(2-3句) → 意义(1句)",
        "template": """【中文摘要模板】

{background}。然而，现有研究对{gap}尚未给出明确答案。本文基于{data_description}，
采用{method}方法，实证检验了{research_question}。研究发现：（1）{finding1}；
（2）{finding2}；（3）{finding3}。机制分析表明{mechanism}。本文的研究为{implication}
提供了经验证据，对{policy}具有参考意义。

【关键词】{keyword1}；{keyword2}；{keyword3}；{keyword4}

【JEL Classification】{jel_codes}""",
        "tips": [
            "中英文摘要内容一致",
            "背景一句话，不要展开",
            "方法和发现要具体",
            "关键词3-5个，按重要性排列",
        ],
    },
    "文献综述": {
        "structure": "按主题分组，每组：已有研究 → 不足 → 本文如何弥补",
        "template": """一、{theme1}的研究
{existing_studies_theme1}
上述研究为理解{topic}提供了重要基础，但在{gap1}方面仍有不足。

二、{theme2}的研究
{existing_studies_theme2}
综合来看，{gap_summary}。

三、文献评述与本文定位
现有文献的不足主要体现在：
{gaps_summary}
本文试图在以下方面做出弥补：{positioning}""",
        "tips": [
            "按主题分组，不要按作者罗列",
            "每段结尾指出不足",
            "最后总结gap并引出本文",
            "引用近3-5年文献为主",
        ],
    },
    "结论": {
        "structure": "四段式：发现 → 启示 → 局限 → 未来",
        "template": """一、研究发现
本文以{unit}为样本，采用{method}方法研究{question}，主要发现如下：
（1）{finding1}；（2）{finding2}；（3）{finding3}。

二、政策启示
基于上述发现，本文提出以下政策建议：
（1）{policy1}；（2）{policy2}；（3）{policy3}。

三、研究局限与未来方向
本研究仍存在以下不足：
（1）{limitation1}；（2）{limitation2}。
未来研究可从以下方向拓展：{future_directions}。""",
        "tips": [
            "发现要与引言呼应",
            "政策建议要基于发现，不要空泛",
            "局限要诚实但不要自毁",
            "未来方向要具体可操作",
        ],
    },
}


# ==================== 变量构造知识库（扩展版） ====================
VARIABLE_CONSTRUCTION = {
    "企业规模": {
        "concept": "企业规模",
        "measure": "总资产的自然对数",
        "formula": "ln(总资产)",
        "source": "CSMAR/Wind 资产负债表",
        "pitfalls": ["注意总资产为0或负数的情况", "单位统一（元→万元→亿元）"],
        "stata": 'gen ln_assets = ln(total_assets)\nlabel var ln_assets "企业规模(ln总资产)"',
        "python": 'df["ln_assets"] = np.log(df["total_assets"])',
        "aliases": ["规模", "size", "资产规模", "企业大小", "公司规模"],
    },
    "资产负债率": {
        "concept": "财务杠杆",
        "measure": "总负债/总资产",
        "formula": "总负债 / 总资产 × 100%",
        "source": "CSMAR/Wind 资产负债表",
        "pitfalls": ["注意分母为0", "百分比还是小数口径"],
        "stata": 'gen debt_ratio = total_liab / total_assets * 100\nlabel var debt_ratio "资产负债率(%)"',
        "python": 'df["debt_ratio"] = df["total_liab"] / df["total_assets"] * 100',
        "aliases": ["杠杆", "leverage", "负债率", "资本结构", "财务杠杆", "lev"],
    },
    "ROE": {
        "concept": "净资产收益率",
        "measure": "净利润/股东权益",
        "formula": "净利润 / 平均股东权益 × 100%",
        "source": "CSMAR/Wind 利润表+资产负债表",
        "pitfalls": ["用加权ROE还是摊薄ROE", "注意ST公司异常值"],
        "stata": 'gen roe = net_profit / avg_equity * 100\nlabel var roe "ROE(%)"',
        "python": 'df["roe"] = df["net_profit"] / df["avg_equity"] * 100',
        "aliases": ["净资产收益率", "roe", "股东回报", "盈利能力"],
    },
    "托宾Q": {
        "concept": "企业价值",
        "measure": "(市值+负债)/总资产",
        "formula": "(股票市值 + 总负债) / 总资产",
        "source": "CSMAR/Wind 资产负债表+股票行情",
        "pitfalls": ["非流通股用每股净资产而非市价", "市值取年末还是平均"],
        "stata": 'gen tobins_q = (market_cap + total_liab) / total_assets\nlabel var tobins_q "托宾Q"',
        "python": 'df["tobins_q"] = (df["market_cap"] + df["total_liab"]) / df["total_assets"]',
        "aliases": ["tobin", "tobins_q", "企业价值", "市场价值", "估值"],
    },
    "机构投资者持股": {
        "concept": "机构投资者持股比例",
        "measure": "机构持股数/总股本",
        "formula": "机构投资者持股合计 / 总股本 × 100%",
        "source": "CSMAR/Wind 股东研究",
        "pitfalls": ["季度数据还是半年度数据", "基金+QFII+券商+保险合计"],
        "stata": 'gen inst_pct = inst_holders / total_shares * 100\nlabel var inst_pct "机构持股比例(%)"',
        "python": 'df["inst_pct"] = df["inst_holders"] / df["total_shares"] * 100',
        "aliases": ["机构持股", "institutional", "机构投资", "基金持股"],
    },
    "股权集中度": {
        "concept": "股权集中度",
        "measure": "前十大股东持股比例合计",
        "formula": "前十大股东持股数 / 总股本 × 100%",
        "source": "CSMAR/Wind 股东研究",
        "pitfalls": ["注意季度披露时间差"],
        "stata": 'gen top10_pct = top10_holders / total_shares * 100\nlabel var top10_pct "前十大股东持股比例(%)"',
        "python": 'df["top10_pct"] = df["top10_holders"] / df["total_shares"] * 100',
        "aliases": ["股权集中", "concentration", "大股东", "股权结构"],
    },
    "数字化转型": {
        "concept": "企业数字化转型程度",
        "measure": "年报关键词词频",
        "formula": "ln(数字化相关关键词词频+1)",
        "source": "CSMAR年报文本 / 手工提取",
        "pitfalls": ["不同年份关键词列表可能不同", "词频受年报长度影响"],
        "stata": '* 需要先用Python做文本分析\ngen digital_score = ln(digital_count + 1)\nlabel var digital_score "数字化转型"',
        "python": 'df["digital_score"] = np.log(df["digital_count"] + 1)',
        "aliases": ["数字化", "digital", "数字经济", "信息化", "智能化"],
    },
    "盈利能力": {
        "concept": "企业盈利能力",
        "measure": "净利润/营业收入",
        "formula": "净利润 / 营业收入 × 100%",
        "source": "CSMAR/Wind 利润表",
        "pitfalls": ["营业利润vs净利润", "扣非后净利润"],
        "stata": 'gen profit_margin = net_profit / revenue * 100\nlabel var profit_margin "净利率(%)"',
        "python": 'df["profit_margin"] = df["net_profit"] / df["revenue"] * 100',
        "aliases": ["利润率", "profit", "净利率", "profit_margin", "营业利润率"],
    },
    "成长性": {
        "concept": "企业成长性",
        "measure": "营业收入同比增长率",
        "formula": "(本期营业收入 - 上期营业收入) / 上期营业收入 × 100%",
        "source": "CSMAR/Wind 利润表",
        "pitfalls": ["注意基期为0的情况", "季度vs年度数据"],
        "stata": 'gen revenue_growth = (revenue - L.revenue) / L.revenue * 100\nlabel var revenue_growth "营收增长率(%)"',
        "python": 'df["revenue_growth"] = df.groupby("stock_code")["revenue"].pct_change() * 100',
        "aliases": ["growth", "增长率", "growth_rate", "营收增长", "收入增长"],
    },
    "现金流": {
        "concept": "企业现金流状况",
        "measure": "经营性现金流/总资产",
        "formula": "经营活动现金流量净额 / 总资产",
        "source": "CSMAR/Wind 现金流量表+资产负债表",
        "pitfalls": ["直接法vs间接法", "注意大额非经常性现金流"],
        "stata": 'gen cfo_ratio = cfo / total_assets\nlabel var cfo_ratio "经营现金流/总资产"',
        "python": 'df["cfo_ratio"] = df["cfo"] / df["total_assets"]',
        "aliases": ["现金流", "cashflow", "cfo", "经营现金流", "现金流量"],
    },
    "企业年龄": {
        "concept": "企业成立年限",
        "measure": "观测年份 - 成立年份",
        "formula": "当前年份 - 成立年份",
        "source": "CSMAR/Wind 公司治理",
        "pitfalls": ["注意成立日期格式", "重组后是否重新计算"],
        "stata": 'gen firm_age = <year> - founded_year\nlabel var firm_age "企业年龄(年)"',
        "python": 'df["firm_age"] = df["year"] - df["founded_year"]',
        "aliases": ["年龄", "age", "成立年限", "上市年限", "公司年龄"],
    },
    "股权性质": {
        "concept": "企业所有权性质",
        "measure": "国有企业=1，非国有企业=0",
        "formula": "SOE虚拟变量",
        "source": "CSMAR/Wind 公司治理",
        "pitfalls": ["实际控制人变更", "混合所有制判断标准"],
        "stata": 'gen soe = (ctrl_owner == "国有")\nlabel var soe "股权性质(国企=1)"',
        "python": 'df["soe"] = (df["ctrl_owner"] == "国有").astype(int)',
        "aliases": ["soe", "国企", "国有", "所有制", "产权性质", "国有企业"],
    },
}


# ==================== 变量→数据源映射 ====================
VARIABLE_DATA_MAP = {
    "财务": ["CSMAR", "Wind", "AKShare"],
    "公司治理": ["CSMAR", "Wind"],
    "收入": ["CFPS", "CHIP", "CGSS"],
    "消费": ["CFPS", "CHIP"],
    "教育": ["CFPS", "CGSS"],
    "家庭": ["CFPS", "CHIP"],
    "个人": ["CFPS", "CGSS"],
    "宏观": ["Wind", "AKShare"],
    "A股": ["AKShare", "CSMAR", "Wind"],
    "行情": ["AKShare", "Wind"],
    "县域": ["PSRD", "北大数字金融"],
    "数字金融": ["北大数字金融"],
    "专利": ["专利数据"],
    "创新": ["专利数据"],
    "债券": ["Wind"],
    "基金": ["Wind"],
}


# ==================== 主要功能函数 ====================

def _fuzzy_match_variable(name: str) -> Optional[str]:
    """模糊匹配变量名，支持别名和部分匹配"""
    name_lower = name.lower().strip()
    # 精确匹配
    if name in VARIABLE_CONSTRUCTION:
        return name
    # 别名匹配
    for var_name, info in VARIABLE_CONSTRUCTION.items():
        aliases = info.get("aliases", [])
        for alias in aliases:
            if alias.lower() == name_lower or name_lower in alias.lower() or alias.lower() in name_lower:
                return var_name
    # 部分匹配
    for var_name in VARIABLE_CONSTRUCTION:
        if name_lower in var_name.lower() or var_name.lower() in name_lower:
            return var_name
    return None


def _fill_template(template: str, replacements: Dict[str, str]) -> str:
    """填充模板中的 {placeholder}，未提供的保留原文"""
    result = template
    for key, value in replacements.items():
        if value:
            result = result.replace("{" + key + "}", value)
    return result


def _match_data_sources(variables: str) -> List[Dict[str, Any]]:
    """根据变量列表智能推荐数据源"""
    var_list = [v.strip().lower() for v in variables.split(",") if v.strip()]
    source_scores: Dict[str, int] = {}

    for var in var_list:
        # 关键词匹配
        for tag, sources in VARIABLE_DATA_MAP.items():
            if tag in var or var in tag:
                for src in sources:
                    source_scores[src] = source_scores.get(src, 0) + 2

        # 直接匹配变量构造库中的source字段
        matched = _fuzzy_match_variable(var)
        if matched:
            info = VARIABLE_CONSTRUCTION[matched]
            src_text = info.get("source", "")
            for src_key in DATA_SOURCES:
                if src_key in src_text:
                    source_scores[src_key] = source_scores.get(src_key, 0) + 3

    # 按分数排序
    ranked = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
    result = []
    for src_key, score in ranked[:5]:
        if src_key in DATA_SOURCES:
            entry = dict(DATA_SOURCES[src_key])
            entry["relevance_score"] = score
            entry["key"] = src_key
            result.append(entry)

    # 如果没有匹配，返回默认推荐
    if not result:
        for src_key in ["CSMAR", "Wind", "AKShare"]:
            entry = dict(DATA_SOURCES[src_key])
            entry["relevance_score"] = 0
            entry["key"] = src_key
            result.append(entry)

    return result


def get_research_design(
    research_question: str,
    data_type: str = "panel",
    unit: str = "enterprise",
    time_span: str = "",
    key_variables: str = "",
) -> Dict[str, Any]:
    """根据研究问题推荐识别策略（增强版：考虑数据类型、变量、关键词）"""
    q = research_question.lower()
    var_text = key_variables.lower() if key_variables else ""
    full_text = q + " " + var_text

    # 关键词匹配得分
    scores = {}
    for strategy_key, strategy in IDENTIFICATION_STRATEGIES.items():
        keywords = strategy.get("keywords", [])
        score = sum(2 if kw in q else 1 for kw in keywords if kw in full_text)
        scores[strategy_key] = score

    # 数据类型加成
    for strategy_key, strategy in IDENTIFICATION_STRATEGIES.items():
        compatible_types = strategy.get("data_types", [])
        if data_type in compatible_types:
            scores[strategy_key] = scores.get(strategy_key, 0) + 1

    # 单位类型加成：省份→SC，企业→DID/IV
    if unit == "province":
        scores["SC"] = scores.get("SC", 0) + 2
        scores["DID"] = scores.get("DID", 0) + 1
    elif unit == "enterprise":
        scores["DID"] = scores.get("DID", 0) + 1
        scores["IV"] = scores.get("IV", 0) + 1

    # 时间跨度加成：短面板→DID，长面板→SC
    if time_span:
        try:
            parts = time_span.replace("—", "-").replace("–", "-").split("-")
            if len(parts) == 2:
                years = int(parts[1]) - int(parts[0])
                if years >= 15:
                    scores["SC"] = scores.get("SC", 0) + 1
                if years >= 5:
                    scores["DID"] = scores.get("DID", 0) + 1
        except (ValueError, IndexError):
            pass

    sorted_strategies = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 生成推荐（至少推荐2个，最多3个）
    recommendations = []
    for strategy_key, score in sorted_strategies[:3]:
        if score > 0 or strategy_key == "DID":
            strategy = IDENTIFICATION_STRATEGIES[strategy_key]
            recommendations.append({
                "strategy": strategy_key,
                "name": strategy["name"],
                "score": score,
                "when": strategy["when"],
                "requirements": strategy["requirements"],
                "model": strategy["model"],
                "fixed_effects": strategy.get("fixed_effects", ""),
                "tests": strategy["tests"],
                "stata_code": strategy["stata_code"],
                "python_code": strategy["python_code"],
                "references": strategy["references"],
            })

    # 如果都没有得分，至少推荐DID
    if not recommendations:
        strategy = IDENTIFICATION_STRATEGIES["DID"]
        recommendations.append({
            "strategy": "DID",
            "name": strategy["name"],
            "score": 0,
            "when": strategy["when"],
            "requirements": strategy["requirements"],
            "model": strategy["model"],
            "fixed_effects": strategy.get("fixed_effects", ""),
            "tests": strategy["tests"],
            "stata_code": strategy["stata_code"],
            "python_code": strategy["python_code"],
            "references": strategy["references"],
        })

    # 数据类型建议
    data_type_suggestions = []
    if data_type == "cross_section" and scores.get("DID", 0) > scores.get("RDD", 0):
        data_type_suggestions.append("DID需要面板数据，建议使用Panel Data")
    if data_type == "time_series" and scores.get("SC", 0) > 0:
        data_type_suggestions.append("合成控制法适合面板数据（多地区时间序列）")

    return {
        "research_question": research_question,
        "data_type": data_type,
        "unit": unit,
        "time_span": time_span,
        "key_variables": key_variables,
        "recommendations": recommendations,
        "primary": recommendations[0] if recommendations else None,
        "data_type_suggestions": data_type_suggestions,
    }


def get_empirical_guide(
    task: str,
    variables: str = "",
    design: str = "",
    outcome: str = "",
    treatment: str = "",
    controls: str = "",
) -> Dict[str, Any]:
    """获取实证操作指南（增强版：按设计筛选、模糊匹配）"""
    if task == "回归代码":
        # 按设计类型筛选模板
        design_upper = design.upper().replace("OLS", "OLS").replace("双重差分", "DID")
        filtered_templates = {}
        for name, tpl in REGRESSION_TEMPLATES.items():
            allowed_designs = tpl.get("designs", [])
            if not design or design_upper in allowed_designs or design in allowed_designs:
                filtered_templates[name] = tpl

        ctrl_list = [c.strip() for c in controls.split(",") if c.strip()] if controls else ["<ctrl1>", "<ctrl2>"]
        return {
            "task": task,
            "design": design,
            "templates": filtered_templates,
            "variable_mapping": {
                "outcome": outcome or "<outcome>",
                "treatment": treatment or "<treatment>",
                "controls": ctrl_list,
            },
        }
    elif task == "变量构造":
        var_list = [v.strip() for v in variables.split(",") if v.strip()]
        result = {}
        suggestions = []
        for var in var_list:
            matched = _fuzzy_match_variable(var)
            if matched:
                result[matched] = VARIABLE_CONSTRUCTION[matched]
                if matched != var:
                    suggestions.append(f"「{var}」已匹配到「{matched}」")
            else:
                result[var] = {
                    "concept": var,
                    "measure": "需根据研究设计定义",
                    "formula": "待定",
                    "source": "CSMAR/Wind/AKShare",
                    "pitfalls": ["需明确定义口径"],
                    "suggestion": "建议参考CSMAR变量字典或类似研究的变量定义",
                }
        return {"task": task, "variables": result, "suggestions": suggestions}
    elif task == "描述统计":
        return {"task": task, "template": REGRESSION_TEMPLATES["描述统计"]}
    elif task == "数据推荐":
        recommended = _match_data_sources(variables)
        return {
            "task": task,
            "data_sources": DATA_SOURCES,
            "recommended_sources": recommended,
            "variables": variables,
            "suggestion": f"根据「{variables}」推荐以上数据源，按相关度排序",
        }
    else:
        return {"task": task, "error": f"未知任务: {task}，可选: 回归代码/变量构造/描述统计/数据推荐"}


def get_paper_section(
    section: str,
    research_info: str = "",
    findings: str = "",
    contributions: str = "",
) -> Dict[str, Any]:
    """生成论文段落模板（增强版：自动填充占位符）"""
    template = PAPER_WRITING_TEMPLATES.get(section)
    if not template:
        return {"error": f"未知section: {section}，可选: {list(PAPER_WRITING_TEMPLATES.keys())}"}

    # 从 research_info 提取信息用于填充
    info = research_info or ""
    replacements = {
        "background": info if info else "[请填写研究背景：宏观趋势+现实问题]",
        "gap": "[请填写研究缺口：现有文献在XX方面存在不足]",
        "method": "[请填写研究方法]",
        "research_question": info if info else "[请填写研究问题]",
        "data_source": "[请填写数据来源]",
        "data_description": "[请填写数据描述]",
        "unit": "[请填写研究对象]",
        "findings": findings if findings else "[请填写主要发现]",
        "contributions": contributions if contributions else "[请填写边际贡献]",
        "finding1": findings.split("；")[0].strip() if findings and "；" in findings else (findings if findings else "[发现1]"),
        "finding2": findings.split("；")[1].strip() if findings and "；" in findings and len(findings.split("；")) > 1 else "[发现2]",
        "finding3": findings.split("；")[2].strip() if findings and "；" in findings and len(findings.split("；")) > 2 else "[发现3]",
        "mechanism": "[请填写机制分析]",
        "implication": "[请填写理论意义]",
        "policy": "[请填写政策含义]",
        "keyword1": "[关键词1]",
        "keyword2": "[关键词2]",
        "keyword3": "[关键词3]",
        "keyword4": "[关键词4]",
        "jel_codes": "[JEL分类号]",
        "topic": info if info else "[研究主题]",
        "positioning": contributions if contributions else "[本文定位]",
    }

    filled_template = _fill_template(template["template"], replacements)

    return {
        "section": section,
        "structure": template["structure"],
        "template": filled_template,
        "raw_template": template["template"],
        "tips": template["tips"],
        "research_info": research_info,
        "findings": findings,
        "contributions": contributions,
        "has_user_input": bool(research_info or findings or contributions),
    }
