
from __future__ import annotations
from typing import Dict, Any
import hashlib
import fitz  # PyMuPDF

from summary_generator import generate_short_summary, generate_long_summary
def _rid(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:10]


def parse_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Enhanced version:
    - Extract full text with PyMuPDF
    - Extract metadata (title, authors, abstract)
    - Detect sections and count citations
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Extract metadata from PDF
    metadata = doc.metadata
    pdf_title = metadata.get("title", "").strip() if metadata else ""
    pdf_author = metadata.get("author", "").strip() if metadata else ""

    # Extract text from all pages
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    full_text = "\n".join(pages_text).strip()

    page_count = len(doc)
    doc.close()

    # Fallback if no text extracted
    if not full_text:
        full_text = "⚠️ 未能从PDF提取到可读文本（可能是扫描版/图片PDF）。请换一篇可复制文本的PDF，或后续接OCR。"

    # Extract title from text if not in metadata
    title = pdf_title or _extract_title_from_text(full_text)

    # Extract authors
    authors = _extract_authors_from_text(full_text, pdf_author)

    # Extract abstract
    abstract = _extract_abstract_from_text(full_text)

    # Count citations
    citations_count = _count_citations(full_text)

    # Detect sections
    sections = _detect_sections(full_text)

    request_id = _rid(str(len(pdf_bytes)) + full_text[:200])
    return {
        "request_id": request_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "pages": page_count,
        "citations_count": citations_count,
        "sections": sections,
        "full_text": full_text,
    }


def _extract_title_from_text(text: str) -> str:
    """Extract title from first few lines of text"""
    import re

    lines = text.split('\n')
    # Look at first 15 lines for title
    for i, line in enumerate(lines[:15]):
        line = line.strip()
        # Title is usually a longer line (20-200 chars) without special patterns
        if 20 < len(line) < 200 and not re.match(r'^\d+$|^[A-Z]{2,}$|^http', line):
            # Avoid lines that look like headers, page numbers, or URLs
            if not line.lower().startswith(('abstract', 'introduction', 'keywords', 'arxiv')):
                return line

    return "Untitled"


def _extract_authors_from_text(text: str, pdf_author: str = "") -> list:
    """Extract author names from text"""
    import re

    if pdf_author:
        # Split by common delimiters
        authors = re.split(r'[,;]|\sand\s', pdf_author)
        return [a.strip() for a in authors if a.strip()]

    # Look for author patterns in first 30 lines
    lines = text.split('\n')
    for i, line in enumerate(lines[:30]):
        line = line.strip()
        # Look for lines with capitalized names (2-4 words, each capitalized)
        if re.match(r'^([A-Z][a-z]+\s+){1,3}[A-Z][a-z]+$', line):
            # Check if next few lines also match (multiple authors)
            authors = [line]
            for j in range(i+1, min(i+5, len(lines))):
                next_line = lines[j].strip()
                if re.match(r'^([A-Z][a-z]+\s+){1,3}[A-Z][a-z]+$', next_line):
                    authors.append(next_line)
                else:
                    break
            if authors:
                return authors

    return []


def _extract_abstract_from_text(text: str) -> str:
    """Extract abstract section from text"""
    import re

    # Look for abstract section
    abstract_match = re.search(
        r'(?i)abstract\s*[:\-]?\s*\n\s*(.+?)(?=\n\s*\n|\n\s*(?:introduction|keywords|1\.|I\.))',
        text,
        re.DOTALL
    )

    if abstract_match:
        abstract = abstract_match.group(1).strip()
        # Limit to reasonable length
        if len(abstract) > 2000:
            abstract = abstract[:2000] + "..."
        return abstract

    return None


def _count_citations(text: str) -> int:
    """Count citations in text"""
    import re

    # Count [1], [2], etc.
    bracket_citations = len(re.findall(r'\[\d+\]', text))

    # Count (Author, Year) style citations
    author_year_citations = len(re.findall(r'\([A-Z][a-z]+(?:\s+et al\.)?,?\s+\d{4}\)', text))

    # Return the higher count (papers usually use one style)
    return max(bracket_citations, author_year_citations)


def _detect_sections(text: str) -> list:
    """Detect paper sections"""
    import re

    sections = []

    # Common section patterns
    section_patterns = [
        (r'(?i)abstract', 'Abstract'),
        (r'(?i)introduction|1\.\s*introduction', 'Introduction'),
        (r'(?i)related work|2\.\s*related', 'Related Work'),
        (r'(?i)method|approach|3\.\s*method', 'Methods'),
        (r'(?i)experiment|result|4\.\s*experiment', 'Results'),
        (r'(?i)discussion|5\.\s*discussion', 'Discussion'),
        (r'(?i)conclusion|6\.\s*conclusion', 'Conclusion'),
        (r'(?i)reference|bibliography', 'References'),
    ]

    for pattern, name in section_patterns:
        match = re.search(pattern, text)
        if match:
            sections.append({"name": name, "position": match.start()})

    # If no sections detected, return full text
    if not sections:
        return [{"name": "Full Text", "text": text}]

    # Sort by position
    sections.sort(key=lambda x: x['position'])

    # Extract text for each section
    for i, section in enumerate(sections):
        start = section['position']
        end = sections[i+1]['position'] if i+1 < len(sections) else len(text)
        section['text'] = text[start:end].strip()[:500]  # Preview only
        del section['position']

    return sections


import uuid
from typing import Dict, Any, Optional
import uuid
from backend.app.services.model_service import call_genstudio_chat

# ============== 优化的Prompt配置 ==============
# 增强版System Prompt
SYSTEM_PROMPT = """You are a world-class academic paper analyst. Your expertise spans computer science, mathematics, physics, biology, medicine, and engineering. You excel at:

1. Distilling complex research into clear, concise summaries
2. Identifying novel contributions and innovations
3. Explaining technical methods with precision
4. Evaluating experimental rigor and results
5. Providing balanced criticism of limitations

Always structure your output professionally, use precise academic language, and focus on what matters most to researchers."""

# One-Liner Prompt - 强调核心贡献和创新
ONE_LINER_PROMPT = """Analyze this academic paper and provide a ONE-SENTENCE summary that captures:
- The specific problem being solved
- The core novel approach or contribution
- The key quantitative or qualitative result

Example format: "This paper presents [novel approach] for [problem], achieving [key result] on [benchmark/dataset]."

Paper text: """

# Detailed Prompt - 要求结构化输出
DETAILED_PROMPT = """Provide a comprehensive structured summary of this academic paper (~400 words) covering:

1. **Background & Motivation** (2-3 sentences): What problem does the paper address? Why is it important?

2. **Core Contribution** (2-3 sentences): What is the novel approach or method? What are the key innovations?

3. **Method Summary** (3-4 sentences): How does the approach work? What are the main technical components?

4. **Key Results** (2-3 sentences): What experiments were conducted? What were the main findings and improvements?

5. **Limitations & Future Work** (1-2 sentences): What are the paper's limitations? What future directions are suggested?

Paper text: """

# Mermaid图生成Prompt
MERMAID_PROMPT = """Based on this paper, generate a Mermaid flowchart showing the paper's methodology or framework.

Requirements:
- Use clear node labels describing each step/component
- Show the flow from input to output
- Include key technical components as nodes
- Keep it simple but informative

Paper text: """


# ============== 中文版 Prompt 配置 ==============
SYSTEM_PROMPT_ZH = """你是一位世界级的学术论文分析师。你的专业涵盖计算机科学、数学、物理学、生物学、医学和工程学。你擅长：

1. 将复杂的研究提炼成清晰、简洁的摘要
2. 识别新颖的贡献和创新
3. 精确解释技术方法
4. 评估实验的严谨性和结果
5. 对局限性提供平衡的批评

始终以专业的结构化方式输出内容，使用精确的学术语言，聚焦于研究者最关心的内容。"""

ONE_LINER_PROMPT_ZH = """分析这篇学术论文，提供一句总结，包含：
- 要解决的具体问题
- 核心的新颖方法或贡献
- 关键的定量或定性结果

示例格式："本文提出了[新颖方法]用于[问题]，在[基准/数据集]上取得了[关键结果]。"

论文文本："""

DETAILED_PROMPT_ZH = """请提供这篇学术论文的综合结构化摘要（约400字），涵盖：

1. **背景与动机**（2-3句）：论文解决了什么问题？为什么重要？

2. **核心贡献**（2-3句）：什么是新颖的方法或技术？关键创新点是什么？

3. **方法概述**（3-4句）：方法是如何工作的？主要技术组件是什么？

4. **关键结果**（2-3句）：进行了哪些实验？主要发现和改进是什么？

5. **局限性与未来工作**（1-2句）：论文的局限性是什么？有哪些未来方向？

论文文本："""

MERMAID_PROMPT_ZH = """根据这篇论文，生成一个Mermaid流程图来展示论文的方法论或框架。

要求：
- 使用清晰的节点标签描述每个步骤/组件
- 展示从输入到输出的流程
- 包含关键的技术组件作为节点
- 保持简洁但信息丰富

论文文本："""


def summarize_text(text: str, mode: str = "mvp", model: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    # 根据语言选择对应的 Prompt
    if language == "zh":
        system_prompt = SYSTEM_PROMPT_ZH
        one_liner_prompt = ONE_LINER_PROMPT_ZH
        detailed_prompt = DETAILED_PROMPT_ZH
        mermaid_prompt = MERMAID_PROMPT_ZH
    else:
        system_prompt = SYSTEM_PROMPT
        one_liner_prompt = ONE_LINER_PROMPT
        detailed_prompt = DETAILED_PROMPT
        mermaid_prompt = MERMAID_PROMPT

    # 1. Try GenStudio API if model is specified
    if model and model != "mvp-default" and not model.startswith("error"):
        try:
            # 优化文本截断策略：优先保留摘要、引言、结论
            truncated_text = _smart_truncate(text)

            # One Liner - 使用优化的prompt
            messages_one = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": one_liner_prompt + truncated_text}
            ]
            one_liner = call_genstudio_chat(messages_one, model)

            # Detailed - 使用优化的prompt
            messages_detail = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": detailed_prompt + truncated_text}
            ]
            detailed = call_genstudio_chat(messages_detail, model)

            # Mermaid - 添加图生成
            messages_mermaid = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mermaid_prompt + truncated_text}
            ]
            mermaid = call_genstudio_chat(messages_mermaid, model)

            return {
                "request_id": str(uuid.uuid4()),
                "one_liner": one_liner,
                "detailed": detailed,
                "mermaid": mermaid,
            }
        except Exception as e:
            print(f"GenStudio API call failed: {e}. Falling back to local logic.")
            # Fallback to local logic below

    # 2. Local Mock Logic (Fallback)
    structured = {"preamble": text}

    one_liner = generate_short_summary(structured)

    long_pack = generate_long_summary(structured)
    # long_pack = {"sections": {...}, "full_text": "..."}
    detailed = long_pack.get("full_text", "")

    # 先保持你们现有 mermaid 生成逻辑；如果没有就返回空字符串
    mermaid = ""  # or your existing mermaid builder

    # 根据语言添加不同的前缀标签
    if language == "zh":
        return {
            "request_id": str(uuid.uuid4()),
            "one_liner": f"【1分钟速览】{one_liner}",
            "detailed": f"【10分钟精读】{detailed}",
            "mermaid": mermaid,
        }
    else:
        return {
            "request_id": str(uuid.uuid4()),
            "one_liner": f"【1分钟速览】{one_liner}",
            "detailed": f"【10分钟精读】{detailed}",
            "mermaid": mermaid,
        }


def _smart_truncate(text: str, max_length: int = 8000) -> str:
    """智能截断文本，优先保留重要部分（摘要、引言、结论）"""
    # 尝试提取摘要
    abstract_match = None
    intro_match = None
    conclusion_match = None

    # 简单正则匹配（实际可用更复杂的section detection）
    import re
    abstract_match = re.search(r'(?i)abstract\s*[:\-]?\s*(.{100,1500}?)(?=\n\n|introduction|1\.|I\.)', text)
    intro_match = re.search(r'(?i)(introduction|1\.\s*)[^\n]{10,2000}', text)
    conclusion_match = re.search(r'(?i)(conclusion|discussion|5\.\s*|6\.\s*|related work)[^\n]{10,2000}', text)

    # 构建优先保留的文本
    priority_parts = []

    if abstract_match:
        priority_parts.append(abstract_match.group(1).strip())

    if conclusion_match:
        priority_parts.append(conclusion_match.group(0).strip())

    if intro_match:
        priority_parts.append(intro_match.group(0).strip())

    # 合并优先部分
    priority_text = "\n\n".join(priority_parts)

    if len(priority_text) >= max_length * 0.6:
        # 如果优先部分已经足够，返回截断后的优先部分
        return priority_text[:max_length]

    # 否则，追加正文剩余部分
    remaining = max_length - len(priority_text)
    return (priority_text + "\n\n" + text[:remaining])[:max_length]