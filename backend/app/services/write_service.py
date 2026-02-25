from __future__ import annotations
from typing import Dict, Any, List, Optional
import uuid
from backend.app.services.model_service import call_genstudio_chat
import hashlib
import re
import os
import sys

# allow importing from repo root (style_transfer.py is at repo root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from style_transfer import StyleTransfer

_style_engine = StyleTransfer()

def _rid(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:10]


def profile_text(text: str, domain: str) -> Dict[str, Any]:
    request_id = _rid(text[:50] + domain)

    # 超轻量MVP：粗略指标（后续算法B替换为 BERT/规则+统计）
    passive_hits = len(re.findall(r"\bwas\b|\bwere\b|\bbeen\b", text.lower()))
    tokens = max(1, len(re.findall(r"\w+", text)))
    passive_ratio = min(1.0, passive_hits / tokens * 10)

    lexical = {
        "formality_score": 0.75,
        "sentence_complexity": 0.60,
        "domain_terms": ["transformer", "attention"] if domain == "cs" else [],
    }
    structural = {
        "passive_ratio": round(passive_ratio, 3),
        "transition_words": 2.0,
        "paragraph_structure": "IMRaD",
    }
    diagnostics = [
        "Consider adding clearer transitions between sentences.",
        "Use more precise verbs for claims (e.g., demonstrate/validate).",
    ]
    return {
        "request_id": request_id,
        "lexical": lexical,
        "structural": structural,
        "diagnostics": diagnostics,
    }


def _get_formality_description(formality: float) -> str:
    """根据 formality 值生成详细的风格描述"""
    if formality >= 0.9:
        return "极其正式 - 使用最规范的学术语言，避免任何口语化表达，使用复杂的从句结构，极少量使用缩约词"
    elif formality >= 0.7:
        return "高度正式 - 使用规范的学术语言，避免口语化表达，使用适当的从句结构，少量使用被动语态"
    elif formality >= 0.5:
        return "中等正式 - 保持学术专业性，适度使用复杂句式，平衡使用主动和被动语态"
    elif formality >= 0.3:
        return "口语化 - 使用通俗易懂的表达，以简单句为主，可以使用日常用语和缩约词"
    elif formality >= 0.1:
        return "很口语化 - 使用不正经的表达，使用各种日常用语，并引用网络梗和俚语，展现幽默感"
    else:
        return "极其口语化 - 使用极不正经的表达，并引用尽可能多的网络梗和俚语，极尽幽默感，想方设法逗乐读者"


def transfer_text(text: str, target_journal: str, formality: float, domain: str, model: Optional[str] = None) -> Dict[str, Any]:
    # 1. Try GenStudio API if model is specified
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            # 生成详细的正式程度描述
            formality_desc = _get_formality_description(formality)
            # Rewrite
            messages_rewrite = [
                {"role": "system", "content": "You are an expert academic editor."},
                {"role": "user", "content": f"""Rewrite the following academic text for {target_journal} style.

【Target Style】: {target_journal}
【Domain】: {domain}
【Formality Level】: {formality_desc}

Original Text:
{text}

Please rewrite the text above to match the target journal style while maintaining the formality level specified. Keep the original meaning intact."""}
            ]
            rewritten = call_genstudio_chat(messages_rewrite, model)

            # Suggestions
            messages_suggest = [
                {"role": "system", "content": "You are an expert academic editor."},
                {"role": "user", "content": f"""Provide 3 brief suggestions to improve the following text for {target_journal} style with formality level: {formality_desc}

Original Text:
{text}

Provide your suggestions in a concise format."""}
            ]
            suggestions_text = call_genstudio_chat(messages_suggest, model)
            suggestions = [line.strip('- *') for line in suggestions_text.split('\n') if line.strip()]
            
            return {
                "request_id": str(uuid.uuid4()),
                "rewritten": rewritten,
                "suggestions": suggestions
            }
        except Exception as e:
            print(f"GenStudio rewrite failed: {e}. Falling back to local logic.")
            # Fallback to local logic

    # 2. Local Mock Logic (Fallback)
    try:
        return _style_engine.transfer_for_api(
            text=text,
            target_journal=target_journal,
            formality=formality,
            domain=domain,
        )
    except Exception as e:
        return {
            "request_id": "fallback",
            "rewritten": f"[{target_journal} style, formality={formality:.2f}] {text}",
            "suggestions": [f"Fallback: style transfer failed: {type(e).__name__}"],
        }