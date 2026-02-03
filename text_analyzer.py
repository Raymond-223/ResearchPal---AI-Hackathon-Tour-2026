"""
文本分析模块
使用魔搭BERT进行文本分词和词性标注
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from modelscope.pipelines import pipeline
    from modelscope.utils.constant import Tasks
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False

try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


@dataclass
class TokenInfo:
    """分词结果信息"""
    word: str
    pos: str  # 词性标注
    start: int
    end: int


@dataclass
class AnalysisResult:
    """文本分析结果"""
    tokens: List[TokenInfo]
    sentences: List[str]
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    

class TextAnalyzer:
    """
    文本分析器
    支持中英文文本的分词和词性标注
    """
    
    def __init__(self, use_modelscope: bool = True):
        """
        初始化文本分析器
        
        Args:
            use_modelscope: 是否使用魔搭模型，默认True
        """
        self.use_modelscope = use_modelscope and MODELSCOPE_AVAILABLE
        self._tokenizer = None
        self._pos_tagger = None
        
        if self.use_modelscope:
            self._init_modelscope_models()
        elif JIEBA_AVAILABLE:
            # 使用jieba作为备选方案
            jieba.initialize()
        # 如果都不可用，使用简单分词
    
    def _init_modelscope_models(self):
        """初始化魔搭模型"""
        try:
            # 使用魔搭的中文分词模型
            self._tokenizer = pipeline(
                task=Tasks.word_segmentation,
                model='damo/nlp_structbert_word-segmentation_chinese-base'
            )
            # 使用魔搭的词性标注模型
            self._pos_tagger = pipeline(
                task=Tasks.part_of_speech,
                model='damo/nlp_structbert_part-of-speech_chinese-base'
            )
        except Exception as e:
            print(f"魔搭模型加载失败，使用备选方案: {e}")
            self.use_modelscope = False
    
    def analyze(self, text: str) -> AnalysisResult:
        """
        分析文本
        
        Args:
            text: 输入文本
            
        Returns:
            AnalysisResult: 分析结果
        """
        if not text.strip():
            return AnalysisResult(
                tokens=[],
                sentences=[],
                word_count=0,
                sentence_count=0,
                avg_sentence_length=0.0
            )
        
        # 分句
        sentences = self._split_sentences(text)
        
        # 分词和词性标注
        tokens = self._tokenize_and_tag(text)
        
        # 计算统计信息
        word_count = len(tokens)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0.0
        
        return AnalysisResult(
            tokens=tokens,
            sentences=sentences,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length
        )
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        # 支持中英文句子分隔符
        sentence_pattern = r'[.!?。！？；;]+'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize_and_tag(self, text: str) -> List[TokenInfo]:
        """分词和词性标注"""
        tokens = []
        
        if self.use_modelscope and self._tokenizer and self._pos_tagger:
            tokens = self._modelscope_tokenize(text)
        elif JIEBA_AVAILABLE:
            tokens = self._jieba_tokenize(text)
        else:
            tokens = self._simple_tokenize(text)
        
        return tokens
    
    def _modelscope_tokenize(self, text: str) -> List[TokenInfo]:
        """使用魔搭模型分词"""
        tokens = []
        try:
            # 分词
            seg_result = self._tokenizer(text)
            words = seg_result.get('output', text.split())
            if isinstance(words, str):
                words = words.split()
            
            # 词性标注
            pos_result = self._pos_tagger(text)
            pos_tags = pos_result.get('output', [])
            
            # 合并结果
            pos_map = {}
            if isinstance(pos_tags, list):
                for item in pos_tags:
                    if isinstance(item, dict) and 'word' in item and 'pos' in item:
                        pos_map[item['word']] = item['pos']
            
            position = 0
            for word in words:
                if not word.strip():
                    continue
                pos = pos_map.get(word, 'UNK')
                start = text.find(word, position)
                if start == -1:
                    start = position
                end = start + len(word)
                tokens.append(TokenInfo(
                    word=word,
                    pos=pos,
                    start=start,
                    end=end
                ))
                position = end
                
        except Exception as e:
            print(f"魔搭分词失败: {e}")
            return self._jieba_tokenize(text)
        
        return tokens
    
    def _jieba_tokenize(self, text: str) -> List[TokenInfo]:
        """使用jieba分词"""
        if not JIEBA_AVAILABLE:
            return self._simple_tokenize(text)
        
        tokens = []
        position = 0
        
        for word, pos in pseg.cut(text):
            if not word.strip():
                continue
            start = text.find(word, position)
            if start == -1:
                start = position
            end = start + len(word)
            tokens.append(TokenInfo(
                word=word,
                pos=pos,
                start=start,
                end=end
            ))
            position = end
        
        return tokens
    
    def _simple_tokenize(self, text: str) -> List[TokenInfo]:
        """简单分词（备选方案，按字符/空格分割）"""
        tokens = []
        
        # 检测是否主要为中文
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        is_chinese = chinese_chars > len(text) * 0.3
        
        if is_chinese:
            # 中文按字符分词
            position = 0
            for char in text:
                if char.strip():
                    tokens.append(TokenInfo(
                        word=char,
                        pos='UNK',
                        start=position,
                        end=position + 1
                    ))
                position += 1
        else:
            # 英文按空格分词
            words = re.findall(r'\b\w+\b', text)
            position = 0
            for word in words:
                start = text.find(word, position)
                if start == -1:
                    start = position
                end = start + len(word)
                tokens.append(TokenInfo(
                    word=word,
                    pos='UNK',
                    start=start,
                    end=end
                ))
                position = end
        
        return tokens
    
    def get_pos_distribution(self, tokens: List[TokenInfo]) -> Dict[str, int]:
        """获取词性分布统计"""
        distribution = {}
        for token in tokens:
            pos = token.pos
            distribution[pos] = distribution.get(pos, 0) + 1
        return distribution
    
    def to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """将分析结果转换为字典格式（供API返回）"""
        return {
            "tokens": [
                {
                    "word": t.word,
                    "pos": t.pos,
                    "start": t.start,
                    "end": t.end
                }
                for t in result.tokens
            ],
            "sentences": result.sentences,
            "statistics": {
                "word_count": result.word_count,
                "sentence_count": result.sentence_count,
                "avg_sentence_length": round(result.avg_sentence_length, 2)
            }
        }
