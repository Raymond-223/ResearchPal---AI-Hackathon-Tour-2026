"""
风格指纹评分模块
评估学术写作的正式程度、被动语态比例、领域术语匹配度
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .text_analyzer import TextAnalyzer, TokenInfo, AnalysisResult


class AcademicDomain(Enum):
    """学术领域枚举"""
    COMPUTER_SCIENCE = "computer_science"
    NATURAL_SCIENCE = "natural_science"
    SOCIAL_SCIENCE = "social_science"
    MEDICAL = "medical"
    ENGINEERING = "engineering"
    GENERAL = "general"


@dataclass
class StyleScore:
    """风格评分结果"""
    formality_score: float  # 正式程度 0-100
    passive_voice_ratio: float  # 被动语态比例 0-100
    terminology_score: float  # 领域术语匹配度 0-100
    sentence_complexity: float  # 句子复杂度 0-100
    overall_score: float  # 综合评分 0-100
    details: Dict[str, Any]  # 详细信息


class StyleScorer:
    """
    风格评分器
    分析学术文本的写作风格特征
    """
    
    # 常见口语化词汇（需要避免）
    INFORMAL_WORDS_CN = {
        "很", "非常", "太", "真的", "其实", "就是", "所以", "然后",
        "那个", "这个", "感觉", "觉得", "好像", "大概", "可能",
        "挺", "蛮", "超级", "特别", "啊", "呢", "吧", "嘛"
    }
    
    INFORMAL_WORDS_EN = {
        "very", "really", "actually", "basically", "just", "kind of",
        "sort of", "like", "stuff", "thing", "things", "a lot",
        "lots of", "gonna", "wanna", "gotta", "ok", "okay", "yeah"
    }
    
    # 学术正式词汇
    FORMAL_WORDS_CN = {
        "因此", "然而", "此外", "综上所述", "基于", "旨在", "针对",
        "提出", "采用", "实现", "分析", "研究", "探讨", "验证",
        "表明", "证明", "显示", "阐述", "论述", "综述"
    }
    
    FORMAL_WORDS_EN = {
        "therefore", "however", "furthermore", "moreover", "consequently",
        "nevertheless", "accordingly", "subsequently", "thus", "hence",
        "investigate", "demonstrate", "illustrate", "analyze", "propose",
        "implement", "evaluate", "establish", "validate", "examine"
    }
    
    # 被动语态标志词（中文）
    PASSIVE_MARKERS_CN = {"被", "由", "经", "受", "遭", "得到", "加以", "予以", "给予"}
    
    # 被动语态正则（英文）
    PASSIVE_PATTERN_EN = r'\b(is|are|was|were|been|being|be)\s+\w+ed\b'
    
    # 领域术语词典
    DOMAIN_TERMS = {
        AcademicDomain.COMPUTER_SCIENCE: {
            "cn": {"算法", "模型", "神经网络", "深度学习", "机器学习", "优化", "训练", 
                   "推理", "特征", "参数", "架构", "框架", "性能", "准确率", "损失函数",
                   "卷积", "注意力机制", "预训练", "微调", "数据集"},
            "en": {"algorithm", "model", "neural network", "deep learning", "machine learning",
                   "optimization", "training", "inference", "feature", "parameter", "architecture",
                   "framework", "performance", "accuracy", "loss function", "convolution",
                   "attention", "pretrained", "fine-tuning", "dataset"}
        },
        AcademicDomain.NATURAL_SCIENCE: {
            "cn": {"实验", "假设", "理论", "分子", "原子", "反应", "化合物", "能量",
                   "光谱", "测量", "观测", "样本", "浓度", "温度", "压力"},
            "en": {"experiment", "hypothesis", "theory", "molecule", "atom", "reaction",
                   "compound", "energy", "spectrum", "measurement", "observation", "sample",
                   "concentration", "temperature", "pressure"}
        },
        AcademicDomain.MEDICAL: {
            "cn": {"患者", "临床", "治疗", "诊断", "症状", "病例", "疗效", "副作用",
                   "剂量", "预后", "病理", "细胞", "基因", "蛋白质"},
            "en": {"patient", "clinical", "treatment", "diagnosis", "symptom", "case",
                   "efficacy", "side effect", "dosage", "prognosis", "pathology", "cell",
                   "gene", "protein"}
        },
        AcademicDomain.GENERAL: {
            "cn": {"研究", "方法", "结果", "结论", "分析", "数据", "实验", "验证"},
            "en": {"research", "method", "result", "conclusion", "analysis", "data",
                   "experiment", "validation"}
        }
    }
    
    def __init__(self, analyzer: Optional[TextAnalyzer] = None):
        """
        初始化风格评分器
        
        Args:
            analyzer: 文本分析器实例，如不提供则创建新实例
        """
        self.analyzer = analyzer or TextAnalyzer(use_modelscope=False)
    
    def score(
        self, 
        text: str, 
        domain: AcademicDomain = AcademicDomain.GENERAL
    ) -> StyleScore:
        """
        对文本进行风格评分
        
        Args:
            text: 输入文本
            domain: 学术领域
            
        Returns:
            StyleScore: 风格评分结果
        """
        if not text.strip():
            return StyleScore(
                formality_score=0,
                passive_voice_ratio=0,
                terminology_score=0,
                sentence_complexity=0,
                overall_score=0,
                details={}
            )
        
        # 分析文本
        analysis = self.analyzer.analyze(text)
        
        # 计算各项指标
        formality = self._calculate_formality(text, analysis)
        passive_ratio = self._calculate_passive_ratio(text, analysis)
        terminology = self._calculate_terminology_score(text, domain)
        complexity = self._calculate_sentence_complexity(analysis)
        
        # 综合评分 (加权平均)
        overall = (
            formality * 0.3 +
            passive_ratio * 0.2 +
            terminology * 0.25 +
            complexity * 0.25
        )
        
        return StyleScore(
            formality_score=round(formality, 2),
            passive_voice_ratio=round(passive_ratio, 2),
            terminology_score=round(terminology, 2),
            sentence_complexity=round(complexity, 2),
            overall_score=round(overall, 2),
            details={
                "word_count": analysis.word_count,
                "sentence_count": analysis.sentence_count,
                "avg_sentence_length": round(analysis.avg_sentence_length, 2),
                "domain": domain.value,
                "informal_words_found": self._find_informal_words(text),
                "formal_words_found": self._find_formal_words(text)
            }
        )
    
    def _calculate_formality(self, text: str, analysis: AnalysisResult) -> float:
        """计算正式程度评分"""
        if analysis.word_count == 0:
            return 0.0
        
        # 统计口语化词汇出现次数
        informal_count = 0
        formal_count = 0
        
        text_lower = text.lower()
        
        # 检查中文口语词
        for word in self.INFORMAL_WORDS_CN:
            informal_count += text.count(word)
        
        # 检查英文口语词
        for word in self.INFORMAL_WORDS_EN:
            informal_count += len(re.findall(r'\b' + word + r'\b', text_lower))
        
        # 检查正式词汇
        for word in self.FORMAL_WORDS_CN:
            formal_count += text.count(word)
        
        for word in self.FORMAL_WORDS_EN:
            formal_count += len(re.findall(r'\b' + word + r'\b', text_lower))
        
        # 计算正式程度分数
        informal_ratio = informal_count / analysis.word_count
        formal_ratio = formal_count / analysis.word_count
        
        # 正式程度 = 100 - 口语化程度 + 正式词汇加成
        score = 100 - (informal_ratio * 200) + (formal_ratio * 100)
        return max(0, min(100, score))
    
    def _calculate_passive_ratio(self, text: str, analysis: AnalysisResult) -> float:
        """计算被动语态比例"""
        if analysis.sentence_count == 0:
            return 0.0
        
        passive_count = 0
        
        # 检查中文被动语态
        for marker in self.PASSIVE_MARKERS_CN:
            passive_count += text.count(marker)
        
        # 检查英文被动语态
        passive_count += len(re.findall(self.PASSIVE_PATTERN_EN, text, re.IGNORECASE))
        
        # 被动语态比例（学术写作中适度使用被动语态是好的）
        ratio = passive_count / analysis.sentence_count
        
        # 理想的被动语态比例是20%-40%，转换为分数
        if ratio < 0.1:
            score = ratio * 500  # 太少，线性增长
        elif ratio <= 0.4:
            score = 50 + (ratio - 0.1) * 166.67  # 合理范围，高分
        else:
            score = 100 - (ratio - 0.4) * 100  # 太多，降分
        
        return max(0, min(100, score))
    
    def _calculate_terminology_score(self, text: str, domain: AcademicDomain) -> float:
        """计算领域术语匹配度"""
        terms = self.DOMAIN_TERMS.get(domain, self.DOMAIN_TERMS[AcademicDomain.GENERAL])
        
        term_count = 0
        total_terms = len(terms["cn"]) + len(terms["en"])
        
        # 检查中文术语
        for term in terms["cn"]:
            if term in text:
                term_count += 1
        
        # 检查英文术语
        text_lower = text.lower()
        for term in terms["en"]:
            if term.lower() in text_lower:
                term_count += 1
        
        # 计算覆盖率并转换为分数
        coverage = term_count / total_terms if total_terms > 0 else 0
        score = min(100, coverage * 500)  # 使用20%的术语即可达到满分
        
        return score
    
    def _calculate_sentence_complexity(self, analysis: AnalysisResult) -> float:
        """计算句子复杂度"""
        if analysis.sentence_count == 0:
            return 0.0
        
        # 基于平均句长评估复杂度
        avg_len = analysis.avg_sentence_length
        
        # 理想的学术写作句子长度是15-25词
        if avg_len < 8:
            score = avg_len * 6.25  # 太短
        elif avg_len <= 25:
            score = 50 + (avg_len - 8) * 2.94  # 合理范围
        elif avg_len <= 35:
            score = 100 - (avg_len - 25) * 3  # 略长但可接受
        else:
            score = 70 - (avg_len - 35) * 2  # 太长
        
        return max(0, min(100, score))
    
    def _find_informal_words(self, text: str) -> List[str]:
        """找出文本中的口语化词汇"""
        found = []
        text_lower = text.lower()
        
        for word in self.INFORMAL_WORDS_CN:
            if word in text:
                found.append(word)
        
        for word in self.INFORMAL_WORDS_EN:
            if re.search(r'\b' + word + r'\b', text_lower):
                found.append(word)
        
        return found
    
    def _find_formal_words(self, text: str) -> List[str]:
        """找出文本中的正式词汇"""
        found = []
        text_lower = text.lower()
        
        for word in self.FORMAL_WORDS_CN:
            if word in text:
                found.append(word)
        
        for word in self.FORMAL_WORDS_EN:
            if re.search(r'\b' + word + r'\b', text_lower):
                found.append(word)
        
        return found
    
    def get_improvement_suggestions(self, score: StyleScore) -> List[str]:
        """根据评分结果给出改进建议"""
        suggestions = []
        
        if score.formality_score < 60:
            suggestions.append("文本正式程度较低，建议减少口语化表达，使用更专业的学术词汇")
        
        if score.passive_voice_ratio < 30:
            suggestions.append("被动语态使用较少，学术写作中可适当增加被动语态以增强客观性")
        elif score.passive_voice_ratio > 80:
            suggestions.append("被动语态使用过多，建议适当使用主动语态以增强表达力")
        
        if score.terminology_score < 40:
            suggestions.append("领域术语使用较少，建议增加专业术语以提高学术性")
        
        if score.sentence_complexity < 40:
            suggestions.append("句子过于简单，可适当使用复合句以增强论述深度")
        elif score.sentence_complexity > 85:
            suggestions.append("部分句子过长，建议拆分长句以提高可读性")
        
        if not suggestions:
            suggestions.append("整体写作风格良好，符合学术写作规范")
        
        return suggestions
    
    def to_dict(self, score: StyleScore) -> Dict[str, Any]:
        """将评分结果转换为字典格式（供API返回）"""
        return {
            "scores": {
                "formality": score.formality_score,
                "passive_voice_ratio": score.passive_voice_ratio,
                "terminology": score.terminology_score,
                "sentence_complexity": score.sentence_complexity,
                "overall": score.overall_score
            },
            "details": score.details,
            "suggestions": self.get_improvement_suggestions(score)
        }
