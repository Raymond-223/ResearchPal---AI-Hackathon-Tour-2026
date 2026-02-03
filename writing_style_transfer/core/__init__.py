"""
Core模块导出
"""

from .text_analyzer import TextAnalyzer, TokenInfo, AnalysisResult
from .style_scorer import StyleScorer, StyleScore, AcademicDomain
from .grammar_checker import GrammarChecker, Suggestion, SuggestionType
from .style_transfer import StyleTransfer, TransferResult, JournalStyle
from .version_diff import VersionDiff, DiffResult, TextVersion, DiffType

__all__ = [
    # 文本分析
    'TextAnalyzer', 'TokenInfo', 'AnalysisResult',
    
    # 风格评分
    'StyleScorer', 'StyleScore', 'AcademicDomain',
    
    # 语法检查
    'GrammarChecker', 'Suggestion', 'SuggestionType',
    
    # 风格迁移
    'StyleTransfer', 'TransferResult', 'JournalStyle',
    
    # 版本对比
    'VersionDiff', 'DiffResult', 'TextVersion', 'DiffType'
]
