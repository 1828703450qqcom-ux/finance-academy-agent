from fastapi import APIRouter
from schemas import PaperSearchRequest
from services.paper_service import search_papers
from crawlers.paper_crawler import paper_crawler
from database import SessionLocal, PaperFavorite

router = APIRouter(prefix="/api/paper", tags=["paper"])


@router.post("/search")
async def search_paper(req: PaperSearchRequest):
    results = search_papers(
        query=req.query,
        sources=req.sources,
        year_from=req.year_from,
        year_to=req.year_to,
        fields=req.fields,
    )
    return {"results": results, "total": len(results)}


@router.post("/search-advanced")
async def search_advanced(req: PaperSearchRequest):
    """高级搜索 - 包含所有爬虫数据源"""
    source_map = {
        "openalex": "openalex",
        "arxiv": "arxiv",
        "semantic_scholar": "semantic_scholar",
        "cnki": "cnki",
        "ssrn": "ssrn",
        "nber": "nber",
    }
    crawler_sources = []
    api_sources = []
    for s in (req.sources or []):
        if s in ["semantic_scholar", "cnki", "ssrn", "nber"]:
            crawler_sources.append(s)
        else:
            api_sources.append(s)

    all_results = []
    # API数据源
    if api_sources:
        all_results.extend(search_papers(
            query=req.query,
            sources=api_sources,
            year_from=req.year_from,
            year_to=req.year_to,
        ))
    # 爬虫数据源
    if crawler_sources:
        all_results.extend(paper_crawler.search_all(
            query=req.query,
            sources=crawler_sources,
            year_from=req.year_from,
            year_to=req.year_to,
        ))

    all_results.sort(key=lambda x: x.get("citation_count", 0), reverse=True)
    return {"results": all_results, "total": len(all_results)}


@router.post("/favorite")
async def add_favorite(paper: dict):
    db = SessionLocal()
    try:
        fav = PaperFavorite(
            title=paper.get("title", ""),
            authors=paper.get("authors", ""),
            year=paper.get("year", 0),
            source=paper.get("source", ""),
            citation_count=paper.get("citation_count", 0),
            url=paper.get("url", ""),
        )
        db.add(fav)
        db.commit()
        return {"message": "收藏成功", "id": fav.id}
    finally:
        db.close()


@router.get("/favorites")
async def list_favorites():
    db = SessionLocal()
    try:
        favs = db.query(PaperFavorite).order_by(PaperFavorite.created_at.desc()).all()
        return {
            "favorites": [
                {
                    "id": f.id,
                    "title": f.title,
                    "authors": f.authors,
                    "year": f.year,
                    "source": f.source,
                    "citation_count": f.citation_count,
                    "url": f.url,
                }
                for f in favs
            ]
        }
    finally:
        db.close()


@router.delete("/favorite/{fav_id}")
async def remove_favorite(fav_id: int):
    db = SessionLocal()
    try:
        fav = db.query(PaperFavorite).filter(PaperFavorite.id == fav_id).first()
        if fav:
            db.delete(fav)
            db.commit()
        return {"message": "已取消收藏"}
    finally:
        db.close()
