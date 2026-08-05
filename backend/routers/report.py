import os
import json
from fastapi import APIRouter, UploadFile, File, Body
from database import SessionLocal, UploadedReport
from services.report_service import analyze_report, parse_financial_report

router = APIRouter(prefix="/api/report", tags=["report"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_report(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    company_name = file.filename.replace(".pdf", "").replace("年报", "").replace("半年报", "")
    year = 2024

    db = SessionLocal()
    try:
        report = UploadedReport(
            filename=file.filename,
            file_path=file_path,
            company_name=company_name,
            year=year,
        )
        db.add(report)
        db.commit()
        report_id = report.id
    finally:
        db.close()

    return {
        "report_id": report_id,
        "filename": file.filename,
        "company_name": company_name,
        "year": year,
        "message": "上传成功",
    }


@router.post("/analyze")
async def analyze_uploaded_report(body: dict = Body(...)):
    report_id = body.get("report_id")
    dimensions = body.get("dimensions") or ["dupont", "revenue_growth", "profitability", "solvency"]

    db = SessionLocal()
    try:
        report = db.query(UploadedReport).filter(UploadedReport.id == report_id).first()
        if not report:
            return {"error": "报告未找到"}

        result = analyze_report(report.file_path, dimensions)
        result["company_name"] = report.company_name
        result["year"] = report.year

        report.analysis_result = json.dumps(result)
        db.commit()

        return result
    finally:
        db.close()


@router.get("/list")
async def list_reports():
    db = SessionLocal()
    try:
        reports = (
            db.query(UploadedReport)
            .order_by(UploadedReport.created_at.desc())
            .all()
        )
        return {
            "reports": [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "company_name": r.company_name,
                    "year": r.year,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in reports
            ]
        }
    finally:
        db.close()


@router.get("/quick-analysis/{filename}")
async def quick_analysis(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "文件不存在"}

    result = parse_financial_report(file_path)
    return result
