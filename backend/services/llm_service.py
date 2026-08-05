"""
MiniMax LLM Service
调用 MiniMax-M2.7-highspeed 模型
"""
import os
import requests
import json
import time
import re
from typing import List, Dict, Optional


MINIMAX_API_URL = os.getenv("MINIMAX_API_URL", "https://minimax.chat/v1/chat/completions")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7-highspeed")


def _clean_response(text: str) -> str:
    """清理AI响应中的特殊标记和乱码"""
    if not text:
        return ""
    import logging
    logger = logging.getLogger("llm_service")
    logger.warning(f"RAW_LLM_RESPONSE: {text[:500]}")
    # 移除<think>...</think>思考标签（多种变体）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 移除特殊token标记 <|...|>
    text = re.sub(r'<\|[^\|]*\|>', '', text)
    # 移除 [INST] / <<SYS>> 等对话模板标记
    text = re.sub(r'\[INST\].*?\[/INST\]', '', text, flags=re.DOTALL)
    text = re.sub(r'<<SYS>>.*?<</SYS>>', '', text, flags=re.DOTALL)
    # 移除控制字符（保留换行、空格、中英文、标点）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # 合并多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    cleaned = text.strip()
    logger.warning(f"CLEANED_LLM_RESPONSE: {cleaned[:500]}")
    # 如果清理后为空但原文不为空，返回原文（避免误删有效内容）
    if not cleaned and text.strip():
        logger.warning("CLEANED_TO_EMPTY, returning original")
        return text.strip()
    return cleaned


def call_minimax(
    system_prompt: str,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = 60,
) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MINIMAX_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(3):
        try:
            resp = requests.post(MINIMAX_API_URL, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                return _clean_response(content)
            elif "error" in data:
                return f"[AI服务错误] {data['error'].get('message', str(data['error']))}"
            else:
                return "[AI服务返回为空，请稍后重试]"

        except requests.exceptions.Timeout:
            if attempt < 2:
                time.sleep(3)
                continue
            return "[AI服务响应超时，请稍后重试]"
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                time.sleep(3)
                continue
            return "[AI服务连接失败，请检查网络]"
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            return f"[AI服务异常] {str(e)}"

    return "[AI服务请求失败，请稍后重试]"


def call_minimax_structured(
    system_prompt: str,
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> Optional[Dict]:
    response = call_minimax(
        system_prompt=system_prompt,
        user_message=user_message,
        history=history,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except (json.JSONDecodeError, TypeError):
        return None
