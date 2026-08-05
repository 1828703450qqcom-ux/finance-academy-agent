"""
文件分析路由 - 支持上传CSV/Excel/TXT等文件进行AI分析
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
import asyncio

router = APIRouter(prefix="/api/research", tags=["file-analysis"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-file")
async def upload_file(session_id: str = "default", file: UploadFile = File(...)):
    """上传文件"""
    filepath = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {"filename": f"{session_id}_{file.filename}", "size": len(content), "session_id": session_id}


@router.post("/analyze-file")
async def analyze_file(session_id: str = "default", filename: str = ""):
    """分析上传的文件"""
    from services.llm_service import call_minimax
    from database import SessionLocal, ChatHistory

    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": "文件不存在"}

    try:
        ext = os.path.splitext(filename)[1].lower()
        file_content = ""

        if ext in [".csv"]:
            import pandas as pd
            df = pd.read_csv(filepath, nrows=100)
            file_content = f"CSV文件，共{len(df)}行{len(df.columns)}列\n\n列名：{list(df.columns)}\n\n前5行：\n{df.head().to_string()}\n\n统计：\n{df.describe().to_string()}"
        elif ext in [".xlsx", ".xls"]:
            import pandas as pd
            df = pd.read_excel(filepath, nrows=100)
            file_content = f"Excel文件，共{len(df)}行{len(df.columns)}列\n\n列名：{list(df.columns)}\n\n前5行：\n{df.head().to_string()}\n\n统计：\n{df.describe().to_string()}"
        elif ext in [".docx"]:
            from docx import Document
            doc = Document(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            tables = []
            for table in doc.tables:
                for row in table.rows:
                    tables.append([cell.text for cell in row.cells])
            file_content = f"Word文档，共{len(paragraphs)}段\n\n正文内容：\n{''.join(paragraphs[:50])}"
            if tables:
                file_content += f"\n\n表格数据：\n{str(tables[:10])}"
        elif ext in [".pdf"]:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages[:10]:
                text += page.extract_text() or ""
            file_content = f"PDF文档，共{len(reader.pages)}页\n\n内容摘要：\n{text[:5000]}"
        elif ext in [".txt", ".md", ".py", ".json"]:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()[:5000]
        else:
            file_content = f"文件: {filename}，类型: {ext}"

        system_prompt = """你是金融数据分析专家，帮助研究者分析上传的数据文件。

## 输出要求
1. 数据概览：行数、列数、数据类型
2. 关键变量说明：每个列的经济含义
3. 数据质量评估：缺失值、异常值
4. 统计特征：均值、标准差、分布
5. 研究建议：适合什么研究方法，需要注意什么"""

        user_msg = f"请分析以下数据文件：\n\n{file_content}"

        def _call():
            return call_minimax(system_prompt=system_prompt, user_message=user_msg, temperature=0.5, max_tokens=3000)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call)

        # 保存到数据库
        db = SessionLocal()
        try:
            db.add(ChatHistory(session_id=f"research:{session_id}", role="user", content=f"[文件分析] {filename}"))
            db.add(ChatHistory(session_id=f"research:{session_id}", role="assistant", content=response))
            db.commit()
        finally:
            db.close()

        return {"response": response, "filename": filename, "session_id": session_id}

    except Exception as e:
        return {"error": f"文件分析失败: {str(e)}"}
