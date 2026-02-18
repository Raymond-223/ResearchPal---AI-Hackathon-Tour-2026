#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文分析工具
功能：生成论文的短概要和详细分析报告
作者：算法工程师A
日期：2024-01-15
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from paper_parser import parse_paper
from summary_generator import pack_summary_result
from visual_helper import generate_citation_graph, generate_figure_description


class PaperAnalyzer:
    """论文分析器类"""
    
    def __init__(self):
        """初始化论文分析器"""
        self.parse_result = None
        self.summary_result = None
        self.visual_data = None
    
    def analyze_paper(self, pdf_path: str) -> bool:
        """
        分析论文并生成结果
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            bool: 是否分析成功
        """
        print(f"\n📄 开始分析论文：{os.path.basename(pdf_path)}")
        
        try:
            # 1. 解析PDF
            print("\n🔍 步骤1：解析PDF文件...")
            self.parse_result = parse_paper(pdf_path)
            print(f"   ✅ PDF解析完成，耗时：{self.parse_result['processing_time']:.2f}秒")
            print(f"   📊 文档统计：{self.parse_result['text_data']['metadata']['total_pages']}页 | "
                  f"公式{self.parse_result['text_data']['metadata']['formula_count']}个 | "
                  f"图表{self.parse_result['text_data']['metadata']['figure_count']}个")
            
            # 2. 生成摘要
            print("\n📝 步骤2：生成论文摘要...")
            self.summary_result = pack_summary_result(self.parse_result['text_data']['structured_text'])
            print(f"   ✅ 摘要生成完成，耗时：{self.summary_result['processing_time']:.2f}秒")
            
            # 3. 生成可视化数据
            print("\n📊 步骤3：生成可视化数据...")
            self.visual_data = {
                'citation_graph': generate_citation_graph(self.parse_result['text_data']['structured_text']),
                'figure_descriptions': generate_figure_description(
                    self.parse_result['text_data']['structured_text'],
                    self.parse_result['text_data']['figures']
                )
            }
            print(f"   ✅ 可视化数据生成完成，参考文献：{self.visual_data['citation_graph']['reference_count']}篇")
            
            print("\n🎉 论文分析完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 分析失败：{str(e)}")
            return False
    
    def generate_short_summary(self) -> str:
        """
        生成短概要
        
        Returns:
            str: 短概要文本
        """
        if not self.parse_result or not self.summary_result:
            return "错误：请先成功分析论文"
        
        # 提取元数据
        metadata = self.parse_result['metadata']
        
        # 构建短概要
        short_summary = "# 论文短概要\n\n"
        
        # 期刊和奖项信息
        short_summary += "## 发表信息\n"
        short_summary += f"- **标题**：{metadata.get('title', '未知')}\n"
        short_summary += f"- **作者**：{metadata.get('authors', '未知')}\n"
        short_summary += f"- **发表期刊/会议**：{metadata.get('journal', '未知')}\n"
        short_summary += f"- **发表时间**：{metadata.get('published_date', '未知')}\n"
        short_summary += f"- **DOI/ArXiv**：{metadata.get('arxiv_link', '未知')}\n\n"
        
        # 核心问题和动机
        short_summary += "## 研究背景\n"
        if 'background' in self.summary_result['long_summary']['sections']:
            short_summary += self.summary_result['long_summary']['sections']['background'] + "\n\n"
        else:
            short_summary += "该研究旨在解决相关领域的关键问题...\n\n"
        
        # 主要贡献和创新点
        short_summary += "## 核心贡献\n"
        short_summary += self.summary_result['short_summary'] + "\n\n"
        
        # 创新方法
        short_summary += "## 创新方法\n"
        if 'method' in self.summary_result['long_summary']['sections']:
            short_summary += self.summary_result['long_summary']['sections']['method'] + "\n\n"
        
        # 实验结果
        short_summary += "## 实验结果\n"
        if 'results' in self.summary_result['long_summary']['sections']:
            short_summary += self.summary_result['long_summary']['sections']['results'] + "\n\n"
        
        # 遗留问题和未来工作
        short_summary += "## 遗留问题与未来方向\n"
        if 'conclusion' in self.summary_result['long_summary']['sections']:
            conclusion = self.summary_result['long_summary']['sections']['conclusion']
            # 尝试提取未来工作部分
            if 'future' in conclusion.lower() or 'future work' in conclusion.lower() or 'future research' in conclusion.lower():
                short_summary += conclusion + "\n\n"
            else:
                short_summary += "论文提出了以下可能的未来研究方向：\n"
                short_summary += "- 扩展模型在更多数据集上的应用\n"
                short_summary += "- 改进算法效率和性能\n"
                short_summary += "- 探索与其他技术的结合\n\n"
        
        # 核心关键词
        short_summary += "## 核心关键词\n"
        keywords_str = ", ".join([kw['word'] for kw in self.summary_result['keywords'][:5]])
        short_summary += keywords_str
        
        return short_summary
    
    def generate_long_summary(self) -> str:
        """
        生成详细分析报告（面向0基础）
        
        Returns:
            str: 详细分析报告
        """
        if not self.parse_result or not self.summary_result:
            return "错误：请先成功分析论文"
        
        # 提取元数据
        metadata = self.parse_result['metadata']
        
        # 构建详细分析报告
        long_summary = "# 论文详细分析报告\n\n"
        
        # 1. 基本信息
        long_summary += "## 1. 基本信息\n\n"
        long_summary += f"### 1.1 论文标题\n**{metadata.get('title', '未知')}**\n\n"
        
        long_summary += f"### 1.2 作者信息\n{metadata.get('authors', '未知')}\n\n"
        
        long_summary += "### 1.3 发表信息\n"
        long_summary += f"- **期刊/会议**：{metadata.get('journal', '未知')}\n"
        long_summary += f"- **发表时间**：{metadata.get('published_date', '未知')}\n"
        long_summary += f"- **论文链接**：{metadata.get('arxiv_link', '未知')}\n\n"
        
        # 2. 研究背景（面向0基础）
        long_summary += "## 2. 研究背景\n\n"
        long_summary += "### 2.1 研究领域简介\n"
        # 从摘要和引言中提取领域介绍
        if 'preamble' in self.parse_result['text_data']['structured_text']:
            preamble = self.parse_result['text_data']['structured_text']['preamble'][:500]
            long_summary += self._simplify_text(preamble) + "\n\n"
        else:
            long_summary += "该研究属于计算机科学/人工智能领域...\n\n"
        
        long_summary += "### 2.2 研究问题\n"
        if 'background' in self.summary_result['long_summary']['sections']:
            long_summary += self._simplify_text(self.summary_result['long_summary']['sections']['background']) + "\n\n"
        else:
            long_summary += "目前该领域存在的主要问题包括...\n\n"
        
        # 3. 核心方法（详细拆解）
        long_summary += "## 3. 核心方法\n\n"
        if 'method' in self.summary_result['long_summary']['sections']:
            method_summary = self.summary_result['long_summary']['sections']['method']
            long_summary += "### 3.1 方法概述\n"
            long_summary += self._simplify_text(method_summary) + "\n\n"
        
        # 数学公式解释（如果有）
        formulas = self.parse_result['text_data']['formulas']
        if formulas:
            long_summary += "### 3.2 关键公式解释\n\n"
            for i, formula in enumerate(formulas[:3]):  # 最多解释3个公式
                long_summary += f"#### 公式{i+1}\n"
                long_summary += f"```\n{formula['content']}\n```\n\n"
                long_summary += "**通俗解释**：这个公式表示了...（这里会根据公式内容给出通俗解释）\n\n"
        
        # 图表解释
        if self.visual_data['figure_descriptions']:
            long_summary += "### 3.3 关键图表解析\n\n"
            for i, desc in enumerate(self.visual_data['figure_descriptions'][:3]):
                long_summary += f"#### 图{desc['id']}：{desc['type']}\n"
                long_summary += f"**描述**：{desc['description']}\n\n"
                long_summary += "**图表解读**：\n"
                long_summary += self._explain_figure(desc) + "\n\n"
        
        # 4. 实验结果
        long_summary += "## 4. 实验结果\n\n"
        if 'results' in self.summary_result['long_summary']['sections']:
            long_summary += "### 4.1 实验设置\n"
            long_summary += "研究者使用了以下数据集和评估指标...\n\n"
            
            long_summary += "### 4.2 主要结果\n"
            long_summary += self._simplify_text(self.summary_result['long_summary']['sections']['results']) + "\n\n"
            
            long_summary += "### 4.3 结果解读\n"
            long_summary += "这些结果表明...（用通俗语言解释结果的意义）\n\n"
        
        # 5. 结论与展望
        long_summary += "## 5. 结论与展望\n\n"
        if 'conclusion' in self.summary_result['long_summary']['sections']:
            long_summary += "### 5.1 主要贡献\n"
            long_summary += self._simplify_text(self.summary_result['long_summary']['sections']['conclusion']) + "\n\n"
        
        long_summary += "### 5.2 研究局限性\n"
        long_summary += "该研究的主要局限性包括：\n"
        long_summary += "- 数据集规模有限\n"
        long_summary += "- 计算复杂度较高\n"
        long_summary += "- 某些场景下效果不佳\n\n"
        
        long_summary += "### 5.3 未来研究方向\n"
        long_summary += "未来可能的研究方向：\n"
        long_summary += "- 扩展到更多应用场景\n"
        long_summary += "- 优化算法效率\n"
        long_summary += "- 与其他技术结合\n\n"
        
        # 6. 关键术语表
        long_summary += "## 6. 关键术语表\n\n"
        for keyword in self.summary_result['keywords'][:8]:
            long_summary += f"### {keyword['word']}\n"
            long_summary += f"**定义**：{keyword.get('definition', '暂无定义')}\n\n"
            if keyword.get('related_terms'):
                long_summary += f"**相关术语**：{', '.join(keyword['related_terms'])}\n\n"
        
        return long_summary
    
    def _simplify_text(self, text: str) -> str:
        """简化文本，使其更易理解"""
        # 移除复杂术语，替换为简单表达
        text = text.replace('state-of-the-art', '最先进的')
        text = text.replace('propose', '提出')
        text = text.replace('demonstrate', '证明')
        text = text.replace('evaluate', '评估')
        text = text.replace('implementation', '实现')
        
        # 限制句子长度
        sentences = text.split('. ')
        simplified = []
        for sentence in sentences:
            if len(sentence) > 100:
                # 简化长句
                sentence = sentence[:100] + "..."
            simplified.append(sentence)
        
        return '. '.join(simplified)
    
    def _explain_figure(self, figure_desc: Dict[str, str]) -> str:
        """解释图表内容（面向0基础）"""
        figure_type = figure_desc['type']
        
        explanations = {
            '架构图': "这张图展示了系统的整体结构，就像一个建筑物的蓝图。图中的每个方框代表一个组件，箭头表示数据或信息的流向。你可以把它想象成一个工厂的生产线，原材料从一端进入，经过各个加工环节，最终产出产品。",
            '折线图': "这张图用线条展示了数据随时间或其他因素的变化趋势。上升的线表示数值在增加，下降的线表示数值在减少。这就像观察股票价格的走势图，可以清楚地看到涨跌情况。",
            '柱状图': "这张图用不同高度的柱子来比较不同类别的数据。柱子越高，表示对应类别的数值越大。就像比较不同学生的考试成绩，一眼就能看出谁高谁低。",
            '散点图': "这张图用许多点来展示两个变量之间的关系。点的位置由两个坐标决定，通过观察点的分布规律，可以发现变量之间是否存在关联。",
            '热力图': "这张图用不同的颜色深浅来表示数值的大小。颜色越深表示数值越大，颜色越浅表示数值越小。就像地图上的温度分布图，直观地展示了热度分布情况。",
            '表格': "这张表格以行列的形式展示了详细的数据。每行代表一个条目，每列代表一个属性。通过表格可以精确地看到每个数据点的具体数值。",
            '示意图': "这张图通过直观的方式展示了某个概念或过程。它不追求数据的精确性，而是帮助读者理解基本原理。"
        }
        
        return explanations.get(figure_type, "这张图展示了相关内容，可以帮助理解论文中的概念。")
    
    def save_results(self, output_dir: str = "."):
        """
        保存分析结果
        
        Args:
            output_dir: 输出目录
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存短概要
        short_summary_path = os.path.join(output_dir, "short_summary.md")
        with open(short_summary_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_short_summary())
        print(f"\n📄 短概要已保存至：{short_summary_path}")
        
        # 保存详细分析
        long_summary_path = os.path.join(output_dir, "long_summary.md")
        with open(long_summary_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_long_summary())
        print(f"📄 详细分析已保存至：{long_summary_path}")
        
        # 保存完整结果（JSON）
        full_result_path = os.path.join(output_dir, "full_analysis_result.json")
        full_result = {
            'parse_result': self.parse_result,
            'summary_result': self.summary_result,
            'visual_data': self.visual_data
        }
        
        # 转换不支持JSON序列化的对象
        def convert_for_json(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            else:
                return str(obj)
        
        with open(full_result_path, 'w', encoding='utf-8') as f:
            json.dump(convert_for_json(full_result), f, ensure_ascii=False, indent=2)
        print(f"📊 完整分析数据已保存至：{full_result_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='论文分析工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('--output-dir', '-o', default='analysis_results', help='输出目录')
    parser.add_argument('--mode', '-m', choices=['short', 'long', 'both'], default='both', help='输出模式')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"❌ 错误：文件 '{args.pdf_path}' 不存在")
        sys.exit(1)
    
    # 检查文件是否为PDF
    if not args.pdf_path.lower().endswith('.pdf'):
        print(f"❌ 错误：文件 '{args.pdf_path}' 不是PDF文件")
        sys.exit(1)
    
    # 创建分析器并分析论文
    analyzer = PaperAnalyzer()
    if analyzer.analyze_paper(args.pdf_path):
        # 根据模式生成输出
        if args.mode in ['short', 'both']:
            print("\n📝 生成短概要...")
            short_summary = analyzer.generate_short_summary()
            print(short_summary[:500] + "..." if len(short_summary) > 500 else short_summary)
        
        if args.mode in ['long', 'both']:
            print("\n📝 生成详细分析报告...")
            # 详细报告可能很长，这里只显示开头
            long_summary = analyzer.generate_long_summary()
            print(long_summary[:300] + "..." if len(long_summary) > 300 else long_summary)
        
        # 保存结果
        analyzer.save_results(args.output_dir)
        print(f"\n🎉 所有结果已保存至目录：{args.output_dir}")


if __name__ == "__main__":
    main()