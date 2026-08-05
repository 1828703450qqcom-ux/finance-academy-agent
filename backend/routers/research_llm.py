"""
科研助手 LLM 路由
集成 MiniMax API + Econ-Claw 提示词框架
提供AI驱动的研究设计、实证指导、论文写作能力
每个用户独立会话，避免回答冲突
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
import asyncio
import uuid

router = APIRouter(prefix="/api/research", tags=["research-llm"])

# 会话前缀，区分科研助手和普通聊天
SESSION_PREFIX = "research:"


def _get_session_messages(session_id: str, limit: int = 20) -> List[Dict[str, str]]:
    """从数据库加载会话历史"""
    from database import SessionLocal, ChatHistory
    db = SessionLocal()
    try:
        full_id = f"{SESSION_PREFIX}{session_id}"
        messages = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == full_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()
        return [{"role": m.role, "content": m.content} for m in messages]
    finally:
        db.close()


def _save_message(session_id: str, role: str, content: str):
    """保存消息到数据库"""
    from database import SessionLocal, ChatHistory
    db = SessionLocal()
    try:
        full_id = f"{SESSION_PREFIX}{session_id}"
        msg = ChatHistory(session_id=full_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()


# ==================== 请求模型 ====================

class ResearchChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str = "assistant"


class TopicScoutRequest(BaseModel):
    session_id: str
    research_question: str
    context: Optional[str] = ""


class DesignDoctorRequest(BaseModel):
    session_id: str
    research_question: str
    data_type: str = "panel"
    dependent_var: Optional[str] = ""
    independent_vars: Optional[str] = ""
    context: Optional[str] = ""


class PaperDraftRequest(BaseModel):
    session_id: str
    section: str = "引言"
    research_info: str
    findings: Optional[str] = ""
    contributions: Optional[str] = ""


class ReviewRequest(BaseModel):
    session_id: str
    paper_text: str
    focus: Optional[str] = ""


class LiteratureRequest(BaseModel):
    session_id: str
    research_question: str
    keywords: Optional[str] = ""


# ==================== 会话管理端点 ====================

@router.post("/session")
async def create_research_session():
    """创建新的科研助手会话"""
    session_id = str(uuid.uuid4())[:8]
    return {"session_id": session_id}


@router.delete("/session/{session_id}")
async def delete_research_session(session_id: str):
    """删除科研助手会话"""
    from database import SessionLocal, ChatHistory
    db = SessionLocal()
    try:
        full_id = f"{SESSION_PREFIX}{session_id}"
        db.query(ChatHistory).filter(ChatHistory.session_id == full_id).delete()
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.get("/session/{session_id}/history")
async def get_research_history(session_id: str):
    """获取科研助手会话历史"""
    messages = _get_session_messages(session_id, limit=100)
    return {"messages": messages, "session_id": session_id}


# ==================== AI端点 ====================

@router.post("/chat")
async def research_chat(req: ResearchChatRequest):
    """通用科研助手对话"""
    from services.llm_service import call_minimax
    from services.econ_claw_prompts import (
        RESEARCH_ASSISTANT_SYSTEM,
        TOPIC_SCOUT_SYSTEM,
        DESIGN_DOCTOR_SYSTEM,
        PAPER_DRAFTER_SYSTEM,
        REVIEWER_SYSTEM,
    )

    system_map = {
        "assistant": RESEARCH_ASSISTANT_SYSTEM,
        "topic-scout": TOPIC_SCOUT_SYSTEM,
        "design-doctor": DESIGN_DOCTOR_SYSTEM,
        "paper-draft": PAPER_DRAFTER_SYSTEM,
        "review": REVIEWER_SYSTEM,
    }

    system_prompt = system_map.get(req.mode, RESEARCH_ASSISTANT_SYSTEM)

    # 加载会话历史
    history = _get_session_messages(req.session_id)

    # 保存用户消息
    _save_message(req.session_id, "user", req.message)

    def _call():
        return call_minimax(
            system_prompt=system_prompt,
            user_message=req.message,
            history=history,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    # 保存AI回复
    _save_message(req.session_id, "assistant", response)

    return {"response": response, "mode": req.mode, "session_id": req.session_id}


@router.post("/topic-scout")
async def topic_scout(req: TopicScoutRequest):
    """选题探索：将想法转化为研究问题"""
    from services.llm_service import call_minimax
    from services.econ_claw_prompts import TOPIC_SCOUT_SYSTEM, build_topic_scout_prompt

    user_msg = build_topic_scout_prompt(req.research_question, req.context)
    history = _get_session_messages(req.session_id)
    _save_message(req.session_id, "user", f"[选题] {req.research_question}")

    def _call():
        return call_minimax(
            system_prompt=TOPIC_SCOUT_SYSTEM,
            user_message=user_msg,
            history=history,
            temperature=0.7,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    _save_message(req.session_id, "assistant", response)

    return {"response": response, "type": "topic-scout", "session_id": req.session_id}


@router.post("/design-doctor")
async def design_doctor(req: DesignDoctorRequest):
    """方法对比：选择最佳因果识别策略"""
    from services.llm_service import call_minimax
    from services.econ_claw_prompts import DESIGN_DOCTOR_SYSTEM, build_design_doctor_prompt

    user_msg = build_design_doctor_prompt(
        req.research_question, req.data_type,
        req.dependent_var, req.independent_vars, req.context,
    )
    history = _get_session_messages(req.session_id)
    _save_message(req.session_id, "user", f"[方法] {req.research_question}")

    def _call():
        return call_minimax(
            system_prompt=DESIGN_DOCTOR_SYSTEM,
            user_message=user_msg,
            history=history,
            temperature=0.3,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    _save_message(req.session_id, "assistant", response)

    return {"response": response, "type": "design-doctor", "session_id": req.session_id}


@router.post("/paper-draft")
async def paper_draft(req: PaperDraftRequest):
    """论文写作：生成论文各部分草稿"""
    from services.llm_service import call_minimax
    from services.econ_claw_prompts import PAPER_DRAFTER_SYSTEM, build_paper_draft_prompt

    user_msg = build_paper_draft_prompt(req.section, req.research_info, req.findings, req.contributions)
    history = _get_session_messages(req.session_id)
    _save_message(req.session_id, "user", f"[写作] {req.section}")

    def _call():
        return call_minimax(
            system_prompt=PAPER_DRAFTER_SYSTEM,
            user_message=user_msg,
            history=history,
            temperature=0.5,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    _save_message(req.session_id, "assistant", response)

    return {"response": response, "type": "paper-draft", "section": req.section, "session_id": req.session_id}


@router.post("/review")
async def review_simulate(req: ReviewRequest):
    """审稿模拟：四阶段审稿流程"""
    from services.llm_service import call_minimax
    from services.econ_claw_prompts import REVIEWER_SYSTEM, build_review_prompt

    user_msg = build_review_prompt(req.paper_text, req.focus)
    history = _get_session_messages(req.session_id)
    _save_message(req.session_id, "user", f"[审稿] {req.focus or '全文审查'}")

    def _call():
        return call_minimax(
            system_prompt=REVIEWER_SYSTEM,
            user_message=user_msg,
            history=history,
            temperature=0.4,
            max_tokens=6000,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    _save_message(req.session_id, "assistant", response)

    return {"response": response, "type": "review", "session_id": req.session_id}


@router.post("/literature")
async def literature_review(req: LiteratureRequest):
    """文献综述助手"""
    from services.llm_service import call_minimax

    system_prompt = """你是一位文献综述专家，帮助研究者梳理相关文献。

## 输出要求
1. 按主题/方法/时间分类整理相关文献
2. 每篇文献包含：作者(年份) 标题 - 主要发现 - 与本文关系
3. 指出现有文献的空白和不足
4. 建议本文的创新方向

## 文献检索建议
- OpenAlex: https://openalex.org (免费API)
- Google Scholar: 综合性强
- CNKI: 中文文献
- Web of Science: 英文核心期刊

注意：不要编造文献。如果不确定具体文献信息，建议用户到数据库搜索确认。"""

    user_msg = f"研究问题：{req.research_question}"
    if req.keywords:
        user_msg += f"\n关键词：{req.keywords}"
    user_msg += "\n\n请帮我梳理这个领域的文献脉络，指出研究空白，并建议可能的创新方向。"

    history = _get_session_messages(req.session_id)
    _save_message(req.session_id, "user", f"[文献] {req.research_question}")

    def _call():
        return call_minimax(
            system_prompt=system_prompt,
            user_message=user_msg,
            history=history,
            temperature=0.5,
        )

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, _call)

    _save_message(req.session_id, "assistant", response)

    return {"response": response, "type": "literature", "session_id": req.session_id}
