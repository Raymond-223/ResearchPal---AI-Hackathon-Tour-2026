# 学术写作风格迁移模块
# 算法工程师B负责模块

from .core.text_analyzer import TextAnalyzer
from .core.style_scorer import StyleScorer
from .core.grammar_checker import GrammarChecker
from .core.style_transfer import StyleTransfer
from .core.version_diff import VersionDiff

__version__ = "1.0.0"
__all__ = [
    "TextAnalyzer",
    "StyleScorer", 
    "GrammarChecker",
    "StyleTransfer",
    "VersionDiff"
]
