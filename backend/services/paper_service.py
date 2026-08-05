import requests
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional


def search_openalex(
    query: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    results = []
    try:
        params = {
            "search": query,
            "per_page": 10,
            "sort": "cited_by_count:desc",
        }
        filters = []
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filters.append(f"to_publication_date:{year_to}-12-31")
        if filters:
            params["filter"] = ",".join(filters)

        resp = requests.get(
            "https://api.openalex.org/works", params=params, timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            for work in data.get("results", []):
                authors = ", ".join(
                    [a.get("author", {}).get("display_name", "") for a in work.get("authorships", [])[:5]]
                )
                results.append(
                    {
                        "title": work.get("title", ""),
                        "authors": authors,
                        "year": work.get("publication_year", 0),
                        "source": "OpenAlex",
                        "citation_count": work.get("cited_by_count", 0),
                        "url": work.get("doi", work.get("id", "")),
                        "abstract": work.get("abstract_inverted_index", {})
                        if isinstance(work.get("abstract_inverted_index"), str)
                        else "",
                    }
                )
    except Exception:
        pass
    return results


def search_arxiv(
    query: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> List[Dict[str, Any]]:
    results = []
    try:
        search_query = f"all:{query}"
        if year_from:
            search_query += f" AND submittedDate:[{year_from}0101 TO *]"
        if year_to:
            search_query += f" AND submittedDate:[* TO {year_to}1231]"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": 10,
            "sortBy": "relevance",
        }
        resp = requests.get(
            "http://export.arxiv.org/api/query", params=params, timeout=15
        )
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                summary = entry.find("atom:summary", ns)
                published = entry.find("atom:published", ns)
                authors = [
                    a.find("atom:name", ns).text
                    for a in entry.findall("atom:author", ns)[:5]
                ]
                links = entry.findall("atom:link", ns)
                pdf_url = ""
                for link in links:
                    if link.get("title") == "pdf":
                        pdf_url = link.get("href", "")

                year = 0
                if published is not None and published.text:
                    year = int(published.text[:4])

                results.append(
                    {
                        "title": (title.text if title is not None else "").strip(),
                        "authors": ", ".join(authors),
                        "year": year,
                        "source": "arXiv",
                        "citation_count": 0,
                        "url": pdf_url or (
                            entry.find("atom:id", ns).text
                            if entry.find("atom:id", ns) is not None
                            else ""
                        ),
                        "abstract": (summary.text if summary is not None else "")[:500],
                    }
                )
    except Exception:
        pass
    return results


def search_papers(
    query: str,
    sources: List[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if sources is None:
        sources = ["openalex", "arxiv"]

    all_results = []
    if "openalex" in sources:
        all_results.extend(search_openalex(query, year_from, year_to, fields))
    if "arxiv" in sources:
        all_results.extend(search_arxiv(query, year_from, year_to))

    all_results.sort(key=lambda x: x.get("citation_count", 0), reverse=True)
    return all_results
