
from __future__ import annotations
from typing import Dict, Any
import hashlib
import fitz  # PyMuPDF

from summary_generator import generate_short_summary, generate_long_summary
def _rid(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:10]


def parse_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    MVP可用版：
    - 用 PyMuPDF 提取全文文本
    - 章节先给一个粗切（可被算法A替换为更准的section识别）
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    full_text = "\n".join(pages_text).strip()

    # 简单兜底：如果抽不出文本，给提示（演示不会空白）
    if not full_text:
        full_text = "⚠️ 未能从PDF提取到可读文本（可能是扫描版/图片PDF）。请换一篇可复制文本的PDF，或后续接OCR。"

    # 粗略“章节”切分（后续算法A可替换）
    sections = [{"name": "Full Text", "text": full_text}]

    request_id = _rid(str(len(pdf_bytes)) + full_text[:200])
    return {
        "request_id": request_id,
        "title": None,
        "authors": [],
        "abstract": None,
        "sections": sections,
        "full_text": full_text,
    }


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