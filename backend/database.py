import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_PATH = os.getenv("FINANCE_DB_PATH", os.path.join(os.path.dirname(__file__), "finance_agent.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    role = Column(String(16))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class UploadedReport(Base):
    __tablename__ = "uploaded_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(256))
    file_path = Column(String(512))
    company_name = Column(String(128))
    year = Column(Integer)
    analysis_result = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class ResearchProject(Base):
    __tablename__ = "research_projects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256))
    variables = Column(Text)
    model_type = Column(String(64))
    results = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_type = Column(String(64))
    stock_pool = Column(String(64))
    start_date = Column(String(16))
    end_date = Column(String(16))
    metrics = Column(Text)
    equity_curve = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class PaperFavorite(Base):
    __tablename__ = "paper_favorites"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512))
    authors = Column(String(512))
    year = Column(Integer)
    source = Column(String(64))
    citation_count = Column(Integer)
    url = Column(String(1024))
    created_at = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
