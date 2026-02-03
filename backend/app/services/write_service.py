from __future__ import annotations
from typing import Dict, Any, List
import hashlib
import re


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


def transfer_text(text: str, target_journal: str, formality: float, domain: str) -> Dict[str, Any]:
    request_id = _rid(text[:50] + target_journal + str(formality) + domain)

    # MVP：先做“模板化改写”占位，后续接 qwen-7b-chat
    rewritten = (
        f"[{target_journal} style, formality={formality:.2f}] "
        + text.replace("shows", "demonstrates").replace("we", "we (the authors)")
    )
    suggestions = [
        "Prefer passive voice in methods when appropriate.",
        "Add a contrast sentence: 'Unlike previous work, ...'.",
        "Quantify improvements with exact numbers if available.",
    ]
    return {
        "request_id": request_id,
        "rewritten": rewritten,
        "suggestions": suggestions,
    }