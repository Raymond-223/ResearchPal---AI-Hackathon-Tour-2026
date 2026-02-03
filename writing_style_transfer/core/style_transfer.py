"""
学术写作风格迁移模块
使用魔搭Qwen模型实现期刊风格适配
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

try:
    from modelscope import AutoModelForCausalLM, AutoTokenizer
    from modelscope import GenerationConfig
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False


class JournalStyle(Enum):
    """期刊风格枚举"""
    NATURE = "nature"
    SCIENCE = "science"
    ACL = "acl"
    IEEE = "ieee"
    CELL = "cell"
    LANCET = "lancet"
    GENERAL_ACADEMIC = "general"


@dataclass
class TransferResult:
    """风格迁移结果"""
    original_text: str
    transferred_text: str
    target_style: JournalStyle
    changes_made: List[str]
    confidence: float


class StyleTransfer:
    """
    学术写作风格迁移器
    将普通文本转换为特定期刊风格
    """
    
    # 期刊风格特征描述
    STYLE_DESCRIPTIONS = {
        JournalStyle.NATURE: {
            "name": "Nature",
            "characteristics": [
                "简洁有力的开篇",
                "活跃的语态为主",
                "避免过度技术术语",
                "强调研究影响力",
                "段落简短精炼"
            ],
            "prompt_template": """请将以下学术文本改写为Nature期刊风格。Nature风格特点：
1. 开篇直接点明研究意义
2. 语言简洁有力，多用主动语态
3. 避免过多术语，让非专业读者也能理解核心贡献
4. 突出研究的创新性和影响力
5. 段落精炼，逻辑清晰

原文：
{text}

请改写为Nature风格（保持原意，只调整表达方式）："""
        },
        JournalStyle.SCIENCE: {
            "name": "Science",
            "characteristics": [
                "严谨的科学表述",
                "数据驱动的论证",
                "平衡的主被动语态",
                "明确的方法描述"
            ],
            "prompt_template": """请将以下学术文本改写为Science期刊风格。Science风格特点：
1. 严谨准确的科学表述
2. 数据和证据驱动的论证方式
3. 主被动语态平衡使用
4. 方法描述清晰明确
5. 注重实验结果的可重复性

原文：
{text}

请改写为Science风格（保持原意，只调整表达方式）："""
        },
        JournalStyle.ACL: {
            "name": "ACL (计算语言学)",
            "characteristics": [
                "技术细节详尽",
                "形式化描述",
                "基线对比明确",
                "消融实验分析"
            ],
            "prompt_template": """请将以下学术文本改写为ACL会议论文风格。ACL风格特点：
1. 技术细节描述详尽准确
2. 适当使用形式化/数学化表述
3. 明确的基线方法对比
4. 强调实验设置的公平性
5. 结果分析深入，包含消融研究

原文：
{text}

请改写为ACL风格（保持原意，只调整表达方式）："""
        },
        JournalStyle.IEEE: {
            "name": "IEEE",
            "characteristics": [
                "结构化表述",
                "技术规范严格",
                "被动语态为主",
                "图表引用规范"
            ],
            "prompt_template": """请将以下学术文本改写为IEEE期刊风格。IEEE风格特点：
1. 高度结构化的表述方式
2. 技术术语使用规范
3. 被动语态为主，客观严谨
4. 图表和公式引用规范
5. 强调技术实现细节

原文：
{text}

请改写为IEEE风格（保持原意，只调整表达方式）："""
        },
        JournalStyle.GENERAL_ACADEMIC: {
            "name": "通用学术",
            "characteristics": [
                "正式规范",
                "逻辑严密",
                "术语准确",
                "客观中立"
            ],
            "prompt_template": """请将以下文本改写为规范的学术写作风格。学术写作特点：
1. 语言正式规范，避免口语化表达
2. 逻辑结构严密，论证有理有据
3. 术语使用准确专业
4. 保持客观中立的叙述立场
5. 适当使用被动语态

原文：
{text}

请改写为规范学术风格（保持原意，只调整表达方式）："""
        }
    }
    
    def __init__(self, model_name: str = "qwen/Qwen-7B-Chat", use_modelscope: bool = True):
        """
        初始化风格迁移器
        
        Args:
            model_name: 魔搭模型名称
            use_modelscope: 是否使用魔搭模型
        """
        self.model_name = model_name
        self.use_modelscope = use_modelscope and MODELSCOPE_AVAILABLE
        self._model = None
        self._tokenizer = None
        
        if self.use_modelscope:
            self._init_model()
    
    def _init_model(self):
        """初始化Qwen模型"""
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                trust_remote_code=True
            ).eval()
            print(f"模型 {self.model_name} 加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            self.use_modelscope = False
    
    def transfer(
        self, 
        text: str, 
        target_style: JournalStyle = JournalStyle.GENERAL_ACADEMIC,
        max_length: int = 2048
    ) -> TransferResult:
        """
        执行风格迁移
        
        Args:
            text: 输入文本
            target_style: 目标期刊风格
            max_length: 最大生成长度
            
        Returns:
            TransferResult: 迁移结果
        """
        if not text.strip():
            return TransferResult(
                original_text=text,
                transferred_text=text,
                target_style=target_style,
                changes_made=[],
                confidence=0.0
            )
        
        style_info = self.STYLE_DESCRIPTIONS.get(
            target_style, 
            self.STYLE_DESCRIPTIONS[JournalStyle.GENERAL_ACADEMIC]
        )
        
        if self.use_modelscope and self._model and self._tokenizer:
            transferred = self._transfer_with_model(text, style_info, max_length)
        else:
            # 使用规则替换作为备选方案
            transferred = self._transfer_with_rules(text, target_style)
        
        # 分析改动
        changes = self._analyze_changes(text, transferred)
        
        # 计算置信度
        confidence = self._calculate_confidence(text, transferred)
        
        return TransferResult(
            original_text=text,
            transferred_text=transferred,
            target_style=target_style,
            changes_made=changes,
            confidence=confidence
        )
    
    def _transfer_with_model(self, text: str, style_info: Dict, max_length: int) -> str:
        """使用Qwen模型进行风格迁移"""
        prompt = style_info["prompt_template"].format(text=text)
        
        try:
            response, _ = self._model.chat(
                self._tokenizer,
                prompt,
                history=None,
                max_length=max_length,
                temperature=0.7,
                top_p=0.9
            )
            return response.strip()
        except Exception as e:
            print(f"模型推理失败: {e}")
            return text
    
    def _transfer_with_rules(self, text: str, style: JournalStyle) -> str:
        """使用规则进行基础风格转换（备选方案）"""
        result = text
        
        # 通用学术化替换规则
        replacements = {
            # 中文口语 -> 学术
            "很": "显著",
            "非常": "极其",
            "好的": "良好的",
            "坏的": "不良的",
            "所以": "因此",
            "但是": "然而",
            "而且": "此外",
            # 英文口语 -> 学术
            "a lot of": "numerous",
            "lots of": "many",
            "big": "significant",
            "small": "minor",
            "good": "favorable",
            "bad": "unfavorable",
            "get": "obtain",
            "show": "demonstrate",
        }
        
        for old, new in replacements.items():
            if old in result.lower():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                result = pattern.sub(new, result)
        
        return result
    
    def _analyze_changes(self, original: str, transferred: str) -> List[str]:
        """分析原文和迁移后文本的主要变化"""
        changes = []
        
        if len(transferred) < len(original) * 0.8:
            changes.append("文本更加精简")
        elif len(transferred) > len(original) * 1.2:
            changes.append("添加了更多细节描述")
        
        # 检查被动语态变化
        passive_markers = ["被", "由", "was", "were", "is", "are"]
        orig_passive = sum(1 for m in passive_markers if m in original.lower())
        trans_passive = sum(1 for m in passive_markers if m in transferred.lower())
        
        if trans_passive > orig_passive:
            changes.append("增加了被动语态使用")
        elif trans_passive < orig_passive:
            changes.append("减少了被动语态，使用更多主动语态")
        
        # 检查正式词汇变化
        formal_words = ["因此", "然而", "此外", "therefore", "however", "furthermore"]
        orig_formal = sum(1 for w in formal_words if w in original.lower())
        trans_formal = sum(1 for w in formal_words if w in transferred.lower())
        
        if trans_formal > orig_formal:
            changes.append("使用了更正式的连接词")
        
        if not changes:
            changes.append("进行了细微的风格调整")
        
        return changes
    
    def _calculate_confidence(self, original: str, transferred: str) -> float:
        """计算迁移置信度"""
        if original == transferred:
            return 0.0
        
        # 基于文本相似度和长度比例计算置信度
        len_ratio = min(len(original), len(transferred)) / max(len(original), len(transferred))
        
        # 简单的词重叠率
        orig_words = set(original.split())
        trans_words = set(transferred.split())
        overlap = len(orig_words & trans_words) / max(len(orig_words), 1)
        
        # 置信度：既不完全相同，也不完全不同
        confidence = 0.5 + (len_ratio * 0.25) + ((1 - abs(overlap - 0.7)) * 0.25)
        
        return round(min(1.0, max(0.0, confidence)), 2)
    
    def get_style_info(self, style: JournalStyle) -> Dict[str, Any]:
        """获取指定期刊风格的详细信息"""
        info = self.STYLE_DESCRIPTIONS.get(
            style, 
            self.STYLE_DESCRIPTIONS[JournalStyle.GENERAL_ACADEMIC]
        )
        return {
            "name": info["name"],
            "characteristics": info["characteristics"]
        }
    
    def list_available_styles(self) -> List[Dict[str, str]]:
        """列出所有可用的期刊风格"""
        return [
            {"id": style.value, "name": info["name"]}
            for style, info in self.STYLE_DESCRIPTIONS.items()
        ]
    
    def to_dict(self, result: TransferResult) -> Dict[str, Any]:
        """将迁移结果转换为字典格式（供API返回）"""
        return {
            "original": result.original_text,
            "transferred": result.transferred_text,
            "target_style": result.target_style.value,
            "changes": result.changes_made,
            "confidence": result.confidence
        }
