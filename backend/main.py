import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import chat, empirical, quant, report, paper, macro, finance_report, research_llm

app = FastAPI(title="金融学院AI助手", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check router (必须在static mount之前注册)
health_router = APIRouter(tags=["health"])

@health_router.get("/api/health")
async def health():
    return {"status": "ok", "message": "金融学院AI助手运行中"}

app.include_router(health_router)
app.include_router(chat.router)
app.include_router(empirical.router)
app.include_router(quant.router)
app.include_router(report.router)
app.include_router(paper.router)
app.include_router(macro.router)
app.include_router(finance_report.router)
app.include_router(research_llm.router)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
