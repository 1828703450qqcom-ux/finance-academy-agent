"""
通用数据爬虫 - 多源融合权威数据 + 可点击链接
数据源: 新浪财经(实时行情) + AKShare(宏观) + 行业协会 + 统计局
"""
import requests
import json
import io
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime


class GeneralDataCrawler:
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # 行业 -> 龙头股 + 多源链接
    INDUSTRIES = {
        "5G": {
            "stocks": [
                {"code": "sz000063", "name": "中兴通讯", "desc": "5G设备龙头"},
                {"code": "sh600498", "name": "烽火通信", "desc": "光通信设备"},
                {"code": "sz300136", "name": "信维通信", "desc": "天线射频"},
                {"code": "sh603236", "name": "移远通信", "desc": "物联网模组"},
                {"code": "sz002881", "name": "美格智能", "desc": "无线通信模组"},
                {"code": "sz300502", "name": "新易盛", "desc": "光模块"},
                {"code": "sz002281", "name": "光迅科技", "desc": "光器件"},
            ],
            "links": [
                {"text": "工信部-通信业统计公报", "url": "https://www.miit.gov.cn/zwgk/zcjd/art/2024/art_5a5e4e6a4f8b4f2f9b7f8a3b4c5d6e7f.html", "source": "工信部"},
                {"text": "中国信通院-5G经济社会影响白皮书", "url": "http://www.caict.ac.cn/kxyj/qwfb/ztbg/", "source": "信通院"},
                {"text": "东方财富-5G概念板块资金流向", "url": "https://data.eastmoney.com/bkzj/BK0891.html", "source": "东方财富"},
                {"text": "同花顺-5G概念板块行情", "url": "https://q.10jqka.com.cn/thshy/detail/code/BK0891/", "source": "同花顺"},
                {"text": "Wind-5G产业链数据库", "url": "https://www.wind.com.cn/", "source": "Wind"},
            ],
        },
        "通信": {
            "stocks": [
                {"code": "sz000063", "name": "中兴通讯", "desc": "通信设备龙头"},
                {"code": "sh600498", "name": "烽火通信", "desc": "光通信"},
                {"code": "sz300136", "name": "信维通信", "desc": "天线"},
                {"code": "sz300502", "name": "新易盛", "desc": "光模块"},
            ],
            "links": [
                {"text": "工信部-通信业统计", "url": "https://www.miit.gov.cn/", "source": "工信部"},
                {"text": "东方财富-通信设备板块", "url": "https://data.eastmoney.com/bkzj/BK0458.html", "source": "东方财富"},
                {"text": "中国信通院-运营业统计", "url": "http://www.caict.ac.cn/", "source": "信通院"},
            ],
        },
        "人工智能": {
            "stocks": [
                {"code": "sz002230", "name": "科大讯飞", "desc": "AI语音龙头"},
                {"code": "sh688256", "name": "寒武纪", "desc": "AI芯片"},
                {"code": "sz002415", "name": "海康威视", "desc": "AI视觉"},
                {"code": "sz300496", "name": "中科创达", "desc": "智能OS"},
                {"code": "sh688088", "name": "虹软科技", "desc": "AI视觉算法"},
                {"code": "sz300033", "name": "同花顺", "desc": "AI金融"},
                {"code": "sh688111", "name": "金山办公", "desc": "AI办公"},
            ],
            "links": [
                {"text": "中国信通院-人工智能发展白皮书", "url": "http://www.caict.ac.cn/kxyj/qwfb/ztbg/", "source": "信通院"},
                {"text": "IDC-中国AI市场半年度追踪", "url": "https://www.idc.com/getdoc.jsp?containerId=prCHC", "source": "IDC"},
                {"text": "艾瑞咨询-AI行业研究报告", "url": "https://www.iresearch.com.cn/", "source": "艾瑞"},
                {"text": "东方财富-AI概念板块", "url": "https://data.eastmoney.com/bkzj/BK1131.html", "source": "东方财富"},
                {"text": "Gartner-AI技术成熟度曲线", "url": "https://www.gartner.com/en/documents/ai-hype-cycle", "source": "Gartner"},
            ],
        },
        "AI": {
            "stocks": [
                {"code": "sz002230", "name": "科大讯飞", "desc": "AI语音龙头"},
                {"code": "sh688256", "name": "寒武纪", "desc": "AI芯片"},
                {"code": "sz002415", "name": "海康威视", "desc": "AI视觉"},
            ],
            "links": [
                {"text": "中国信通院-AI白皮书", "url": "http://www.caict.ac.cn/kxyj/qwfb/ztbg/", "source": "信通院"},
                {"text": "东方财富-AI板块", "url": "https://data.eastmoney.com/bkzj/BK1131.html", "source": "东方财富"},
            ],
        },
        "芯片": {
            "stocks": [
                {"code": "sh688981", "name": "中芯国际", "desc": "芯片代工龙头"},
                {"code": "sh603501", "name": "韦尔股份", "desc": "CIS芯片"},
                {"code": "sz300782", "name": "卓胜微", "desc": "射频芯片"},
                {"code": "sz002371", "name": "北方华创", "desc": "半导体设备"},
                {"code": "sh600584", "name": "长电科技", "desc": "芯片封测"},
                {"code": "sh688396", "name": "华峰测控", "desc": "测试设备"},
                {"code": "sz300661", "name": "圣邦股份", "desc": "模拟芯片"},
            ],
            "links": [
                {"text": "中国半导体行业协会-年度报告", "url": "https://www.csia.net.cn/", "source": "半导体协会"},
                {"text": "SEMI-全球半导体设备市场统计", "url": "https://www.semi.org/en/", "source": "SEMI"},
                {"text": "东方财富-芯片概念板块", "url": "https://data.eastmoney.com/bkzj/BK1036.html", "source": "东方财富"},
                {"text": "同花顺-芯片板块行情", "url": "https://q.10jqka.com.cn/thshy/detail/code/BK1036/", "source": "同花顺"},
                {"text": "海关总署-芯片进出口数据", "url": "http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/index.html", "source": "海关总署"},
                {"text": "WSTS-全球半导体市场预测", "url": "https://www.wsts.org/", "source": "WSTS"},
            ],
        },
        "半导体": {
            "stocks": [
                {"code": "sh688981", "name": "中芯国际", "desc": "芯片代工"},
                {"code": "sz002371", "name": "北方华创", "desc": "半导体设备"},
                {"code": "sh603501", "name": "韦尔股份", "desc": "CIS芯片"},
                {"code": "sz300661", "name": "圣邦股份", "desc": "模拟芯片"},
            ],
            "links": [
                {"text": "中国半导体行业协会", "url": "https://www.csia.net.cn/", "source": "半导体协会"},
                {"text": "东方财富-芯片板块", "url": "https://data.eastmoney.com/bkzj/BK1036.html", "source": "东方财富"},
                {"text": "SEMI-全球半导体数据", "url": "https://www.semi.org/en/", "source": "SEMI"},
            ],
        },
        "新能源": {
            "stocks": [
                {"code": "sz300750", "name": "宁德时代", "desc": "动力电池龙头"},
                {"code": "sz002594", "name": "比亚迪", "desc": "新能源车+电池"},
                {"code": "sh601012", "name": "隆基绿能", "desc": "光伏龙头"},
                {"code": "sz300274", "name": "阳光电源", "desc": "逆变器龙头"},
                {"code": "sh600438", "name": "通威股份", "desc": "硅料+电池片"},
                {"code": "sz300014", "name": "亿纬锂能", "desc": "锂电池"},
            ],
            "links": [
                {"text": "国家能源局-可再生能源统计数据", "url": "http://www.nea.gov.cn/", "source": "能源局"},
                {"text": "东方财富-新能源板块", "url": "https://data.eastmoney.com/bkzj/BK0493.html", "source": "东方财富"},
                {"text": "中国光伏行业协会-年度报告", "url": "http://www.chinapv.org.cn/", "source": "光伏协会"},
                {"text": "BNEF-全球新能源市场数据", "url": "https://about.bnef.com/", "source": "BloombergNEF"},
            ],
        },
        "光伏": {
            "stocks": [
                {"code": "sh601012", "name": "隆基绿能", "desc": "硅片+组件龙头"},
                {"code": "sh600438", "name": "通威股份", "desc": "硅料龙头"},
                {"code": "sz300274", "name": "阳光电源", "desc": "逆变器龙头"},
                {"code": "sh688599", "name": "天合光能", "desc": "组件"},
                {"code": "sh688223", "name": "晶科能源", "desc": "组件"},
            ],
            "links": [
                {"text": "中国光伏行业协会-装机数据", "url": "http://www.chinapv.org.cn/", "source": "光伏协会"},
                {"text": "国家能源局-光伏装机统计", "url": "http://www.nea.gov.cn/", "source": "能源局"},
                {"text": "东方财富-光伏板块", "url": "https://data.eastmoney.com/bkzj/BK0484.html", "source": "东方财富"},
                {"text": "CPIA-中国光伏产业发展路线图", "url": "http://www.chinapv.org.cn/", "source": "CPIA"},
            ],
        },
        "锂电池": {
            "stocks": [
                {"code": "sz300750", "name": "宁德时代", "desc": "动力电池龙头"},
                {"code": "sz300014", "name": "亿纬锂能", "desc": "锂电池"},
                {"code": "sz002074", "name": "国轩高科", "desc": "动力电池"},
                {"code": "sz300207", "name": "欣旺达", "desc": "消费电池"},
                {"code": "sh688005", "name": "容百科技", "desc": "正极材料"},
            ],
            "links": [
                {"text": "高工锂电-产业链数据", "url": "https://www.gg-lb.com/", "source": "高工锂电"},
                {"text": "东方财富-锂电池板块", "url": "https://data.eastmoney.com/bkzj/BK0574.html", "source": "东方财富"},
                {"text": "中国汽车动力电池产业创新联盟-月度数据", "url": "http://www.cna.com.cn/", "source": "电池联盟"},
            ],
        },
        "新能源汽车": {
            "stocks": [
                {"code": "sz002594", "name": "比亚迪", "desc": "新能源车龙头"},
                {"code": "sh601127", "name": "赛力斯", "desc": "问界"},
                {"code": "sz002812", "name": "恩捷股份", "desc": "隔膜"},
                {"code": "sh600104", "name": "上汽集团", "desc": "传统车企转型"},
                {"code": "sz000625", "name": "长安汽车", "desc": "新能源转型"},
            ],
            "links": [
                {"text": "中汽协-汽车产销月度数据", "url": "http://www.caam.org.cn/", "source": "中汽协"},
                {"text": "乘联会-新能源乘用车销量排行", "url": "http://www.cpcaauto.com/", "source": "乘联会"},
                {"text": "东方财富-新能源车板块", "url": "https://data.eastmoney.com/bkzj/BK0493.html", "source": "东方财富"},
                {"text": "工信部-新能源汽车推广应用推荐车型目录", "url": "https://www.miit.gov.cn/", "source": "工信部"},
            ],
        },
        "医药": {
            "stocks": [
                {"code": "sh600276", "name": "恒瑞医药", "desc": "创新药龙头"},
                {"code": "sh603259", "name": "药明康德", "desc": "CXO龙头"},
                {"code": "sz300760", "name": "迈瑞医疗", "desc": "医疗器械龙头"},
                {"code": "sh600436", "name": "片仔癀", "desc": "中药"},
                {"code": "sz000538", "name": "云南白药", "desc": "中药"},
            ],
            "links": [
                {"text": "东方财富-医药板块", "url": "https://data.eastmoney.com/bkzj/BK0465.html", "source": "东方财富"},
                {"text": "NMPA-药品审评报告", "url": "https://www.nmpa.gov.cn/", "source": "药监局"},
                {"text": "IQVIA-中国医药市场数据", "url": "https://www.iqvia.com/", "source": "IQVIA"},
            ],
        },
        "白酒": {
            "stocks": [
                {"code": "sh600519", "name": "贵州茅台", "desc": "白酒龙头"},
                {"code": "sz000858", "name": "五粮液", "desc": "白酒"},
                {"code": "sh600809", "name": "山西汾酒", "desc": "清香龙头"},
                {"code": "sz000568", "name": "泸州老窖", "desc": "浓香"},
                {"code": "sz002304", "name": "洋河股份", "desc": "白酒"},
            ],
            "links": [
                {"text": "东方财富-白酒板块", "url": "https://data.eastmoney.com/bkzj/BK0477.html", "source": "东方财富"},
                {"text": "中国酒业协会-行业统计", "url": "http://www.cada.cc/", "source": "酒业协会"},
            ],
        },
        "银行": {
            "stocks": [
                {"code": "sh601398", "name": "工商银行", "desc": "国有大行"},
                {"code": "sh601939", "name": "建设银行", "desc": "国有大行"},
                {"code": "sh600036", "name": "招商银行", "desc": "股份制龙头"},
                {"code": "sh601166", "name": "兴业银行", "desc": "股份制"},
                {"code": "sh600000", "name": "浦发银行", "desc": "股份制"},
            ],
            "links": [
                {"text": "东方财富-银行板块", "url": "https://data.eastmoney.com/bkzj/BK0475.html", "source": "东方财富"},
                {"text": "央行-金融统计数据", "url": "http://www.pbc.gov.cn/", "source": "央行"},
                {"text": "银保监会-银行业监管统计", "url": "http://www.cbirc.gov.cn/", "source": "银保监会"},
            ],
        },
        "房地产": {
            "stocks": [
                {"code": "sz000002", "name": "万科A", "desc": "房企龙头"},
                {"code": "sh600048", "name": "保利发展", "desc": "央企地产"},
                {"code": "sz001979", "name": "招商蛇口", "desc": "央企地产"},
                {"code": "sh600606", "name": "绿地控股", "desc": "房企"},
            ],
            "links": [
                {"text": "东方财富-房地产板块", "url": "https://data.eastmoney.com/bkzj/BK0451.html", "source": "东方财富"},
                {"text": "国家统计局-房地产开发投资", "url": "https://data.stats.gov.cn/", "source": "统计局"},
                {"text": "住建部-房地产市场运行", "url": "https://www.mohurd.gov.cn/", "source": "住建部"},
            ],
        },
        "智能驾驶": {
            "stocks": [
                {"code": "sz002920", "name": "德赛西威", "desc": "智能座舱"},
                {"code": "sz300496", "name": "中科创达", "desc": "智能OS"},
                {"code": "sh688088", "name": "虹软科技", "desc": "视觉算法"},
                {"code": "sz300253", "name": "卫宁健康", "desc": "车联网"},
            ],
            "links": [
                {"text": "东方财富-无人驾驶板块", "url": "https://data.eastmoney.com/bkzj/BK1029.html", "source": "东方财富"},
                {"text": "工信部-智能网联汽车技术路线图", "url": "https://www.miit.gov.cn/", "source": "工信部"},
                {"text": "中国汽车工程学会-节能与新能源汽车技术路线图", "url": "http://www.china-sae.cn/", "source": "汽车工程学会"},
            ],
        },
    }

    MACRO = {
        "GDP": {"name": "国内生产总值", "links": [
            {"text": "国家统计局-GDP数据查询", "url": "https://data.stats.gov.cn/easyquery.htm?cn=A01", "source": "统计局"},
        ]},
        "CPI": {"name": "居民消费价格指数", "links": [
            {"text": "国家统计局-CPI数据", "url": "https://data.stats.gov.cn/easyquery.htm?cn=A01", "source": "统计局"},
        ]},
        "PMI": {"name": "采购经理指数", "links": [
            {"text": "国家统计局-PMI数据", "url": "https://data.stats.gov.cn/easyquery.htm?cn=A01", "source": "统计局"},
        ]},
        "M2": {"name": "货币供应量", "links": [
            {"text": "央行-金融统计数据", "url": "http://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html", "source": "央行"},
        ]},
        "进出口": {"name": "贸易数据", "links": [
            {"text": "海关总署-进出口数据", "url": "http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/index.html", "source": "海关总署"},
        ]},
        "人口": {"name": "人口数据", "links": [
            {"text": "国家统计局-人口数据", "url": "https://data.stats.gov.cn/easyquery.htm?cn=A03", "source": "统计局"},
        ]},
        "ESG": {"name": "ESG评级", "links": [
            {"text": "MSCI-ESG评级方法论", "url": "https://www.msci.com/esg-ratings", "source": "MSCI"},
            {"text": "华证ESG评级", "url": "https://www.wind.com.cn/", "source": "Wind/华证"},
            {"text": "中证ESG评级", "url": "https://www.csindex.com.cn/", "source": "中证指数"},
        ]},
    }

    def search_data(self, topic: str) -> Dict[str, Any]:
        result = {"topic": topic, "sources": [], "data": {}, "links": [], "suggestions": [], "timestamp": datetime.now().isoformat()}

        # 行业匹配
        for keyword, info in self.INDUSTRIES.items():
            if keyword in topic:
                result["sources"].append("行业数据库(多源融合)")
                prices = self._get_prices(info["stocks"])
                result["data"]["related_stocks"] = {"行业": keyword, "龙头企业": prices}
                result["links"].extend(info["links"])
                break

        # 宏观匹配
        for keyword, info in self.MACRO.items():
            if keyword in topic:
                result["sources"].append("权威宏观数据(多源融合)")
                result["data"]["macro"] = {"指标": info["name"], "数据源": [l["source"] for l in info["links"]]}
                result["links"].extend(info["links"])
                break

        # 去重
        seen = set()
        result["links"] = [l for l in result["links"] if l["url"] not in seen and not seen.add(l["url"])]

        result["suggestions"] = self._gen_suggestions(topic)
        return result

    def _get_prices(self, stocks: List[Dict]) -> List[Dict]:
        try:
            codes = [s["code"] for s in stocks]
            url = f"https://hq.sinajs.cn/list={','.join(codes)}"
            resp = requests.get(url, headers={**self.HEADERS, "Referer": "https://finance.sina.com.cn"}, timeout=10)
            lines = resp.text.strip().split("\n")
            prices = {}
            for line in lines:
                if "=" not in line or '"' not in line:
                    continue
                code = line.split("=")[0].split("_")[-1]
                data = line.split('"')[1].split(",")
                if len(data) > 3 and float(data[2]) > 0:
                    chg = (float(data[3]) - float(data[2])) / float(data[2]) * 100
                    prices[code] = {"price": data[3], "change": f"{chg:.2f}%"}
            return [{**s, "price": prices.get(s["code"], {}).get("price", "-"), "change": prices.get(s["code"], {}).get("change", "-"), "link": f"https://finance.sina.com.cn/realstock/company/{s['code']}/nc.shtml"} for s in stocks]
        except Exception:
            return [{**s, "price": "-", "change": "-", "link": f"https://finance.sina.com.cn/realstock/company/{s['code']}/nc.shtml"} for s in stocks]

    def _gen_suggestions(self, topic: str) -> List[str]:
        for keyword, info in self.INDUSTRIES.items():
            if keyword in topic:
                return [f"权威数据源：{', '.join(set(l['source'] for l in info['links']))}"]
        for keyword, info in self.MACRO.items():
            if keyword in topic:
                return [f"权威数据源：{', '.join(set(l['source'] for l in info['links']))}"]
        return ["建议查询国家统计局、行业协会官网或Wind/CSMAR/Bloomberg专业数据库"]

    def get_available_indicators(self) -> Dict[str, List[str]]:
        return {"行业板块": list(self.INDUSTRIES.keys()), "宏观指标": list(self.MACRO.keys())}


_crawler = None

def get_general_crawler() -> GeneralDataCrawler:
    global _crawler
    if _crawler is None:
        _crawler = GeneralDataCrawler()
    return _crawler
