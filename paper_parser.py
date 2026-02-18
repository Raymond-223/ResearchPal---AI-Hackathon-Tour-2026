#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文解析核心模块
功能：实现PDF文件读取、文本提取、章节结构化分块、元数据补全等核心功能
作者：算法工程师A
日期：2024-01-15
"""

import fitz  # PyMuPDF
import re
import requests
import time
from typing import Dict, List, Optional, Union, Tuple, Any

# 常量定义
MAX_PDF_SIZE = 20 * 1024 * 1024  # 20MB
MAX_PAGES = 100  # 最大处理页数
API_TIMEOUT = 5  # API超时时间（秒）
HEADER_FOOTER_KEYWORDS = ['page', 'copyright', 'doi', 'isbn', 'issn', 'abstract', 'introduction', 'references']
SECTION_KEYWORDS = {
    'abstract': ['abstract', '摘要'],
    'introduction': ['introduction', '引言', '前言', 'background'],
    'method': ['method', 'methods', 'methodology', '算法', '方法', '实现'],
    'experiment': ['experiment', 'experiments', 'evaluation', '实验', '评估', '测试'],
    'result': ['result', 'results', 'findings', '结果', '发现'],
    'discussion': ['discussion', '讨论', '分析'],
    'conclusion': ['conclusion', 'conclusions', '总结', '结论'],
    'references': ['references', 'bibliography', 'literature', '参考文献', '参考资料']
}
FORMULA_CHARS = '=+*∑∫∂∇Δ≡≈≠≤≥±×÷∈∉⊂⊃⊆⊇∪∩∧∨¬→←↔↦↤∀∃∄□◇◊△▲○●'


def extract_pdf_text(pdf_input: Union[bytes, str], max_pages: int = MAX_PAGES) -> Dict[str, Any]:
    """
    从PDF文件中提取文本内容并进行结构化处理
    
    Args:
        pdf_input: bytes（文件流）或 str（文件路径）
        max_pages: 最大处理页数
        
    Returns:
        Dict: 包含结构化文本、章节信息、公式图表位置等
    """
    try:
        # 打开PDF文件
        if isinstance(pdf_input, bytes):
            doc = fitz.open(stream=pdf_input, filetype="pdf")
        elif isinstance(pdf_input, str):
            doc = fitz.open(pdf_input)
        else:
            raise ValueError("输入类型错误，必须是bytes或str")
        
        # 检查文件大小
        if len(doc) > max_pages:
            print(f"警告：PDF页数({len(doc)})超过最大处理页数({max_pages})，将只处理前{max_pages}页")
            pages_to_process = range(max_pages)
        else:
            pages_to_process = range(len(doc))
        
        # 初始化结果容器
        full_text = []
        structured_text = {'preamble': []}
        current_section = 'preamble'
        formulas = []
        figures = []
        
        # 逐页提取文本
        for page_num in pages_to_process:
            page = doc[page_num]
            
            # 获取文本块（包含坐标信息）
            blocks = page.get_text("blocks")
            
            # 按y坐标排序文本块
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            # 合并文本块为段落
            page_text = []
            current_paragraph = []
            prev_y = None
            
            for block in blocks:
                text = block[4].strip()
                if not text:
                    continue
                
                # 判断是否为页眉页脚
                if _is_header_footer(text, page_num, len(doc)):
                    continue
                
                # 判断是否为公式
                if _is_formula_block(text):
                    formula_placeholder = f"<formula>公式{len(formulas)+1}（详见原文第{page_num+1}页）</formula>"
                    formulas.append({
                        'id': len(formulas) + 1,
                        'page': page_num + 1,
                        'content': text,
                        'placeholder': formula_placeholder
                    })
                    current_paragraph.append(formula_placeholder)
                    continue
                
                # 按坐标合并段落
                current_y = block[1]
                if prev_y is not None and current_y - prev_y > 15:
                    if current_paragraph:
                        page_text.append(' '.join(current_paragraph))
                        current_paragraph = []
                
                current_paragraph.append(text)
                prev_y = current_y
            
            if current_paragraph:
                page_text.append(' '.join(current_paragraph))
            
            # 处理图片
            images = page.get_images()
            for img_index, img in enumerate(images):
                figure_placeholder = f"<figure>图{len(figures)+1}（详见原文第{page_num+1}页）</figure>"
                figures.append({
                    'id': len(figures) + 1,
                    'page': page_num + 1,
                    'index': img_index,
                    'placeholder': figure_placeholder
                })
                # 在适当位置插入图片占位符
                if page_text:
                    page_text.append(figure_placeholder)
            
            # 合并页面文本
            page_content = '\n\n'.join(page_text)
            full_text.append(page_content)
            
            # 章节识别与结构化
            section_text = _identify_sections(page_content, current_section)
            for section, content in section_text.items():
                if section != current_section:
                    current_section = section
                    if section not in structured_text:
                        structured_text[section] = []
                structured_text[current_section].extend(content)
        
        doc.close()
        
        # 合并结构化文本
        for section in structured_text:
            structured_text[section] = '\n\n'.join(structured_text[section])
        
        return {
            'full_text': '\n\n'.join(full_text),
            'structured_text': structured_text,
            'formulas': formulas,
            'figures': figures,
            'metadata': {
                'total_pages': len(doc),
                'processed_pages': len(pages_to_process),
                'formula_count': len(formulas),
                'figure_count': len(figures)
            }
        }
        
    except fitz.fitz.FileDataError:
        raise ValueError("文件格式错误：无法解析PDF文件，可能是文件损坏")
    except fitz.fitz.PDFError as e:
        if "encrypted" in str(e).lower():
            raise ValueError("无法解析加密文件")
        else:
            raise ValueError(f"PDF解析错误：{str(e)}")
    except Exception as e:
        raise ValueError(f"解析失败：{str(e)}")


def get_paper_metadata(arxiv_id: Optional[str] = None, doi: Optional[str] = None, 
                      title: Optional[str] = None) -> Dict[str, str]:
    """
    从ArXiv API获取论文元数据
    
    Args:
        arxiv_id: ArXiv ID
        doi: DOI编号
        title: 论文标题
        
    Returns:
        Dict: 论文元数据
    """
    metadata = {}
    
    # 优先使用ArXiv ID查询
    if arxiv_id:
        try:
            url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            response = requests.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            # 解析XML响应
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 命名空间处理
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # 提取核心元数据
            entry = root.find('.//atom:entry', ns)
            if entry:
                title_elem = entry.find('.//atom:title', ns)
                if title_elem is not None:
                    metadata['title'] = title_elem.text.strip()
                
                authors = []
                for author in entry.findall('.//atom:author', ns):
                    name = author.find('.//atom:name', ns)
                    if name is not None:
                        authors.append(name.text.strip())
                metadata['authors'] = ', '.join(authors)
                
                published = entry.find('.//atom:published', ns)
                if published is not None:
                    metadata['published_date'] = published.text[:10]
                
                summary = entry.find('.//atom:summary', ns)
                if summary is not None:
                    metadata['abstract'] = summary.text.strip()
                
                # 获取分类标签
                categories = []
                for category in entry.findall('.//atom:category', ns):
                    if 'term' in category.attrib:
                        categories.append(category.attrib['term'])
                metadata['categories'] = ', '.join(categories)
                
                # ArXiv链接
                metadata['arxiv_link'] = f"https://arxiv.org/abs/{arxiv_id}"
        
        except requests.RequestException as e:
            print(f"ArXiv API调用失败：{str(e)}")
        except ET.ParseError as e:
            print(f"XML解析失败：{str(e)}")
    
    # 如果没有获取到元数据，尝试从标题推断
    if not metadata and title:
        metadata['title'] = title
        metadata['authors'] = "未知"
        metadata['published_date'] = "未知"
        metadata['abstract'] = ""
        metadata['categories'] = ""
        metadata['arxiv_link'] = ""
    
    return metadata


def parse_paper(pdf_input: Union[bytes, str], arxiv_id: Optional[str] = None,
                doi: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
    """
    完整的论文解析流程
    
    Args:
        pdf_input: PDF输入（bytes或str）
        arxiv_id: ArXiv ID（可选）
        doi: DOI编号（可选）
        title: 论文标题（可选）
        
    Returns:
        Dict: 完整的解析结果
    """
    start_time = time.time()
    
    # 1. 提取PDF文本
    text_result = extract_pdf_text(pdf_input)
    
    # 2. 获取元数据
    metadata = get_paper_metadata(arxiv_id, doi, title)
    
    # 3. 合并结果
    result = {
        'text_data': text_result,
        'metadata': metadata,
        'processing_time': time.time() - start_time,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    }
    
    return result


def _is_header_footer(text: str, page_num: int, total_pages: int) -> bool:
    """判断文本是否为页眉页脚"""
    # 纯数字（可能是页码）
    if re.match(r'^\d+$', text):
        return True
    
    # 文本长度很短
    if len(text) < 100:
        # 检查关键词
        text_lower = text.lower()
        for keyword in HEADER_FOOTER_KEYWORDS:
            if keyword in text_lower:
                return True
        
        # 检查是否包含页码格式
        page_patterns = [
            r'page \d+',
            r'\d+ / \d+',
            r'\d+ of \d+'
        ]
        for pattern in page_patterns:
            if re.search(pattern, text_lower):
                return True
    
    return False


def _is_formula_block(text: str) -> bool:
    """判断文本块是否为公式"""
    # 长度限制
    if len(text) > 200:
        return False
    
    # 计算公式字符占比
    formula_char_count = sum(1 for char in text if char in FORMULA_CHARS)
    formula_ratio = formula_char_count / len(text) if text else 0
    
    # 公式字符占比超过15%判定为公式
    return formula_ratio > 0.15


def _identify_sections(text: str, current_section: str) -> Dict[str, List[str]]:
    """识别文本中的章节"""
    result = {current_section: []}
    lines = text.split('\n')
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        # 检查是否为章节标题
        for section, keywords in SECTION_KEYWORDS.items():
            for keyword in keywords:
                # 匹配章节标题格式
                if re.match(rf'^(section\s*\d+(\.\d+)*\s*)?{keyword}(:|\s*$)', line_stripped):
                    # 新章节开始
                    if section != current_section:
                        current_section = section
                        result[current_section] = []
                    break
        
        result[current_section].append(line)
    
    return result


if __name__ == "__main__":
    # 测试代码
    try:
        # 替换为实际的PDF文件路径
        test_pdf_path = "test_paper.pdf"
        
        # 解析PDF
        result = parse_paper(test_pdf_path)
        
        # 打印结果统计
        print(f"解析完成，耗时：{result['processing_time']:.2f}秒")
        print(f"总页数：{result['text_data']['metadata']['total_pages']}")
        print(f"公式数量：{result['text_data']['metadata']['formula_count']}")
        print(f"图表数量：{result['text_data']['metadata']['figure_count']}")
        print(f"识别的章节：{list(result['text_data']['structured_text'].keys())}")
        
        # 打印摘要（如果存在）
        if 'abstract' in result['text_data']['structured_text']:
            abstract = result['text_data']['structured_text']['abstract']
            print(f"\n摘要：{abstract[:200]}...")
            
    except Exception as e:
        print(f"测试失败：{str(e)}")