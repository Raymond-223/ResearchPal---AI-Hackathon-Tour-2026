from __future__ import annotations
from typing import Dict, Any
import hashlib
import fitz  # PyMuPDF


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


def summarize_text(text: str, mode: str) -> Dict[str, Any]:
    """
    仍是 mock 摘要：你后面只需要在这里接入算法A的 bart/qwen 即可
    """
    request_id = _rid(text[:50] + mode)
    one_liner = f"【1分钟速览】(mock) This paper proposes an approach in mode={mode}."
    detailed = (
        "【10分钟精读】(mock)\n"
        "- Method: ...\n"
        "- Experiments: ...\n"
        "- Results: ...\n"
    )
    mermaid = """graph TD
A[Paper] --> B[Method]
A --> C[Experiments]
B --> D[Contribution]
"""
    return {
        "request_id": request_id,
        "one_liner": one_liner,
        "detailed": detailed,
        "mermaid": mermaid,
    }