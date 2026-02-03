"""
学术写作风格迁移模块 - FastAPI接口
供全栈工程师集成调用
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core.text_analyzer import TextAnalyzer
from ..core.style_scorer import StyleScorer, AcademicDomain
from ..core.grammar_checker import GrammarChecker
from ..core.style_transfer import StyleTransfer, JournalStyle
from ..core.version_diff import VersionDiff


# ============ 请求/响应模型 ============

class TextAnalyzeRequest(BaseModel):
    """文本分析请求"""
    text: str = Field(..., description="待分析文本", min_length=1)


class TextAnalyzeResponse(BaseModel):
    """文本分析响应"""
    tokens: List[dict]
    sentences: List[str]
    statistics: dict


class StyleScoreRequest(BaseModel):
    """风格评分请求"""
    text: str = Field(..., description="待评分文本", min_length=1)
    domain: str = Field(default="general", description="学术领域")


class StyleScoreResponse(BaseModel):
    """风格评分响应"""
    scores: dict
    details: dict
    suggestions: List[str]


class GrammarCheckRequest(BaseModel):
    """语法检查请求"""
    text: str = Field(..., description="待检查文本", min_length=1)


class GrammarCheckResponse(BaseModel):
    """语法检查响应"""
    suggestions: List[dict]
    corrected_text: Optional[str] = None


class StyleTransferRequest(BaseModel):
    """风格迁移请求"""
    text: str = Field(..., description="待迁移文本", min_length=1)
    target_style: str = Field(default="general", description="目标期刊风格")


class StyleTransferResponse(BaseModel):
    """风格迁移响应"""
    original: str
    transferred: str
    target_style: str
    changes: List[str]
    confidence: float


class VersionSaveRequest(BaseModel):
    """版本保存请求"""
    document_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文本内容")
    label: Optional[str] = Field(None, description="版本标签")
    style: Optional[str] = Field(None, description="风格标记")


class VersionCompareRequest(BaseModel):
    """版本对比请求"""
    text_a: str = Field(..., description="原文本")
    text_b: str = Field(..., description="新文本")
    char_level: bool = Field(default=True, description="是否字符级对比")


class DiffResponse(BaseModel):
    """差异对比响应"""
    similarity: float
    html_diff: str
    summary: dict
    segments: List[dict]


# ============ 路由器定义 ============

router = APIRouter(prefix="/writing", tags=["学术写作风格迁移"])

# 初始化核心服务（使用简单模式避免模型加载问题）
text_analyzer = TextAnalyzer(use_modelscope=False)
style_scorer = StyleScorer(analyzer=text_analyzer)
grammar_checker = GrammarChecker(use_language_tool=False)
style_transfer = StyleTransfer(use_modelscope=False)
version_diff = VersionDiff()


@router.post("/analyze", response_model=TextAnalyzeResponse, summary="文本分析")
async def analyze_text(request: TextAnalyzeRequest):
    """
    分析文本，返回分词、词性标注、统计信息
    """
    try:
        result = text_analyzer.analyze(request.text)
        return text_analyzer.to_dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score", response_model=StyleScoreResponse, summary="风格评分")
async def score_style(request: StyleScoreRequest):
    """
    评估文本的学术写作风格
    返回正式程度、被动语态比例、术语匹配度等指标
    """
    try:
        # 解析领域
        domain = AcademicDomain.GENERAL
        for d in AcademicDomain:
            if d.value == request.domain:
                domain = d
                break
        
        result = style_scorer.score(request.text, domain)
        return style_scorer.to_dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=GrammarCheckResponse, summary="语法检查")
async def check_grammar(request: GrammarCheckRequest):
    """
    检查文本语法，返回优化建议
    """
    try:
        suggestions = grammar_checker.check(request.text)
        corrected = grammar_checker.apply_suggestions(request.text, suggestions)
        
        return {
            "suggestions": grammar_checker.to_dict(suggestions),
            "corrected_text": corrected if corrected != request.text else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfer", response_model=StyleTransferResponse, summary="风格迁移")
async def transfer_style(request: StyleTransferRequest):
    """
    将文本转换为目标期刊风格
    支持: nature, science, acl, ieee, general
    """
    try:
        # 解析目标风格
        target = JournalStyle.GENERAL_ACADEMIC
        for s in JournalStyle:
            if s.value == request.target_style:
                target = s
                break
        
        result = style_transfer.transfer(request.text, target)
        return style_transfer.to_dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles", summary="获取可用风格列表")
async def list_styles():
    """
    获取所有支持的期刊风格
    """
    return {
        "styles": style_transfer.list_available_styles()
    }


@router.get("/domains", summary="获取学术领域列表")
async def list_domains():
    """
    获取所有支持的学术领域
    """
    return {
        "domains": [
            {"id": d.value, "name": d.name}
            for d in AcademicDomain
        ]
    }


@router.post("/version/save", summary="保存版本")
async def save_version(request: VersionSaveRequest):
    """
    保存文本版本
    """
    try:
        version = version_diff.save_version(
            request.document_id,
            request.content,
            request.label,
            request.style
        )
        return version_diff.version_to_dict(version)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{document_id}", summary="获取版本列表")
async def get_versions(document_id: str):
    """
    获取文档的所有历史版本
    """
    try:
        versions = version_diff.get_versions(document_id)
        return {
            "document_id": document_id,
            "versions": [version_diff.version_to_dict(v) for v in versions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diff", response_model=DiffResponse, summary="文本对比")
async def compare_texts(request: VersionCompareRequest):
    """
    对比两个文本，返回差异高亮
    """
    try:
        result = version_diff.compare(
            request.text_a,
            request.text_b,
            request.char_level
        )
        return version_diff.to_dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/version/{document_id}", summary="清除版本历史")
async def clear_versions(document_id: str):
    """
    清除文档的所有版本历史
    """
    try:
        version_diff.clear_versions(document_id)
        return {"message": f"已清除文档 {document_id} 的所有版本"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 综合接口 ============

class FullAnalysisRequest(BaseModel):
    """综合分析请求"""
    text: str = Field(..., description="待分析文本")
    domain: str = Field(default="general", description="学术领域")
    target_style: Optional[str] = Field(None, description="目标风格（可选）")


@router.post("/full-analysis", summary="综合分析")
async def full_analysis(request: FullAnalysisRequest):
    """
    一次性完成文本分析、风格评分、语法检查
    可选：同时进行风格迁移
    """
    try:
        # 文本分析
        analysis = text_analyzer.analyze(request.text)
        
        # 风格评分
        domain = AcademicDomain.GENERAL
        for d in AcademicDomain:
            if d.value == request.domain:
                domain = d
                break
        score = style_scorer.score(request.text, domain)
        
        # 语法检查
        grammar_suggestions = grammar_checker.check(request.text)
        
        result = {
            "analysis": text_analyzer.to_dict(analysis),
            "style_score": style_scorer.to_dict(score),
            "grammar": {
                "suggestions": grammar_checker.to_dict(grammar_suggestions),
                "suggestion_count": len(grammar_suggestions)
            }
        }
        
        # 可选：风格迁移
        if request.target_style:
            target = JournalStyle.GENERAL_ACADEMIC
            for s in JournalStyle:
                if s.value == request.target_style:
                    target = s
                    break
            transfer_result = style_transfer.transfer(request.text, target)
            result["transfer"] = style_transfer.to_dict(transfer_result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
