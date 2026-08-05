"""
学术论文爬虫
数据源：Semantic Scholar、CNKI(知网)、SSRN、NBER
"""
import requests
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote


class PaperCrawler:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    TIMEOUT = 15

    # ==================== Semantic Scholar ====================

    def search_semantic_scholar(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Semantic Scholar API - 免费、高质量学术搜索"""
        results = []
        try:
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,authors,year,citationCount,url,abstract,externalIds,publicationVenue,fieldsOfStudy",
                "sort": "citationCount:desc",
            }
            if year_from or year_to:
                year_range = f"{year_from or ''}-{year_to or ''}"
                params["year"] = year_range

            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                for paper in data.get("data", []):
                    authors = ", ".join(
                        [a.get("name", "") for a in (paper.get("authors") or [])[:5]]
                    )
                    venue = paper.get("publicationVenue", {})
                    venue_name = venue.get("name", "") if venue else ""
                    results.append({
                        "title": paper.get("title", ""),
                        "authors": authors,
                        "year": paper.get("year", 0),
                        "source": "Semantic Scholar",
                        "citation_count": paper.get("citationCount", 0),
                        "url": paper.get("url", ""),
                        "abstract": (paper.get("abstract") or "")[:500],
                        "venue": venue_name,
                        "fields": paper.get("fieldsOfStudy", []),
                        "doi": (paper.get("externalIds") or {}).get("DOI", ""),
                    })
        except Exception:
            pass
        return results

    # ==================== CNKI (知网) ====================

    def search_cnki(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """知网爬虫 - 中文权威学术论文"""
        results = []
        try:
            search_url = "https://kns.cnki.net/kns8s/brief/grid"
            params = {
                "IsSearch": "true",
                "QueryJson": json.dumps({
                    "Platform": "",
                    "DBCode": "CFLS",
                    "KuaKuCode": "CJFQ,CDMD,CIPD,CCND,BDZK,CISD,SNAD,CCJD,GXDB_SECTION,CJFN,CCVD",
                    "QNode": {
                        "QGroup": [{
                            "Key": "Subject",
                            "Title": "",
                            "Logic": 0,
                            "Items": [{
                                "Title": "主题",
                                "Name": "SU",
                                "Value": query,
                                "Operate": "%=",
                                "BlurType": "",
                            }],
                            "ChildItems": [],
                        }],
                    },
                    "ExScope": "1",
                    "SearchType": 1,
                }),
                "PageName": "DefaultResult",
                "DBCode": "CFLS",
                "KuaKuCodes": "CJFQ,CDMD,CIPD,CCND,BDZK,CISD,SNAD,CCJD,GXDB_SECTION,CJFN,CCVD",
                "CurPage": "1",
                "RecordsCntPerPage": str(limit),
                "CurDisplayMode": "listmode",
                "CurrSortField": "",
                "CurrSortFieldType": "desc",
                "IsSentenceSearch": "false",
            }
            if year_from:
                params["QuyTime"] = f"{year_from}-{year_to or datetime.now().year}"

            session = requests.Session()
            session.headers.update(self.HEADERS)
            # 先访问主页获取cookie
            session.get("https://kns.cnki.net/kns8s/defaultresult/index", timeout=self.TIMEOUT)
            resp = session.post(search_url, data=params, timeout=self.TIMEOUT)

            if resp.status_code == 200:
                text = resp.text
                # 解析结果
                titles = re.findall(r'<a[^>]*class="fz14"[^>]*>(.*?)</a>', text, re.DOTALL)
                authors_list = re.findall(r'<td[^>]*class="author"[^>]*>(.*?)</td>', text, re.DOTALL)
                sources_list = re.findall(r'<td[^>]*class="source"[^>]*>(.*?)</td>', text, re.DOTALL)
                dates_list = re.findall(r'<td[^>]*class="date"[^>]*>(.*?)</td>', text, re.DOTALL)

                for i in range(min(len(titles), limit)):
                    title = re.sub(r'<[^>]+>', '', titles[i]).strip()
                    author = re.sub(r'<[^>]+>', '', authors_list[i]).strip() if i < len(authors_list) else ""
                    source = re.sub(r'<[^>]+>', '', sources_list[i]).strip() if i < len(sources_list) else ""
                    date = re.sub(r'<[^>]+>', '', dates_list[i]).strip() if i < len(dates_list) else ""
                    year_match = re.search(r'(\d{4})', date)
                    year = int(year_match.group(1)) if year_match else 0

                    results.append({
                        "title": title,
                        "authors": author,
                        "year": year,
                        "source": f"CNKI-{source}" if source else "CNKI",
                        "citation_count": 0,
                        "url": f"https://kns.cnki.net/kcms2/article/abstract?v={quote(title)}",
                        "abstract": "",
                        "database": "知网",
                    })
        except Exception:
            pass
        return results

    # ==================== SSRN ====================

    def search_ssrn(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """SSRN - 社会科学预印本"""
        results = []
        try:
            params = {
                "abstract": "",
                "title": query,
                "per_page": str(limit),
                "sort": "rank",
                "order": "desc",
            }
            resp = requests.get(
                "https://papers.ssrn.com/sol3/results.cfm",
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            if resp.status_code == 200:
                text = resp.text
                titles = re.findall(r'<h3[^>]*class="title"[^>]*>.*?<a[^>]*>(.*?)</a>', text, re.DOTALL)
                authors_list = re.findall(r'<div[^>]*class="authors"[^>]*>(.*?)</div>', text, re.DOTALL)

                for i in range(min(len(titles), limit)):
                    title = re.sub(r'<[^>]+>', '', titles[i]).strip()
                    author = re.sub(r'<[^>]+>', '', authors_list[i]).strip() if i < len(authors_list) else ""

                    results.append({
                        "title": title,
                        "authors": author,
                        "year": 0,
                        "source": "SSRN",
                        "citation_count": 0,
                        "url": "https://papers.ssrn.com/sol3/papers.cfm",
                        "abstract": "",
                    })
        except Exception:
            pass
        return results

    # ==================== NBER ====================

    def search_nber(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """NBER - 美国国家经济研究局工作论文"""
        results = []
        try:
            params = {"q": query, "per_page": str(limit)}
            resp = requests.get(
                "https://www.nber.org/api/v1/working_page_listing/contentType/working_paper/_/_/search",
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                for paper in data.get("results", [])[:limit]:
                    results.append({
                        "title": paper.get("title", ""),
                        "authors": ", ".join([a.get("name", "") for a in paper.get("authors", [])]),
                        "year": int(paper.get("publicDate", "")[:4]) if paper.get("publicDate") else 0,
                        "source": "NBER",
                        "citation_count": 0,
                        "url": paper.get("url", ""),
                        "abstract": (paper.get("abstract") or "")[:500],
                    })
        except Exception:
            pass
        return results

    # ==================== 综合搜索 ====================

    def search_all(
        self,
        query: str,
        sources: List[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """综合搜索多个数据源"""
        if sources is None:
            sources = ["semantic_scholar", "cnki", "arxiv", "nber"]

        all_results = []
        if "semantic_scholar" in sources:
            all_results.extend(self.search_semantic_scholar(query, year_from, year_to, limit))
        if "cnki" in sources:
            all_results.extend(self.search_cnki(query, year_from, year_to, limit))
        if "ssrn" in sources:
            all_results.extend(self.search_ssrn(query, year_from, year_to, limit))
        if "nber" in sources:
            all_results.extend(self.search_nber(query, limit))

        all_results.sort(key=lambda x: x.get("citation_count", 0), reverse=True)
        return all_results


paper_crawler = PaperCrawler()
