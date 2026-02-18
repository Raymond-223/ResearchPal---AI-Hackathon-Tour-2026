#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文可视化辅助模块
功能：实现引用关系图谱生成、图表文本描述生成等功能
作者：算法工程师A
日期：2024-01-15
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any

# 常量定义
MAX_REFERENCES = 5  # 最大展示参考文献数量
FIGURE_TYPE_KEYWORDS = {
    '架构图': ['architecture', 'framework', 'structure', 'pipeline', 'diagram', 'flowchart', '系统', '架构', '框架', '流程'],
    '折线图': ['line chart', 'line graph', 'trend', 'accuracy', 'performance', 'error', 'loss', '曲线', '趋势', '精度'],
    '柱状图': ['bar chart', 'bar graph', 'comparison', 'benchmark', 'evaluation', '对比', '评估', '柱状'],
    '散点图': ['scatter plot', 'scatter graph', 'distribution', 'correlation', '分布', '相关性'],
    '热力图': ['heatmap', 'attention map', 'confusion matrix', '热力图', '注意力图', '混淆矩阵'],
    '表格': ['table', 'comparison', 'results', 'ablation', '消融', '对比', '结果'],
    '示意图': ['illustration', 'example', 'case study', 'demonstration', '示意', '示例']
}

LANDMARK_PAPERS = [
    'Attention Is All You Need',
    'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
    'Generative Adversarial Networks',
    'ImageNet Classification with Deep Convolutional Neural Networks',
    'Deep Residual Learning for Image Recognition',
    'U-Net: Convolutional Networks for Biomedical Image Segmentation',
    'YOLO: Real-Time Object Detection',
    'AlphaGo Zero: Mastering the Game of Go without Human Knowledge',
    'GPT-3: Language Models are Few-Shot Learners',
    'DALL-E: Creating Images from Text'
]


def generate_citation_graph(structured_text: Dict[str, str]) -> Dict[str, Any]:
    """
    生成引用关系图谱（基于Mermaid）
    
    Args:
        structured_text: 结构化的论文文本
        
    Returns:
        Dict: 包含Mermaid代码和参考文献列表
    """
    # 提取参考文献
    references = []
    
    if 'references' in structured_text:
        references_text = structured_text['references']
        
        # 按格式分割参考文献条目
        # 支持多种引用格式：[1], 1., (1), [1]:, 1.:
        ref_patterns = [
            r'\[\d+\]\s+',      # [1] 
            r'\d+\.\s+',        # 1. 
            r'\(\d+\)\s+',      # (1) 
            r'\[\d+\]:\s+',     # [1]: 
            r'\d+:\s+'          # 1: 
        ]
        
        # 合并所有匹配
        all_refs = []
        for pattern in ref_patterns:
            matches = re.split(f'({pattern})', references_text)
            if len(matches) > 1:
                all_refs.extend(matches)
        
        # 清理并提取有效参考文献
        current_ref = ""
        for item in all_refs:
            item = item.strip()
            
            # 如果是引用编号，开始新的参考文献
            if re.match(r'^(\[\d+\]|\d+\.|\(\d+\)|\[\d+\]:|\d+:)$', item):
                if current_ref:
                    references.append(current_ref)
                    current_ref = ""
                # 移除编号前缀
                item = re.sub(r'^(\[\d+\]|\d+\.|\(\d+\)|\[\d+\]:|\d+:)\s*', '', item)
            
            if item:
                current_ref += " " + item
        
        # 添加最后一个参考文献
        if current_ref:
            references.append(current_ref.strip())
        
        # 清理参考文献文本
        references = [_clean_reference(ref) for ref in references if ref.strip()]
        
        # 取前MAX_REFERENCES篇
        references = references[:MAX_REFERENCES]
    
    # 构建Mermaid图谱
    mermaid_code = _build_mermaid_graph(references)
    
    return {
        'mermaid_code': mermaid_code,
        'references': references,
        'reference_count': len(references)
    }


def generate_figure_description(structured_text: Dict[str, str], figures: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    为图表生成文本描述
    
    Args:
        structured_text: 结构化的论文文本
        figures: 图表信息列表
        
    Returns:
        List[Dict]: 图表描述列表
    """
    figure_descriptions = []
    
    # 合并所有文本以查找图表上下文
    full_text = "\n\n".join([text for text in structured_text.values() if text.strip()])
    
    for figure in figures:
        figure_id = figure['id']
        page_num = figure['page']
        
        # 查找图表上下文
        context = _find_figure_context(full_text, figure_id)
        
        # 推断图表类型
        figure_type = _infer_figure_type(context)
        
        # 生成标准化描述
        description = _generate_standard_description(figure_type, context, figure_id, page_num)
        
        figure_descriptions.append({
            'id': figure_id,
            'page': page_num,
            'type': figure_type,
            'description': description,
            'context': context[:200] + "..." if len(context) > 200 else context
        })
    
    return figure_descriptions


def _clean_reference(reference: str) -> Dict[str, str]:
    """清理参考文献文本并提取关键信息"""
    # 移除多余空格和换行
    reference = re.sub(r'\s+', ' ', reference).strip()
    
    # 提取标题（简化处理）
    title_match = re.search(r'["“](.*?)["”]', reference)
    title = title_match.group(1) if title_match else reference[:100]
    
    # 提取作者（简化处理）
    author_match = re.search(r'^(.+?),\s+\d{4}', reference)
    authors = author_match.group(1) if author_match else "未知作者"
    
    # 判断是否为经典论文
    is_landmark = any(landmark.lower() in title.lower() for landmark in LANDMARK_PAPERS)
    
    # 生成简短描述
    description = f"参考文献[{len(LANDMARK_PAPERS)+1}]"
    if is_landmark:
        description = "经典论文★"
    
    # 尝试提取年份
    year_match = re.search(r'\b(\d{4})\b', reference)
    year = year_match.group(1) if year_match else "未知年份"
    
    return {
        'title': title,
        'authors': authors,
        'year': year,
        'is_landmark': is_landmark,
        'description': description,
        'full_text': reference
    }


def _build_mermaid_graph(references: List[Dict[str, str]]) -> str:
    """构建Mermaid图谱代码"""
    mermaid_code = "graph LR\n"
    mermaid_code += "    subgraph 引用关系图谱\n"
    
    # 当前论文节点
    mermaid_code += '    A["当前论文\\n(核心节点)"] --> B["参考文献"]\n'
    mermaid_code += '    B --> C["详细信息"]\n'
    
    # 添加参考文献节点
    for i, ref in enumerate(references, 1):
        node_id = f"R{i}"
        node_style = "style " + node_id + " fill:#fff9c4,stroke:#ffc107,stroke-width:2px;" if ref['is_landmark'] else ""
        
        mermaid_code += f'    C --> {node_id}["{ref["title"][:30]}{"..." if len(ref["title"]) > 30 else ""}\\n{ref["authors"][:20]}{"..." if len(ref["authors"]) > 20 else ""}"]\n'
        if node_style:
            mermaid_code += f"    {node_style}\n"
    
    mermaid_code += "    end\n"
    mermaid_code += "    class A main_paper;\n"
    mermaid_code += "    class B,C,R1,R2,R3,R4,R5 references;\n"
    mermaid_code += "    classDef main_paper fill:#e3f2fd,stroke:#2196f3,stroke-width:2px;\n"
    mermaid_code += "    classDef references fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1px;\n"
    
    return mermaid_code


def _find_figure_context(text: str, figure_id: int) -> str:
    """查找图表周围的上下文"""
    # 查找图表引用
    patterns = [
        rf'Figure\s*{figure_id}',
        rf'Fig\.\s*{figure_id}',
        rf'图\s*{figure_id}',
        rf'图表\s*{figure_id}',
        rf'<figure>图{figure_id}'
    ]
    
    context = ""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # 提取前后100字符作为上下文
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end]
            break
    
    return context


def _infer_figure_type(context: str) -> str:
    """根据上下文推断图表类型"""
    context_lower = context.lower()
    
    # 计算每种类型的匹配度
    type_scores = {}
    for figure_type, keywords in FIGURE_TYPE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in context_lower:
                score += 1
        
        if score > 0:
            type_scores[figure_type] = score
    
    # 返回匹配度最高的类型
    if type_scores:
        return max(type_scores.items(), key=lambda x: x[1])[0]
    else:
        return "其他图表"


def _generate_standard_description(figure_type: str, context: str, figure_id: int, page_num: int) -> str:
    """生成标准化的图表描述"""
    # 清理上下文
    context = re.sub(r'<[^>]+>', '', context)  # 移除HTML标签
    context = re.sub(r'\s+', ' ', context).strip()
    
    # 根据图表类型生成不同的描述模板
    templates = {
        '架构图': f"图{figure_id}：架构图，展示了{_extract_key_info(context, ['系统', '架构', '框架', '模型', '网络'])}的整体结构，包含{_count_components(context)}个核心模块。",
        '折线图': f"图{figure_id}：折线图，展示了{_extract_key_info(context, ['性能', '精度', '准确率', '误差', '损失'])}随{_extract_key_info(context, ['迭代', '时间', '参数', '比例'])}的变化趋势。",
        '柱状图': f"图{figure_id}：柱状图，对比了{_extract_key_info(context, ['不同方法', '不同模型', '不同参数', '不同数据集'])}在{_extract_key_info(context, ['准确率', '性能', '效率', '速度'])}上的表现。",
        '散点图': f"图{figure_id}：散点图，展示了{_extract_key_info(context, ['数据点', '样本', '实例'])}在{_extract_key_info(context, ['两个', '多个'])}维度上的分布情况。",
        '热力图': f"图{figure_id}：热力图，可视化了{_extract_key_info(context, ['注意力', '相关性', '相似度', '差异'])}的强度分布。",
        '表格': f"图{figure_id}：表格，展示了{_extract_key_info(context, ['实验结果', '对比数据', '消融实验', '参数设置'])}的详细数据。",
        '示意图': f"图{figure_id}：示意图，通过{_extract_key_info(context, ['示例', '案例', '场景'])}直观展示了{_extract_key_info(context, ['方法', '算法', '模型'])}的工作原理。",
        '其他图表': f"图{figure_id}：{_extract_key_info(context, ['图表', '图示', '图形'])}，展示了{context[:50]}..."
    }
    
    description = templates.get(figure_type, templates['其他图表'])
    
    # 添加阅读建议
    reading_tips = {
        '架构图': "建议关注各组件之间的连接关系和数据流向。",
        '折线图': "建议关注曲线的趋势变化和关键拐点。",
        '柱状图': "建议关注各组数据的相对大小和显著性差异。",
        '散点图': "建议关注数据点的分布规律和异常值。",
        '热力图': "建议关注颜色深浅变化和模式识别。",
        '表格': "建议关注关键数据和最优结果。",
        '示意图': "建议结合文字说明理解图示含义。",
        '其他图表': "请结合上下文理解图表内容。"
    }
    
    description += f" {reading_tips.get(figure_type, reading_tips['其他图表'])}"
    
    return description


def _extract_key_info(context: str, keywords: List[str]) -> str:
    """从上下文中提取关键信息"""
    context_lower = context.lower()
    
    for keyword in keywords:
        if keyword in context_lower:
            # 尝试提取包含关键词的短语
            pattern = rf'[^\.,;!?:]*{keyword}[^\.,;!?:]*'
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0).strip()
    
    # 如果没有匹配到，返回通用描述
    return "相关"


def _count_components(context: str) -> int:
    """估算组件数量（简化处理）"""
    # 基于常见分隔符估算
    separators = ['，', '。', '；', ',', '.', ';', 'and', 'or', '、']
    
    for sep in separators:
        if sep in context:
            count = context.count(sep) + 1
            return min(count, 5)  # 最多返回5
    
    return 2  # 默认返回2


if __name__ == "__main__":
    # 测试代码
    test_structured_text = {
        'references': '''
        [1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. Advances in neural information processing systems, 30.
        
        [2] Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805.
        
        [3] Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. Advances in neural information processing systems, 33, 1877-1901.
        
        [4] Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., & Sutskever, I. (2019). Language models are unsupervised multitask learners. OpenAI blog, 1(8), 9.
        
        [5] Wang, X., Girshick, R., Gupta, A., & He, K. (2018). Non-local neural networks. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 7794-7803).
        '''
    }
    
    # 测试引用关系图谱生成
    citation_graph = generate_citation_graph(test_structured_text)
    print("Mermaid代码：")
    print(citation_graph['mermaid_code'])
    print("\n参考文献列表：")
    for ref in citation_graph['references']:
        print(f"- {ref['title']} ({ref['year']}) - {ref['description']}")
    
    # 测试图表描述生成
    test_figures = [
        {'id': 1, 'page': 3, 'index': 0, 'placeholder': '<figure>图1（详见原文第3页）</figure>'},
        {'id': 2, 'page': 5, 'index': 1, 'placeholder': '<figure>图2（详见原文第5页）</figure>'}
    ]
    
    test_full_text = """
    Figure 1 shows the architecture of our proposed Transformer model. The model consists of an encoder and a decoder. The encoder processes the input sequence and the decoder generates the output sequence.
    
    Figure 2 presents the performance comparison between our method and baseline methods. We can see that our method achieves higher accuracy on all datasets.
    """
    
    test_structured_text_with_figures = {
        'method': test_full_text,
        'experiment': "The experimental results are shown in Figure 2."
    }
    
    figure_descriptions = generate_figure_description(test_structured_text_with_figures, test_figures)
    print("\n图表描述：")
    for desc in figure_descriptions:
        print(f"图{desc['id']}（第{desc['page']}页）- {desc['type']}：")
        print(f"  {desc['description']}")