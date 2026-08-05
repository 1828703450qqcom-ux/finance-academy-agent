import json
import uuid
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from database import SessionLocal, ChatHistory
from schemas import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = """你是金融学院AI助手，专精以下领域：
1. 金融学术研究：实证分析、计量经济学、面板数据
2. 量化投资：因子模型、回测策略、风险管理
3. 财务分析：杜邦分析、财务报表解读、估值模型
4. 宏观经济：中国及全球宏观数据解读
5. 学术论文：文献检索、综述写作、研究方法

请用专业但易懂的方式回答问题。如果涉及数据分析，请给出具体的解读和建议。
回答时可以使用Markdown格式，包括表格、列表、加粗等。"""


def generate_response(message: str, history: list = None) -> str:
    from services.llm_service import call_minimax
    return call_minimax(
        system_prompt=SYSTEM_PROMPT,
        user_message=message,
        history=history,
        temperature=0.7,
        max_tokens=2048,
        timeout=60,
    )


@router.post("/send")
async def send_message(req: ChatRequest):
    db = SessionLocal()
    try:
        user_msg = ChatHistory(
            session_id=req.session_id,
            role="user",
            content=req.message,
        )
        db.add(user_msg)
        db.commit()

        # 获取最近10条对话历史作为上下文
        recent = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == req.session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(20)
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in reversed(recent[:-1])]

        response = generate_response(req.message, history)

        assistant_msg = ChatHistory(
            session_id=req.session_id,
            role="assistant",
            content=response,
        )
        db.add(assistant_msg)
        db.commit()

        return {"response": response, "session_id": req.session_id}
    finally:
        db.close()


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    db = SessionLocal()
    try:
        messages = (
            db.query(ChatHistory)
            .filter(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at)
            .all()
        )
        return {
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ]
        }
    finally:
        db.close()


@router.post("/session")
async def create_session():
    return {"session_id": str(uuid.uuid4())}
