"""
多版本对比模块
实现历史版本保存和文本差异高亮
"""

import difflib
import hashlib
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class DiffType(Enum):
    """差异类型"""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    EQUAL = "equal"


@dataclass
class DiffSegment:
    """差异片段"""
    type: DiffType
    original: str
    modified: str
    start_pos: int
    end_pos: int


@dataclass
class TextVersion:
    """文本版本"""
    version_id: str
    content: str
    timestamp: str
    label: Optional[str]
    style: Optional[str]  # 如果是风格迁移后的版本，记录目标风格


@dataclass
class DiffResult:
    """差异对比结果"""
    version_a: str
    version_b: str
    segments: List[DiffSegment]
    similarity: float
    html_diff: str
    summary: Dict[str, int]


class VersionDiff:
    """
    版本对比管理器
    支持文本版本保存、对比和差异高亮
    """
    
    def __init__(self, cache_dir: str = "./cache/versions"):
        """
        初始化版本管理器
        
        Args:
            cache_dir: 版本缓存目录
        """
        self.cache_dir = cache_dir
        self._versions: Dict[str, List[TextVersion]] = {}  # document_id -> versions
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
    
    def save_version(
        self, 
        document_id: str, 
        content: str, 
        label: Optional[str] = None,
        style: Optional[str] = None
    ) -> TextVersion:
        """
        保存新版本
        
        Args:
            document_id: 文档标识
            content: 文本内容
            label: 版本标签（如"原稿"、"优化版"等）
            style: 风格标记
            
        Returns:
            TextVersion: 保存的版本信息
        """
        version_id = self._generate_version_id(content)
        timestamp = datetime.now().isoformat()
        
        version = TextVersion(
            version_id=version_id,
            content=content,
            timestamp=timestamp,
            label=label,
            style=style
        )
        
        if document_id not in self._versions:
            self._versions[document_id] = []
        
        self._versions[document_id].append(version)
        
        # 持久化到文件
        self._save_to_cache(document_id)
        
        return version
    
    def get_versions(self, document_id: str) -> List[TextVersion]:
        """获取文档的所有版本"""
        if document_id not in self._versions:
            self._load_from_cache(document_id)
        return self._versions.get(document_id, [])
    
    def get_version(self, document_id: str, version_id: str) -> Optional[TextVersion]:
        """获取指定版本"""
        versions = self.get_versions(document_id)
        for v in versions:
            if v.version_id == version_id:
                return v
        return None
    
    def compare(
        self, 
        text_a: str, 
        text_b: str,
        char_level: bool = True
    ) -> DiffResult:
        """
        对比两个文本
        
        Args:
            text_a: 原文本
            text_b: 新文本
            char_level: 是否使用字符级对比（默认True）
            
        Returns:
            DiffResult: 对比结果
        """
        if char_level:
            segments = self._char_level_diff(text_a, text_b)
        else:
            segments = self._line_level_diff(text_a, text_b)
        
        # 计算相似度
        similarity = self._calculate_similarity(text_a, text_b)
        
        # 生成HTML高亮
        html_diff = self._generate_html_diff(segments)
        
        # 统计摘要
        summary = self._generate_summary(segments)
        
        return DiffResult(
            version_a=text_a[:50] + "..." if len(text_a) > 50 else text_a,
            version_b=text_b[:50] + "..." if len(text_b) > 50 else text_b,
            segments=segments,
            similarity=similarity,
            html_diff=html_diff,
            summary=summary
        )
    
    def compare_versions(
        self, 
        document_id: str, 
        version_id_a: str, 
        version_id_b: str
    ) -> Optional[DiffResult]:
        """对比两个保存的版本"""
        version_a = self.get_version(document_id, version_id_a)
        version_b = self.get_version(document_id, version_id_b)
        
        if not version_a or not version_b:
            return None
        
        return self.compare(version_a.content, version_b.content)
    
    def _char_level_diff(self, text_a: str, text_b: str) -> List[DiffSegment]:
        """字符级差异对比"""
        segments = []
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        
        position = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                segments.append(DiffSegment(
                    type=DiffType.EQUAL,
                    original=text_a[i1:i2],
                    modified=text_b[j1:j2],
                    start_pos=i1,
                    end_pos=i2
                ))
            elif tag == 'replace':
                segments.append(DiffSegment(
                    type=DiffType.REPLACE,
                    original=text_a[i1:i2],
                    modified=text_b[j1:j2],
                    start_pos=i1,
                    end_pos=i2
                ))
            elif tag == 'delete':
                segments.append(DiffSegment(
                    type=DiffType.DELETE,
                    original=text_a[i1:i2],
                    modified="",
                    start_pos=i1,
                    end_pos=i2
                ))
            elif tag == 'insert':
                segments.append(DiffSegment(
                    type=DiffType.INSERT,
                    original="",
                    modified=text_b[j1:j2],
                    start_pos=i1,
                    end_pos=i1
                ))
        
        return segments
    
    def _line_level_diff(self, text_a: str, text_b: str) -> List[DiffSegment]:
        """行级差异对比"""
        segments = []
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        
        matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
        
        position = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            original = ''.join(lines_a[i1:i2])
            modified = ''.join(lines_b[j1:j2])
            
            if tag == 'equal':
                diff_type = DiffType.EQUAL
            elif tag == 'replace':
                diff_type = DiffType.REPLACE
            elif tag == 'delete':
                diff_type = DiffType.DELETE
            else:  # insert
                diff_type = DiffType.INSERT
            
            segments.append(DiffSegment(
                type=diff_type,
                original=original,
                modified=modified,
                start_pos=sum(len(l) for l in lines_a[:i1]),
                end_pos=sum(len(l) for l in lines_a[:i2])
            ))
        
        return segments
    
    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """计算文本相似度"""
        if not text_a and not text_b:
            return 1.0
        if not text_a or not text_b:
            return 0.0
        
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        return round(matcher.ratio(), 4)
    
    def _generate_html_diff(self, segments: List[DiffSegment]) -> str:
        """生成HTML格式的差异高亮"""
        html_parts = []
        
        for seg in segments:
            if seg.type == DiffType.EQUAL:
                html_parts.append(self._escape_html(seg.original))
            elif seg.type == DiffType.DELETE:
                html_parts.append(
                    f'<span class="diff-delete" style="background:#ffcccc;text-decoration:line-through;">'
                    f'{self._escape_html(seg.original)}</span>'
                )
            elif seg.type == DiffType.INSERT:
                html_parts.append(
                    f'<span class="diff-insert" style="background:#ccffcc;">'
                    f'{self._escape_html(seg.modified)}</span>'
                )
            elif seg.type == DiffType.REPLACE:
                html_parts.append(
                    f'<span class="diff-delete" style="background:#ffcccc;text-decoration:line-through;">'
                    f'{self._escape_html(seg.original)}</span>'
                    f'<span class="diff-insert" style="background:#ccffcc;">'
                    f'{self._escape_html(seg.modified)}</span>'
                )
        
        return ''.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """HTML转义"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;')
            .replace('\n', '<br>')
        )
    
    def _generate_summary(self, segments: List[DiffSegment]) -> Dict[str, int]:
        """生成差异统计摘要"""
        summary = {
            "insertions": 0,
            "deletions": 0,
            "replacements": 0,
            "unchanged_chars": 0,
            "total_changes": 0
        }
        
        for seg in segments:
            if seg.type == DiffType.INSERT:
                summary["insertions"] += len(seg.modified)
            elif seg.type == DiffType.DELETE:
                summary["deletions"] += len(seg.original)
            elif seg.type == DiffType.REPLACE:
                summary["replacements"] += 1
                summary["deletions"] += len(seg.original)
                summary["insertions"] += len(seg.modified)
            else:  # EQUAL
                summary["unchanged_chars"] += len(seg.original)
        
        summary["total_changes"] = (
            summary["insertions"] + 
            summary["deletions"]
        )
        
        return summary
    
    def _generate_version_id(self, content: str) -> str:
        """生成版本ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{content}{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _save_to_cache(self, document_id: str):
        """保存版本到缓存文件"""
        versions = self._versions.get(document_id, [])
        cache_file = os.path.join(self.cache_dir, f"{document_id}.json")
        
        data = [asdict(v) for v in versions]
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_cache(self, document_id: str):
        """从缓存文件加载版本"""
        cache_file = os.path.join(self.cache_dir, f"{document_id}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._versions[document_id] = [
                    TextVersion(**v) for v in data
                ]
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self._versions[document_id] = []
    
    def clear_versions(self, document_id: str):
        """清除文档的所有版本"""
        if document_id in self._versions:
            del self._versions[document_id]
        
        cache_file = os.path.join(self.cache_dir, f"{document_id}.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
    
    def to_dict(self, result: DiffResult) -> Dict[str, Any]:
        """将对比结果转换为字典格式（供API返回）"""
        return {
            "version_a_preview": result.version_a,
            "version_b_preview": result.version_b,
            "similarity": result.similarity,
            "html_diff": result.html_diff,
            "summary": result.summary,
            "segments": [
                {
                    "type": seg.type.value,
                    "original": seg.original,
                    "modified": seg.modified,
                    "position": {"start": seg.start_pos, "end": seg.end_pos}
                }
                for seg in result.segments
            ]
        }
    
    def version_to_dict(self, version: TextVersion) -> Dict[str, Any]:
        """将版本信息转换为字典格式"""
        return {
            "version_id": version.version_id,
            "content": version.content,
            "timestamp": version.timestamp,
            "label": version.label,
            "style": version.style
        }
