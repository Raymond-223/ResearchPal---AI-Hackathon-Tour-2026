"""
语法检查和优化建议模块
提供基础语法检查和学术写作优化建议
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SuggestionType(Enum):
    """建议类型"""
    GRAMMAR = "grammar"  # 语法错误
    STYLE = "style"  # 风格建议
    SPELLING = "spelling"  # 拼写问题
    PUNCTUATION = "punctuation"  # 标点问题
    WORD_CHOICE = "word_choice"  # 用词建议


@dataclass
class Suggestion:
    """优化建议"""
    type: SuggestionType
    message: str
    original: str
    replacement: Optional[str]
    start: int
    end: int
    severity: str  # "error", "warning", "info"


class GrammarChecker:
    """
    语法检查器
    提供中英文基础语法检查和学术写作优化建议
    """
    
    # 常见学术写作错误模式
    ACADEMIC_PATTERNS = {
        # 口语化表达替换建议
        "word_replacements": {
            "cn": {
                "很多": "大量/众多",
                "所以": "因此/故",
                "但是": "然而/但",
                "而且": "此外/并且",
                "因为": "由于/鉴于",
                "虽然": "尽管",
                "这样": "如此/这般",
                "怎么": "如何",
                "好像": "似乎",
                "大概": "约/大约",
                "一些": "若干/部分",
            },
            "en": {
                "a lot of": "numerous/substantial",
                "lots of": "many/numerous",
                "big": "significant/substantial",
                "small": "minor/minimal",
                "good": "favorable/positive",
                "bad": "unfavorable/negative",
                "get": "obtain/acquire",
                "show": "demonstrate/illustrate",
                "give": "provide/present",
                "make": "create/construct",
                "use": "utilize/employ",
                "find": "identify/discover",
                "look at": "examine/investigate",
            }
        },
        # 冗余表达
        "redundant_phrases": {
            "cn": ["首先第一", "最后最终", "重新再次", "完全彻底", "目前现在"],
            "en": ["first and foremost", "each and every", "basic fundamentals", 
                   "future plans", "past history", "true facts", "end result"]
        },
        # 模糊表达（应避免）
        "vague_phrases": {
            "cn": ["一定程度上", "某种意义上", "在某些方面", "可能会", "也许"],
            "en": ["to some extent", "in some ways", "kind of", "sort of", "more or less"]
        }
    }
    
    # 中文标点规则
    CN_PUNCTUATION_RULES = [
        (r'\.{3,}', '……', '省略号应使用中文省略号'),
        (r'[,](?=[\u4e00-\u9fff])', '，', '中文语境应使用中文逗号'),
        (r'[:](?=[\u4e00-\u9fff])', '：', '中文语境应使用中文冒号'),
        (r'[;](?=[\u4e00-\u9fff])', '；', '中文语境应使用中文分号'),
    ]
    
    # 英文标点规则
    EN_PUNCTUATION_RULES = [
        (r'，(?=[a-zA-Z])', ',', '英文语境应使用英文逗号'),
        (r'：(?=[a-zA-Z])', ':', '英文语境应使用英文冒号'),
        (r'；(?=[a-zA-Z])', ';', '英文语境应使用英文分号'),
        (r'\s+,', ',', '逗号前不应有空格'),
        (r',(?=[^\s])', ', ', '逗号后应有空格'),
    ]
    
    def __init__(self, use_language_tool: bool = False):
        """
        初始化语法检查器
        
        Args:
            use_language_tool: 是否使用LanguageTool（英文检查增强）
        """
        self.use_language_tool = use_language_tool
        self._language_tool = None
        
        if use_language_tool:
            self._init_language_tool()
    
    def _init_language_tool(self):
        """初始化LanguageTool"""
        try:
            import language_tool_python
            self._language_tool = language_tool_python.LanguageTool('en-US')
        except Exception as e:
            print(f"LanguageTool加载失败: {e}")
            self.use_language_tool = False
    
    def check(self, text: str) -> List[Suggestion]:
        """
        检查文本并返回优化建议
        
        Args:
            text: 输入文本
            
        Returns:
            List[Suggestion]: 优化建议列表
        """
        suggestions = []
        
        # 检测文本语言
        is_chinese = self._is_chinese_text(text)
        
        # 标点符号检查
        suggestions.extend(self._check_punctuation(text, is_chinese))
        
        # 用词优化建议
        suggestions.extend(self._check_word_choice(text, is_chinese))
        
        # 冗余表达检查
        suggestions.extend(self._check_redundancy(text, is_chinese))
        
        # 模糊表达检查
        suggestions.extend(self._check_vague_expressions(text, is_chinese))
        
        # 英文额外检查（使用LanguageTool）
        if not is_chinese and self.use_language_tool and self._language_tool:
            suggestions.extend(self._check_with_language_tool(text))
        
        # 按位置排序
        suggestions.sort(key=lambda x: x.start)
        
        return suggestions
    
    def _is_chinese_text(self, text: str) -> bool:
        """判断文本是否主要为中文"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        return chinese_chars > english_chars
    
    def _check_punctuation(self, text: str, is_chinese: bool) -> List[Suggestion]:
        """检查标点符号"""
        suggestions = []
        rules = self.CN_PUNCTUATION_RULES if is_chinese else self.EN_PUNCTUATION_RULES
        
        for pattern, replacement, message in rules:
            for match in re.finditer(pattern, text):
                suggestions.append(Suggestion(
                    type=SuggestionType.PUNCTUATION,
                    message=message,
                    original=match.group(),
                    replacement=replacement,
                    start=match.start(),
                    end=match.end(),
                    severity="warning"
                ))
        
        return suggestions
    
    def _check_word_choice(self, text: str, is_chinese: bool) -> List[Suggestion]:
        """检查用词并提供替换建议"""
        suggestions = []
        lang = "cn" if is_chinese else "en"
        replacements = self.ACADEMIC_PATTERNS["word_replacements"][lang]
        
        for word, better in replacements.items():
            if is_chinese:
                for match in re.finditer(re.escape(word), text):
                    suggestions.append(Suggestion(
                        type=SuggestionType.WORD_CHOICE,
                        message=f"建议将「{word}」替换为更学术的表达：{better}",
                        original=word,
                        replacement=better.split('/')[0],
                        start=match.start(),
                        end=match.end(),
                        severity="info"
                    ))
            else:
                pattern = r'\b' + re.escape(word) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    suggestions.append(Suggestion(
                        type=SuggestionType.WORD_CHOICE,
                        message=f"Consider replacing '{word}' with: {better}",
                        original=match.group(),
                        replacement=better.split('/')[0],
                        start=match.start(),
                        end=match.end(),
                        severity="info"
                    ))
        
        return suggestions
    
    def _check_redundancy(self, text: str, is_chinese: bool) -> List[Suggestion]:
        """检查冗余表达"""
        suggestions = []
        lang = "cn" if is_chinese else "en"
        phrases = self.ACADEMIC_PATTERNS["redundant_phrases"][lang]
        
        for phrase in phrases:
            if is_chinese:
                if phrase in text:
                    idx = text.find(phrase)
                    suggestions.append(Suggestion(
                        type=SuggestionType.STYLE,
                        message=f"「{phrase}」是冗余表达，建议简化",
                        original=phrase,
                        replacement=None,
                        start=idx,
                        end=idx + len(phrase),
                        severity="warning"
                    ))
            else:
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    suggestions.append(Suggestion(
                        type=SuggestionType.STYLE,
                        message=f"'{phrase}' is redundant, consider simplifying",
                        original=match.group(),
                        replacement=None,
                        start=match.start(),
                        end=match.end(),
                        severity="warning"
                    ))
        
        return suggestions
    
    def _check_vague_expressions(self, text: str, is_chinese: bool) -> List[Suggestion]:
        """检查模糊表达"""
        suggestions = []
        lang = "cn" if is_chinese else "en"
        phrases = self.ACADEMIC_PATTERNS["vague_phrases"][lang]
        
        for phrase in phrases:
            if is_chinese:
                if phrase in text:
                    idx = text.find(phrase)
                    suggestions.append(Suggestion(
                        type=SuggestionType.STYLE,
                        message=f"「{phrase}」表达模糊，学术写作应更精确",
                        original=phrase,
                        replacement=None,
                        start=idx,
                        end=idx + len(phrase),
                        severity="info"
                    ))
            else:
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    suggestions.append(Suggestion(
                        type=SuggestionType.STYLE,
                        message=f"'{phrase}' is vague, be more specific in academic writing",
                        original=match.group(),
                        replacement=None,
                        start=match.start(),
                        end=match.end(),
                        severity="info"
                    ))
        
        return suggestions
    
    def _check_with_language_tool(self, text: str) -> List[Suggestion]:
        """使用LanguageTool进行英文检查"""
        suggestions = []
        
        if not self._language_tool:
            return suggestions
        
        try:
            matches = self._language_tool.check(text)
            for match in matches:
                suggestions.append(Suggestion(
                    type=SuggestionType.GRAMMAR,
                    message=match.message,
                    original=text[match.offset:match.offset + match.errorLength],
                    replacement=match.replacements[0] if match.replacements else None,
                    start=match.offset,
                    end=match.offset + match.errorLength,
                    severity="error" if "error" in match.ruleId.lower() else "warning"
                ))
        except Exception as e:
            print(f"LanguageTool检查失败: {e}")
        
        return suggestions
    
    def apply_suggestions(self, text: str, suggestions: List[Suggestion]) -> str:
        """
        应用优化建议到文本
        
        Args:
            text: 原始文本
            suggestions: 要应用的建议列表（需要有replacement）
            
        Returns:
            str: 优化后的文本
        """
        # 按位置倒序排列，从后往前替换避免位置偏移
        applicable = [s for s in suggestions if s.replacement]
        applicable.sort(key=lambda x: x.start, reverse=True)
        
        result = text
        for suggestion in applicable:
            result = result[:suggestion.start] + suggestion.replacement + result[suggestion.end:]
        
        return result
    
    def to_dict(self, suggestions: List[Suggestion]) -> List[Dict[str, Any]]:
        """将建议列表转换为字典格式（供API返回）"""
        return [
            {
                "type": s.type.value,
                "message": s.message,
                "original": s.original,
                "replacement": s.replacement,
                "position": {"start": s.start, "end": s.end},
                "severity": s.severity
            }
            for s in suggestions
        ]
