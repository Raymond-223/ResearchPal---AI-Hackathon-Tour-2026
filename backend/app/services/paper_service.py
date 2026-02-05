
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
from typing import Dict, Any

def summarize_text(text: str, mode: str = "mvp") -> Dict[str, Any]:
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