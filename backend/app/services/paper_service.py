
from __future__ import annotations
from typing import Dict, Any
import hashlib
import fitz  # PyMuPDF

from summary_generator import generate_short_summary, generate_long_summary
def _rid(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:10]


def parse_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    MVP可用版：
    - 用 PyMuPDF 提取全文文本
    - 章节先给一个粗切（可被算法A替换为更准的section识别）
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    full_text = "\n".join(pages_text).strip()

    # 简单兜底：如果抽不出文本，给提示（演示不会空白）
    if not full_text:
        full_text = "⚠️ 未能从PDF提取到可读文本（可能是扫描版/图片PDF）。请换一篇可复制文本的PDF，或后续接OCR。"

    # 粗略“章节”切分（后续算法A可替换）
    sections = [{"name": "Full Text", "text": full_text}]

    request_id = _rid(str(len(pdf_bytes)) + full_text[:200])
    return {
        "request_id": request_id,
        "title": None,
        "authors": [],
        "abstract": None,
        "sections": sections,
        "full_text": full_text,
    }


import uuid
from typing import Dict, Any, Optional
import uuid
from backend.app.services.model_service import call_genstudio_chat

def summarize_text(text: str, mode: str = "mvp", model: Optional[str] = None) -> Dict[str, Any]:
    # 1. Try GenStudio API if model is specified
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            # Simple strategy: call twice for one-liner and detailed
            # Truncate text to avoid context limit issues (simple approach)
            truncated_text = text[:8000] 
            
            # One Liner
            messages_one = [
                {"role": "system", "content": "You are a helpful academic assistant."},
                {"role": "user", "content": f"Please provide a one-sentence summary of the following paper text:\n\n{truncated_text}"}
            ]
            one_liner = call_genstudio_chat(messages_one, model)
            
            # Detailed
            messages_detail = [
                {"role": "system", "content": "You are a helpful academic assistant."},
                {"role": "user", "content": f"Please provide a detailed summary (about 300 words) of the following paper text, covering the key contributions, methods, and results:\n\n{truncated_text}"}
            ]
            detailed = call_genstudio_chat(messages_detail, model)
            
            # Mermaid (Optional, prompt engineering required)
            # For now, fallback to empty or mock for graph
            mermaid = ""
            
            return {
                "request_id": str(uuid.uuid4()),
                "one_liner": one_liner,
                "detailed": detailed,
                "mermaid": mermaid,
            }
        except Exception as e:
            print(f"GenStudio API call failed: {e}. Falling back to local logic.")
            # Fallback to local logic below

    # 2. Local Mock Logic (Fallback)
    structured = {"preamble": text}

    one_liner = generate_short_summary(structured)

    long_pack = generate_long_summary(structured)
    # long_pack = {"sections": {...}, "full_text": "..."}
    detailed = long_pack.get("full_text", "")

    # 先保持你们现有 mermaid 生成逻辑；如果没有就返回空字符串
    mermaid = ""  # or your existing mermaid builder

    return {
        "request_id": str(uuid.uuid4()),
        "one_liner": f"【1分钟速览】{one_liner}",
        "detailed": f"【10分钟精读】{detailed}",
        "mermaid": mermaid,
    }