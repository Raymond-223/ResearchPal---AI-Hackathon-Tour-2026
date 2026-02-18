from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., example="INTERNAL_ERROR")
    message: str = Field(..., example="Something went wrong")
    detail: Optional[Dict[str, Any]] = None
    request_id: str


# -------- Paper --------
class PaperParseResponse(BaseModel):
    request_id: str
    title: Optional[str] = None
    authors: List[str] = []
    abstract: Optional[str] = None
    sections: List[Dict[str, Any]] = []  # e.g. [{"name":"Introduction","text":"..."}]
    full_text: str


class PaperSummaryRequest(BaseModel):
    text: str
    mode: str = Field("mvp", description="mvp|fast|deep")


class PaperSummaryResponse(BaseModel):
    request_id: str
    one_liner: str
    detailed: str
    mermaid: str  # simple citation/idea graph in mermaid


# -------- Writing --------
class WriteProfileRequest(BaseModel):
    text: str
    domain: str = "cs"


class WriteProfileResponse(BaseModel):
    request_id: str
    lexical: Dict[str, Any]
    structural: Dict[str, Any]
    diagnostics: List[str]


class WriteTransferRequest(BaseModel):
    text: str
    target_journal: str = "Nature"
    formality: float = 0.85  # 0~1
    domain: str = "cs"


class WriteTransferResponse(BaseModel):
    request_id: str
    rewritten: str
    suggestions: List[str]