#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文摘要生成核心模块
功能：实现多粒度摘要生成（1分钟速览、10分钟精读）、关键词提取等功能
作者：算法工程师A
日期：2024-01-15
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter

# 常量定义
SHORT_SUMMARY_MAX_LENGTH = 150  # 短摘要最大长度
LONG_SUMMARY_MAX_LENGTH = 500   # 长摘要最大长度
KEYWORD_COUNT = 10              # 提取关键词数量
SECTION_SUMMARY_MAX_LENGTH = 100 # 章节小结最大长度

# 关键词知识库（示例）
KEYWORD_KNOWLEDGE_BASE = {
    'transformer': {
        'definition': '一种基于自注意力机制的深度学习模型架构',
        'related_terms': ['attention', 'encoder', 'decoder', 'BERT', 'GPT']
    },
    'llm': {
        'definition': 'Large Language Model，大型语言模型',
        'related_terms': ['GPT', 'BERT', 'T5', 'language model', 'foundation model']
    },
    'fine-tuning': {
        'definition': '对预训练模型进行微调以适应特定任务',
        'related_terms': ['transfer learning', 'pre-training', 'adapter', 'LoRA']
    },
    'embedding': {
        'definition': '将离散变量转换为连续向量表示',
        'related_terms': ['word embedding', 'sentence embedding', 'vector representation']
    },
    'overfitting': {
        'definition': '模型过度拟合训练数据，泛化能力差',
        'related_terms': ['regularization', 'dropout', 'early stopping', 'cross-validation']
    }
}

# 全局变量（懒加载）
_summarizer_pipeline = None


def _init_summarizer():
    """初始化摘要生成模型（懒加载）"""
    global _summarizer_pipeline
    if _summarizer_pipeline is None:
        try:
            from modelscope.pipelines import pipeline
            _summarizer_pipeline = pipeline(
                task="text-summary",
                model="damo/nlp_bart_text-summary_english-base"
            )
        except ImportError:
            print("警告：未安装modelscope，将使用降级摘要策略")
        except Exception as e:
            print(f"警告：模型加载失败：{str(e)}，将使用降级摘要策略")
    
    return _summarizer_pipeline


def generate_short_summary(structured_text: Dict[str, str]) -> str:
    """
    生成1分钟速览摘要（核心贡献+创新点）
    
    Args:
        structured_text: 结构化的论文文本
        
    Returns:
        str: 短摘要文本
    """
    # 确定输入文本优先级
    input_text = ""
    
    # 优先使用摘要章节
    if 'abstract' in structured_text and structured_text['abstract'].strip():
        input_text = structured_text['abstract']
    # 其次使用引言+结论
    elif 'introduction' in structured_text and 'conclusion' in structured_text:
        input_text = structured_text['introduction'] + "\n\n" + structured_text['conclusion']
    # 最后使用全文前1000词
    elif 'preamble' in structured_text:
        input_text = structured_text['preamble'][:1000]
    else:
        # 合并所有可用文本
        input_text = "\n\n".join([text for text in structured_text.values() if text.strip()])[:1000]
    
    # 清理输入文本（移除占位符）
    input_text = _clean_text(input_text)
    
    # 提示词工程
    SHORT_SUMMARY_PROMPT = (
        "请提供这篇学术论文的核心贡献和创新点摘要，重点包括：\n"
        "1. 解决了什么问题\n"
        "2. 提出了什么创新方法或模型\n"
        "3. 取得了什么显著成果\n"
        "请用简洁专业的语言，控制在150词以内。"
    )
    
    try:
        # 尝试使用模型生成摘要
        summarizer = _init_summarizer()
        if summarizer:
            result = summarizer(
                input_text,
                max_length=SHORT_SUMMARY_MAX_LENGTH,
                min_length=50,
                prompt=SHORT_SUMMARY_PROMPT
            )
            summary = result[0]['summary_text']
        else:
            # 降级策略
            summary = _fallback_summary(input_text, SHORT_SUMMARY_MAX_LENGTH)
        
        # 后处理优化
        summary = _postprocess_summary(summary, SHORT_SUMMARY_MAX_LENGTH)
        
    except Exception as e:
        print(f"摘要生成失败：{str(e)}，使用降级策略")
        summary = _fallback_summary(input_text, SHORT_SUMMARY_MAX_LENGTH)
    
    return summary


def generate_long_summary(structured_text: Dict[str, str]) -> Dict[str, str]:
    """
    生成10分钟精读摘要（全流程解读）
    
    Args:
        structured_text: 结构化的论文文本
        
    Returns:
        Dict: 分章节的详细摘要
    """
    long_summary = {}
    
    # 研究背景
    background_text = ""
    if 'introduction' in structured_text:
        background_text = structured_text['introduction']
    elif 'preamble' in structured_text:
        background_text = structured_text['preamble']
    
    if background_text:
        long_summary['background'] = _generate_section_summary(
            background_text, 
            "请总结这篇论文的研究背景和动机，包括：\n1. 研究领域的现状\n2. 存在的主要问题\n3. 研究的重要性",
            SECTION_SUMMARY_MAX_LENGTH
        )
    
    # 研究方法
    method_text = ""
    if 'method' in structured_text:
        method_text = structured_text['method']
    
    if method_text:
        long_summary['method'] = _generate_section_summary(
            method_text,
            "请总结这篇论文提出的研究方法或算法，包括：\n1. 核心思想\n2. 技术细节\n3. 与现有方法的区别",
            SECTION_SUMMARY_MAX_LENGTH
        )
    
    # 实验结果
    result_text = ""
    if 'result' in structured_text:
        result_text = structured_text['result']
    elif 'experiment' in structured_text:
        result_text = structured_text['experiment']
    
    if result_text:
        long_summary['results'] = _generate_section_summary(
            result_text,
            "请总结这篇论文的主要实验结果，包括：\n1. 使用的数据集\n2. 评估指标\n3. 关键实验发现\n4. 性能提升",
            SECTION_SUMMARY_MAX_LENGTH
        )
    
    # 结论与展望
    conclusion_text = ""
    if 'conclusion' in structured_text:
        conclusion_text = structured_text['conclusion']
    elif 'discussion' in structured_text:
        conclusion_text = structured_text['discussion']
    
    if conclusion_text:
        long_summary['conclusion'] = _generate_section_summary(
            conclusion_text,
            "请总结这篇论文的主要结论和未来展望，包括：\n1. 研究贡献\n2. 局限性\n3. 未来研究方向",
            SECTION_SUMMARY_MAX_LENGTH
        )
    
    # 整合为完整长摘要
    full_summary = _integrate_long_summary(long_summary)
    
    # 长度控制
    if len(full_summary) > LONG_SUMMARY_MAX_LENGTH:
        full_summary = full_summary[:LONG_SUMMARY_MAX_LENGTH] + "..."
    
    return {
        'sections': long_summary,
        'full_text': full_summary
    }


def extract_keywords(text: str, top_k: int = KEYWORD_COUNT) -> List[Dict[str, Any]]:
    """
    提取论文关键词
    
    Args:
        text: 论文文本
        top_k: 返回关键词数量
        
    Returns:
        List[Dict]: 关键词列表，包含词频、释义等信息
    """
    # 清理文本
    clean_text = _clean_text(text)
    
    # 分词（简化版）
    words = re.findall(r'\b[a-zA-Z]{3,}\b', clean_text.lower())
    
    # 过滤停用词
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'are', 'from', 'was', 'were', 'has', 'have', 'had',
                  'will', 'would', 'could', 'should', 'in', 'on', 'at', 'by', 'to', 'of', 'as', 'is', 'it', 'its'}
    words = [word for word in words if word not in stop_words]
    
    # 计算词频
    word_freq = Counter(words)
    
    # 专业术语加权
    keywords = []
    for word, freq in word_freq.most_common(top_k * 2):  # 取更多候选词
        # 基础分数 = 词频
        score = freq
        
        # 专业术语加分
        if word in KEYWORD_KNOWLEDGE_BASE:
            score += 5
        
        # 词长度加分（越长越可能是专业术语）
        if len(word) > 6:
            score += 2
        
        keywords.append({
            'word': word,
            'frequency': freq,
            'score': score,
            'definition': KEYWORD_KNOWLEDGE_BASE.get(word, {}).get('definition', ''),
            'related_terms': KEYWORD_KNOWLEDGE_BASE.get(word, {}).get('related_terms', [])
        })
    
    # 按得分排序，取top_k
    keywords.sort(key=lambda x: x['score'], reverse=True)
    keywords = keywords[:top_k]
    
    # 计算词频占比
    total_words = sum(word_freq.values())
    for keyword in keywords:
        keyword['frequency_ratio'] = f"{keyword['frequency'] / total_words * 100:.1f}%"
    
    return keywords


def pack_summary_result(structured_text: Dict[str, str]) -> Dict[str, Any]:
    """
    封装摘要结果
    
    Args:
        structured_text: 结构化的论文文本
        
    Returns:
        Dict: 完整的摘要结果
    """
    start_time = time.time()
    
    # 生成短摘要
    short_summary = generate_short_summary(structured_text)
    
    # 生成长摘要
    long_summary = generate_long_summary(structured_text)
    
    # 提取关键词（使用合并后的文本）
    combined_text = "\n\n".join([text for text in structured_text.values() if text.strip()])
    keywords = extract_keywords(combined_text)
    
    # 提取隐含关键词（从摘要中）
    implicit_keywords = []
    summary_text = short_summary + "\n\n" + long_summary['full_text']
    for word, info in KEYWORD_KNOWLEDGE_BASE.items():
        if word.lower() in summary_text.lower() and word not in [k['word'] for k in keywords]:
            implicit_keywords.append({
                'word': word,
                'definition': info['definition'],
                'related_terms': info['related_terms']
            })
    
    return {
        'short_summary': short_summary,
        'long_summary': long_summary,
        'keywords': keywords,
        'implicit_keywords': implicit_keywords[:5],  # 最多5个隐含关键词
        'processing_time': time.time() - start_time
    }


def _clean_text(text: str) -> str:
    """清理文本，移除占位符"""
    # 移除公式占位符
    text = re.sub(r'<formula>.*?</formula>', '', text)
    # 移除图表占位符
    text = re.sub(r'<figure>.*?</figure>', '', text)
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _fallback_summary(text: str, max_length: int) -> str:
    """降级摘要策略（无模型时使用）"""
    # 提取句子
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # 选择重要句子（基于位置和长度）
    important_sentences = []
    
    # 首段和末段的句子更重要
    total_sentences = len(sentences)
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence or len(sentence) < 10:
            continue
        
        # 位置权重
        position_score = 1.0
        if i == 0 or i == total_sentences - 1:
            position_score = 2.0
        elif i < 3:
            position_score = 1.5
        
        # 包含关键词的句子更重要
        keyword_score = 1.0
        keywords = ['introduce', 'present', 'propose', 'develop', 'show', 'demonstrate',
                   'result', 'conclusion', 'find', 'discover', 'improve', 'achieve']
        for keyword in keywords:
            if keyword in sentence.lower():
                keyword_score = 1.5
                break
        
        score = position_score * keyword_score
        important_sentences.append((sentence, score))
    
    # 按得分排序
    important_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # 拼接摘要
    summary = ""
    for sentence, _ in important_sentences:
        if len(summary) + len(sentence) + 1 <= max_length:
            if summary:
                summary += " "
            summary += sentence
        else:
            break
    
    # 确保摘要完整
    if not summary and sentences:
        summary = sentences[0][:max_length]
    
    return summary


def _postprocess_summary(summary: str, max_length: int) -> str:
    """后处理摘要文本"""
    # 移除冗余表述
    redundant_patterns = [
        r'^In this paper, we',
        r'^This paper',
        r'^The paper',
        r'^In this study, we',
        r'^This study'
    ]
    
    for pattern in redundant_patterns:
        summary = re.sub(pattern, '', summary, flags=re.IGNORECASE)
    
    # 清理空格和标点
    summary = summary.strip()
    if summary and summary[-1] not in ['.', '!', '?']:
        summary += '.'
    
    # 长度控制
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
    
    return summary


def _generate_section_summary(text: str, prompt: str, max_length: int) -> str:
    """生成章节小结"""
    # 清理文本
    text = _clean_text(text)
    
    try:
        # 尝试使用模型
        summarizer = _init_summarizer()
        if summarizer:
            result = summarizer(
                text,
                max_length=max_length,
                min_length=30,
                prompt=prompt
            )
            summary = result[0]['summary_text']
        else:
            # 降级策略
            summary = _fallback_summary(text, max_length)
        
        return _postprocess_summary(summary, max_length)
    
    except Exception as e:
        print(f"章节摘要生成失败：{str(e)}")
        return _fallback_summary(text, max_length)


def _integrate_long_summary(section_summaries: Dict[str, str]) -> str:
    """整合章节摘要为完整长摘要"""
    # 定义整合顺序
    order = ['background', 'method', 'results', 'conclusion']
    
    # 按顺序整合
    full_summary = ""
    for section in order:
        if section in section_summaries:
            if full_summary:
                full_summary += "\n\n"
            
            # 添加小标题
            titles = {
                'background': '研究背景',
                'method': '研究方法',
                'results': '实验结果',
                'conclusion': '结论与展望'
            }
            
            full_summary += f"【{titles[section]}】\n{section_summaries[section]}"
    
    return full_summary


if __name__ == "__main__":
    # 测试代码
    test_structured_text = {
        'abstract': 'This paper presents a novel approach to text summarization using transformer-based models. We propose a new attention mechanism that significantly improves the quality of generated summaries. Experimental results on several benchmark datasets demonstrate that our method outperforms existing state-of-the-art approaches by 15% in ROUGE scores.',
        'introduction': 'Text summarization is a fundamental task in natural language processing. Despite recent advances, existing methods still struggle with long documents and complex semantic relationships. In this paper, we address these challenges by introducing a novel attention mechanism.',
        'method': 'Our proposed method consists of three main components: a hierarchical encoder, an adaptive attention mechanism, and a context-aware decoder. The hierarchical encoder processes the input document at multiple levels of granularity...',
        'experiment': 'We evaluated our method on three benchmark datasets: CNN/DailyMail, XSum, and SAMSum. The experimental results show that our approach achieves state-of-the-art performance...',
        'conclusion': 'In this paper, we proposed a novel transformer-based approach for text summarization. Our method introduces a new attention mechanism that effectively captures long-range dependencies. Experimental results demonstrate significant improvements over existing methods.'
    }
    
    # 测试短摘要生成
    short_summary = generate_short_summary(test_structured_text)
    print(f"短摘要：\n{short_summary}\n")
    
    # 测试长摘要生成
    long_summary = generate_long_summary(test_structured_text)
    print(f"长摘要：\n{long_summary['full_text']}\n")
    
    # 测试关键词提取
    combined_text = "\n\n".join(test_structured_text.values())
    keywords = extract_keywords(combined_text)
    print("关键词：")
    for kw in keywords:
        print(f"- {kw['word']}: {kw['frequency']}次 ({kw['frequency_ratio']})")
    
    # 测试完整封装
    result = pack_summary_result(test_structured_text)
    print(f"\n处理时间：{result['processing_time']:.2f}秒")