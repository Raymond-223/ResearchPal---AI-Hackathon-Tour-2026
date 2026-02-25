from __future__ import annotations

import json
from typing import Generator
from backend.app.core.cache import cache
from backend.app.core.cache import cache, make_summary_cache_key

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from shared.schemas import (
    PaperParseResponse,
    PaperSummaryRequest,
    PaperSummaryResponse,
    WriteProfileRequest,
    WriteProfileResponse,
    WriteTransferRequest,
    WriteTransferResponse,
    ModelListResponse,
)
from backend.app.services.paper_service import parse_pdf_bytes, summarize_text
from backend.app.services.write_service import profile_text, transfer_text
from backend.app.services.model_service import get_available_models, call_genstudio_chat_stream
from summary_generator import generate_short_summary, generate_long_summary

router = APIRouter()


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    models = get_available_models()
    return {"data": models}



@router.post("/paper/parse", response_model=PaperParseResponse)
async def paper_parse(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    result = parse_pdf_bytes(pdf_bytes)
    return result


@router.post("/paper/summary", response_model=PaperSummaryResponse)
async def paper_summary(req: PaperSummaryRequest):
    # Pass model and language to service
    key = make_summary_cache_key(req.text, req.mode + str(req.model) + req.language)
    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    try:
        result = summarize_text(req.text, req.mode, req.model, req.language)
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
    key_payload = f"{req.target_journal}|{req.formality}|{req.domain}|{req.model}\n{req.text}"
    key = "transfer:" + __import__("hashlib").md5(key_payload.encode("utf-8")).hexdigest()

    cached = cache.get(key)
    if cached:
        return json.loads(cached)

    try:
        result = transfer_text(req.text, req.target_journal, req.formality, req.domain, req.model)
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


# ============== 流式输出端点 ==============

async def generate_summary_stream(text: str, mode: str, model: str, language: str) -> Generator[str, None, None]:
    """
    生成流式摘要输出
    """
    import uuid
    
    # 根据语言选择 prompt
    if language == "zh":
        system_prompt = """你是一位世界级的学术论文分析师。你的专业涵盖计算机科学、数学、物理学、生物学、医学和工程学。你擅长：
1. 将复杂的研究提炼成清晰、简洁的摘要
2. 识别新颖的贡献和创新
3. 精确解释技术方法
4. 评估实验的严谨性和结果
5. 对局限性提供平衡的批评

始终以专业的结构化方式输出内容，使用精确的学术语言，聚焦于研究者最关心的内容。"""
        one_liner_prompt = """分析这篇学术论文，提供一句总结，包含：
- 要解决的具体问题
- 核心的新颖方法或贡献
- 关键的定量或定性结果

示例格式："本文提出了[新颖方法]用于[问题]，在[基准/数据集]上取得了[关键结果]。"

论文文本："""
        detailed_prompt = """请提供这篇学术论文的综合结构化摘要（约400字），涵盖：

1. **背景与动机**（2-3句）：论文解决了什么问题？为什么重要？

2. **核心贡献**（2-3句）：什么是新颖的方法或技术？关键创新点是什么？

3. **方法概述**（3-4句）：方法是如何工作的？主要技术组件是什么？

4. **关键结果**（2-3句）：进行了哪些实验？主要发现和改进是什么？

5. **局限性与未来工作**（1-2句）：论文的局限性是什么？有哪些未来方向？

论文文本："""
    else:
        system_prompt = """You are a world-class academic paper analyst. Your expertise spans computer science, mathematics, physics, biology, medicine, and engineering. You excel at:
1. Distilling complex research into clear, concise summaries
2. Identifying novel contributions and innovations
3. Explaining technical methods with precision
4. Evaluating experimental rigor and results
5. Providing balanced criticism of limitations

Always structure your output professionally, use precise academic language, and focus on what matters most to researchers."""
        one_liner_prompt = """Analyze this academic paper and provide a ONE-SENTENCE summary that captures:
- The specific problem being solved
- The core novel approach or contribution
- The key quantitative or qualitative result

Example format: "This paper presents [novel approach] for [problem], achieving [key result] on [benchmark/dataset]."

Paper text: """
        detailed_prompt = """Provide a comprehensive structured summary of this academic paper (~400 words) covering:

1. **Background & Motivation** (2-3 sentences): What problem does the paper address? Why is it important?

2. **Core Contribution** (2-3 sentences): What is the novel approach or method? What are the key innovations?

3. **Method Summary** (3-4 sentences): How does the approach work? What are the main technical components?

4. **Key Results** (2-3 sentences): What experiments were conducted? What were the main findings and improvements?

5. **Limitations & Future Work** (1-2 sentences): What are the paper's limitations? What future directions are suggested?

Paper text: """

    # 智能截断文本
    truncated_text = _smart_truncate_stream(text)
    request_id = str(uuid.uuid4())

    # 发送请求ID
    yield f"data: {json.dumps({'type': 'start', 'request_id': request_id})}\n\n"

    # One Liner 流式输出
    yield f"data: {json.dumps({'type': 'section', 'name': 'one_liner'})}\n\n"
    messages_one = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": one_liner_prompt + truncated_text}
    ]
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            for chunk in call_genstudio_chat_stream(messages_one, model):
                yield f"data: {json.dumps({'type': 'content', 'section': 'one_liner', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'section': 'one_liner', 'content': f'[Error: {str(e)}]'})}\n\n"
    else:
        # Fallback to local logic
        structured = {"preamble": truncated_text}
        one_liner = generate_short_summary(structured)
        prefix = "【1分钟速览】" if language == "zh" else ""
        for char in (prefix + one_liner):
            yield f"data: {json.dumps({'type': 'content', 'section': 'one_liner', 'content': char})}\n\n"

    # Detailed 流式输出
    yield f"data: {json.dumps({'type': 'section', 'name': 'detailed'})}\n\n"
    messages_detail = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": detailed_prompt + truncated_text}
    ]
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            for chunk in call_genstudio_chat_stream(messages_detail, model):
                yield f"data: {json.dumps({'type': 'content', 'section': 'detailed', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'section': 'detailed', 'content': f'[Error: {str(e)}]'})}\n\n"
    else:
        # Fallback to local logic
        structured = {"preamble": truncated_text}
        long_pack = generate_long_summary(structured)
        detailed = long_pack.get("full_text", "")
        prefix = "【10分钟精读】" if language == "zh" else ""
        for char in (prefix + detailed):
            yield f"data: {json.dumps({'type': 'content', 'section': 'detailed', 'content': char})}\n\n"

    # 完成
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def generate_transfer_stream(text: str, target_journal: str, formality: float, domain: str, model: str) -> Generator[str, None, None]:
    """
    生成流式润色改写输出
    """
    import uuid
    
    request_id = str(uuid.uuid4())
    
    # 发送请求ID
    yield f"data: {json.dumps({'type': 'start', 'request_id': request_id})}\n\n"

    # Rewritten 流式输出
    yield f"data: {json.dumps({'type': 'section', 'name': 'rewritten'})}\n\n"
    
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            messages_rewrite = [
                {"role": "system", "content": "You are an expert academic editor."},
                {"role": "user", "content": f"Rewrite the following text for {target_journal} style (Formality: {formality}, Domain: {domain}):\n\n{text}"}
            ]
            for chunk in call_genstudio_chat_stream(messages_rewrite, model):
                yield f"data: {json.dumps({'type': 'content', 'section': 'rewritten', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'section': 'rewritten', 'content': f'[Error: {str(e)}]'})}\n\n"
    else:
        # Fallback to local logic
        from style_transfer import StyleTransfer
        _style_engine = StyleTransfer()
        try:
            result = _style_engine.transfer_for_api(
                text=text,
                target_journal=target_journal,
                formality=formality,
                domain=domain,
            )
            rewritten = result.get("rewritten", text)
        except:
            rewritten = f"[{target_journal} style, formality={formality:.2f}] {text}"
        
        for char in rewritten:
            yield f"data: {json.dumps({'type': 'content', 'section': 'rewritten', 'content': char})}\n\n"

    # Suggestions 流式输出
    yield f"data: {json.dumps({'type': 'section', 'name': 'suggestions'})}\n\n"
    
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            messages_suggest = [
                {"role": "system", "content": "You are an expert academic editor."},
                {"role": "user", "content": f"Provide 3 brief suggestions to improve the following text for {target_journal}:\n\n{text}"}
            ]
            for chunk in call_genstudio_chat_stream(messages_suggest, model):
                yield f"data: {json.dumps({'type': 'content', 'section': 'suggestions', 'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'content', 'section': 'suggestions', 'content': f'[Error: {str(e)}]'})}\n\n"
    else:
        suggestions = ["Consider adding clearer transitions between sentences.", "Use more precise verbs for claims."]
        for suggestion in suggestions:
            for char in suggestion:
                yield f"data: {json.dumps({'type': 'content', 'section': 'suggestions', 'content': char})}\n\n"

    # 完成
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def _smart_truncate_stream(text: str, max_length: int = 8000) -> str:
    """智能截断文本，优先保留重要部分（摘要、引言、结论）"""
    import re
    abstract_match = re.search(r'(?i)abstract\s*[:\-]?\s*(.{100,1500}?)(?=\n\n|introduction|1\.|I\.)', text)
    intro_match = re.search(r'(?i)(introduction|1\.\s*)[^\n]{10,2000}', text)
    conclusion_match = re.search(r'(?i)(conclusion|discussion|5\.\s*|6\.\s*|related work)[^\n]{10,2000}', text)

    priority_parts = []

    if abstract_match:
        priority_parts.append(abstract_match.group(1).strip())

    if conclusion_match:
        priority_parts.append(conclusion_match.group(0).strip())

    if intro_match:
        priority_parts.append(intro_match.group(0).strip())

    priority_text = "\n\n".join(priority_parts)

    if len(priority_text) >= max_length * 0.6:
        return priority_text[:max_length]

    remaining = max_length - len(priority_text)
    return (priority_text + "\n\n" + text[:remaining])[:max_length]


@router.post("/paper/summary/stream")
async def paper_summary_stream(req: PaperSummaryRequest):
    """流式摘要生成端点"""
    return StreamingResponse(
        generate_summary_stream(req.text, req.mode, req.model, req.language),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/write/transfer/stream")
async def write_transfer_stream(req: WriteTransferRequest):
    """流式润色改写端点"""
    return StreamingResponse(
        generate_transfer_stream(req.text, req.target_journal, req.formality, req.domain, req.model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )