from __future__ import annotations

import json
from backend.app.core.cache import cache
from backend.app.core.cache import cache, make_summary_cache_key

from fastapi import APIRouter, UploadFile, File
from shared.schemas import (
    PaperParseResponse,
    PaperSummaryRequest,
    PaperSummaryResponse,
    WriteProfileRequest,
    WriteProfileResponse,
    WriteTransferRequest,
    WriteTransferResponse,
)
from backend.app.services.paper_service import parse_pdf_bytes, summarize_text
from backend.app.services.write_service import profile_text, transfer_text

router = APIRouter()


@router.post("/paper/parse", response_model=PaperParseResponse)
async def paper_parse(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    result = parse_pdf_bytes(pdf_bytes)
    return result


@router.post("/paper/summary", response_model=PaperSummaryResponse)
async def paper_summary(req: PaperSummaryRequest):
    key = make_summary_cache_key(req.text, req.mode)
    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    try:
        result = summarize_text(req.text, req.mode)
        cache.set(key, json.dumps(result))
        return result
    except Exception:
        # 降级：不让接口炸掉
        fallback = {
            "request_id": "fallback",
            "one_liner": "【1分钟速览】(fallback) 摘要服务暂不可用，已返回降级结果。",
            "detailed": "请稍后重试；或切换到缓存/简版摘要。",
            "mermaid": "graph TD\nA[Paper]-->B[Fallback]\n",
        }
        return fallback


@router.post("/write/profile", response_model=WriteProfileResponse)
async def write_profile(req: WriteProfileRequest):
    result = profile_text(req.text, req.domain)
    return result


@router.post("/write/transfer", response_model=WriteTransferResponse)
async def write_transfer(req: WriteTransferRequest):
    # cache key
    key_payload = f"{req.target_journal}|{req.formality}|{req.domain}\n{req.text}"
    key = "transfer:" + __import__("hashlib").md5(key_payload.encode("utf-8")).hexdigest()

    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    try:
        result = transfer_text(req.text, req.target_journal, req.formality, req.domain)
        cache.set(key, json.dumps(result))
        return result
    except Exception:
        # fallback: never 500 during demo
        fallback = {
            "request_id": "fallback",
            "rewritten": f"[{req.target_journal} style fallback] 写作迁移服务暂不可用，已返回降级改写结果。",
            "suggestions": [
                "稍后重试；或降低输入长度。",
                "检查模型服务是否可用/是否超时。",
            ],
        }
        return fallback