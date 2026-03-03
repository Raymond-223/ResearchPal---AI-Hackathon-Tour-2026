from __future__ import annotations
import os
import time
import requests
import gradio as gr
from gradio_utils import (
    validate_pdf_file,
    create_error_message,
    create_success_message,
    create_loading_message,
    retry_on_error,
    timed
)
from gradio_config import TIMEOUT_CONFIG, FILE_UPLOAD_CONFIG
from gradio_ui import UIComponents
from keyboard_shortcuts import get_keyboard_shortcuts
from export_utils import ExportManager

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Load external CSS
css_path = os.path.join(os.path.dirname(__file__), "gradio_styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        external_css = f.read()
except FileNotFoundError:
    print(f"⚠️ Warning: Could not find {css_path}, using inline CSS only")
    external_css = ""

@timed
def call_parse(pdf_file):
    # 1) 没有上传文件
    if pdf_file is None:
        return "", {"error": "请先上传一个PDF文件再点击解析。"}, "", "", 0, 0

    # 2) Gradio File 可能返回：str 路径 / dict / 临时文件对象
    path = None
    if isinstance(pdf_file, str):
        path = pdf_file
    elif isinstance(pdf_file, dict):
        path = pdf_file.get("path") or pdf_file.get("name")
    else:
        path = getattr(pdf_file, "name", None)

    if not path:
        return "", {"error": f"无法识别上传文件对象：{type(pdf_file)}"}, "", "", 0, 0

    # 文件验证
    is_valid, error_msg = validate_pdf_file(path, FILE_UPLOAD_CONFIG["max_file_size"])
    if not is_valid:
        return "", {"error": error_msg}, "", "", 0, 0

    try:
        with open(path, "rb") as f:
            r = requests.post(
                f"{BACKEND}/api/paper/parse",
                files={"file": f},
                timeout=TIMEOUT_CONFIG["parse_timeout"]
            )
        r.raise_for_status()
        data = r.json()

        # Extract metadata
        title = data.get("title", "Untitled")
        authors = ", ".join(data.get("authors", [])) if data.get("authors") else "Unknown"
        pages = data.get("pages", 0)
        citations = data.get("citations_count", 0)

        return data.get("full_text", ""), data, title, authors, pages, citations
    except requests.exceptions.Timeout:
        return "", {"error": "请求超时，请稍后重试"}, "", "", 0, 0
    except requests.exceptions.RequestException as e:
        return "", {"error": f"网络错误：{str(e)}"}, "", "", 0, 0
    except Exception as e:
        return "", {"error": f"解析失败：{str(e)}"}, "", "", 0, 0

def call_summary(text, mode, model, language):
    r = requests.post(f"{BACKEND}/api/paper/summary", json={"text": text, "mode": mode, "model": model, "language": language})
    r.raise_for_status()
    d = r.json()
    return d["one_liner"], d["detailed"], d["mermaid"]

def call_profile(text, domain):
    r = requests.post(f"{BACKEND}/api/write/profile", json={"text": text, "domain": domain})
    r.raise_for_status()
    d = r.json()
    return d["lexical"], d["structural"], "\n".join(d["diagnostics"])


def call_profile_formatted(text, domain, lang="en"):
    """包装call_profile，返回格式化后的卡片式UI"""
    r = requests.post(f"{BACKEND}/api/write/profile", json={"text": text, "domain": domain})
    r.raise_for_status()
    d = r.json()

    lexical = d["lexical"]
    structural = d["structural"]
    diagnostics = d["diagnostics"]

    # 格式化lexical和structural为卡片式展示
    lexical_formatted = format_lexical_metrics(lexical, lang)
    structural_formatted = format_structural_metrics(structural, lang)

    # 合并所有卡片
    combined = lexical_formatted + "\n\n" + structural_formatted

    # 诊断建议
    diagnostics_html = ""
    if diagnostics:
        diag_title = "### Suggestions" if lang == "en" else "### 改进建议"
        diag_items = "\n".join([f"- {d}" for d in diagnostics])
        diagnostics_html = f"\n\n{diag_title}\n\n{diag_items}"

    return lexical, structural, combined + diagnostics_html


def format_lexical_metrics(lexical_data, lang="en"):
    """解析lexical指标，生成卡片式Markdown展示"""
    # 指标名称映射
    names = {
        "en": {
            "formality_score": "Formality Score",
            "sentence_complexity": "Sentence Complexity",
            "domain_terms": "Domain Terms"
        },
        "zh": {
            "formality_score": "正式程度",
            "sentence_complexity": "句子复杂度",
            "domain_terms": "领域术语"
        }
    }
    t = names.get(lang, names["en"])

    # 获取各指标值
    formality = lexical_data.get("formality_score", 0)
    complexity = lexical_data.get("sentence_complexity", 0)
    domain_terms = lexical_data.get("domain_terms", [])

    # 生成进度条
    def progress_bar(value, length=10):
        filled = int(value * length)
        return "█" * filled + "░" * (length - filled)

    # 生成卡片
    cards = []

    # 正式程度卡片
    formality_level = "Casual" if formality < 0.4 else "Balanced" if formality < 0.7 else "Formal"
    formality_level_zh = "较为口语化" if formality < 0.4 else "较为平衡" if formality < 0.7 else "正式"
    level_text = formality_level_zh if lang == "zh" else formality_level
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">📝</span>
        <span class="metric-name">{t['formality_score']}</span>
    </div>
    <div class="metric-value">{progress_bar(formality)} {int(formality * 100)}%</div>
    <div class="metric-desc">{level_text}</div>
</div>
""")

    # 句子复杂度卡片
    complexity_level = "Simple" if complexity < 0.4 else "Moderate" if complexity < 0.7 else "Complex"
    complexity_level_zh = "简单句较多" if complexity < 0.4 else "中等复杂度" if complexity < 0.7 else "复杂句式多"
    level_text = complexity_level_zh if lang == "zh" else complexity_level
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">🔤</span>
        <span class="metric-name">{t['sentence_complexity']}</span>
    </div>
    <div class="metric-value">{progress_bar(complexity)} {int(complexity * 100)}%</div>
    <div class="metric-desc">{level_text}</div>
</div>
""")

    # 领域术语卡片
    terms_display = ", ".join(domain_terms[:5]) if domain_terms else "N/A"
    terms_display_zh = "无检测到领域术语" if not domain_terms else ", ".join(domain_terms[:5])
    display_text = terms_display_zh if lang == "zh" else terms_display
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">🧠</span>
        <span class="metric-name">{t['domain_terms']}</span>
    </div>
    <div class="metric-value-full">{display_text}</div>
</div>
""")

    # 返回标题和卡片容器
    title = "### Lexical Analysis" if lang == "en" else "### 词汇分析"
    return title + "\n\n" + "\n".join(cards)


def format_structural_metrics(structural_data, lang="en"):
    """解析structural指标，生成卡片式Markdown展示"""
    # 指标名称映射
    names = {
        "en": {
            "passive_ratio": "Passive Voice Ratio",
            "transition_words": "Transition Words",
            "paragraph_structure": "Paragraph Structure"
        },
        "zh": {
            "passive_ratio": "被动语态比例",
            "transition_words": "过渡词使用",
            "paragraph_structure": "段落结构"
        }
    }
    t = names.get(lang, names["en"])

    # 获取各指标值
    passive = structural_data.get("passive_ratio", 0)
    transitions = structural_data.get("transition_words", 0)
    structure = structural_data.get("paragraph_structure", "N/A")

    # 生成进度条
    def progress_bar(value, length=10):
        filled = int(value * length)
        return "█" * filled + "░" * (length - filled)

    cards = []

    # 被动语态比例卡片
    passive_level = "Low" if passive < 0.3 else "Moderate" if passive < 0.6 else "High"
    passive_level_zh = "较低" if passive < 0.3 else "适中" if passive < 0.6 else "较高"
    level_text = passive_level_zh if lang == "zh" else passive_level
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">📊</span>
        <span class="metric-name">{t['passive_ratio']}</span>
    </div>
    <div class="metric-value">{progress_bar(passive)} {int(passive * 100)}%</div>
    <div class="metric-desc">{level_text}</div>
</div>
""")

    # 过渡词卡片
    transition_level = "Few" if transitions < 1 else "Adequate" if transitions < 3 else "Good"
    transition_level_zh = "较少" if transitions < 1 else "适中" if transitions < 3 else "丰富"
    level_text = transition_level_zh if lang == "zh" else transition_level
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">🔄</span>
        <span class="metric-name">{t['transition_words']}</span>
    </div>
    <div class="metric-value">{transitions} {level_text}</div>
</div>
""")

    # 段落结构卡片
    structure_zh = {
        "IMRaD": "标准学术结构 (IMRaD)",
        "Abstract": "摘要式结构",
        "List": "清单式结构",
        "N/A": "未检测到"
    }
    structure_display = structure_zh.get(structure, structure) if lang == "zh" else structure
    cards.append(f"""
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">📋</span>
        <span class="metric-name">{t['paragraph_structure']}</span>
    </div>
    <div class="metric-value-full">{structure_display}</div>
</div>
""")

    # 返回标题和卡片容器
    title = "### Structural Analysis" if lang == "en" else "### 结构分析"
    return title + "\n\n" + "\n".join(cards)

def call_transfer(text, journal, formality, domain, model):
    r = requests.post(
        f"{BACKEND}/api/write/transfer",
        json={"text": text, "target_journal": journal, "formality": formality, "domain": domain, "model": model},
    )
    r.raise_for_status()
    d = r.json()
    return d["rewritten"], "\n".join(d["suggestions"])


# ============== 流式处理函数 ==============
def call_summary_stream(text, mode, model, language):
    """
    流式调用摘要生成API
    使用 Gradio 生成器实现真正的流式输出
    """
    if not text or not text.strip():
        yield "❌ 错误：请先上传并解析PDF文件", "等待文件上传...", ""
        return

    one_liner_text = ""
    detailed_text = ""
    mermaid_text = ""

    try:
        # 显示初始加载状态
        yield "⏳ 正在生成摘要...", "⏳ 正在处理中，请稍候...", ""

        with requests.post(
            f"{BACKEND}/api/paper/summary/stream",
            json={"text": text, "mode": mode, "model": model, "language": language},
            stream=True,
            timeout=120
        ) as r:
            r.raise_for_status()

            for line in r.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        import json
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'content':
                                section = data.get('section', '')
                                content = data.get('content', '')
                                if section == 'one_liner':
                                    one_liner_text += content
                                elif section == 'detailed':
                                    detailed_text += content
                                elif section == 'mermaid':
                                    mermaid_text += content
                                # 使用 yield 实现真正的流式输出
                                yield one_liner_text, detailed_text, mermaid_text
                            elif data.get('type') == 'done':
                                break
                        except json.JSONDecodeError:
                            continue
    except requests.exceptions.Timeout:
        yield f"❌ 请求超时：处理时间过长，请尝试使用'快速速览'模式", detailed_text or "请求超时", mermaid_text
    except requests.exceptions.ConnectionError:
        yield f"❌ 连接错误：无法连接到后端服务，请检查服务是否正常运行", "连接失败", ""
    except requests.exceptions.HTTPError as e:
        yield f"❌ 服务器错误 ({e.response.status_code})：{e.response.text[:200]}", "处理失败", ""
    except Exception as e:
        yield f"❌ 未知错误：{str(e)}", "处理失败", ""


def call_transfer_stream(text, journal, formality, domain, model):
    """
    流式调用润色改写API
    使用 Gradio 生成器实现真正的流式输出
    """
    if not text or not text.strip():
        yield "❌ 错误：请先输入要润色的文本", "请输入文本内容"
        return

    rewritten_text = ""
    suggestions_text = ""

    try:
        # 显示初始加载状态
        yield "⏳ 正在润色改写...", "⏳ 正在生成建议..."

        with requests.post(
            f"{BACKEND}/api/write/transfer/stream",
            json={"text": text, "target_journal": journal, "formality": formality, "domain": domain, "model": model},
            stream=True,
            timeout=120
        ) as r:
            r.raise_for_status()

            for line in r.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        import json
                        try:
                            data = json.loads(line[6:])
                            if data.get('type') == 'content':
                                section = data.get('section', '')
                                content = data.get('content', '')
                                if section == 'rewritten':
                                    rewritten_text += content
                                elif section == 'suggestions':
                                    suggestions_text += content
                                # 使用 yield 实现真正的流式输出
                                yield rewritten_text, suggestions_text
                            elif data.get('type') == 'done':
                                break
                        except json.JSONDecodeError:
                            continue
    except requests.exceptions.Timeout:
        yield f"❌ 请求超时：处理时间过长，请稍后重试", suggestions_text or "请求超时"
    except requests.exceptions.ConnectionError:
        yield f"❌ 连接错误：无法连接到后端服务", "连接失败"
    except requests.exceptions.HTTPError as e:
        yield f"❌ 服务器错误 ({e.response.status_code})：{e.response.text[:200]}", "处理失败"
    except Exception as e:
        yield f"❌ 未知错误：{str(e)}", "处理失败"


@retry_on_error(max_retries=2, delay=1.0)
def get_models():
    """Fetch available models from backend with retry logic"""
    # 默认模型列表（作为fallback）
    default_models = [
        ("qwen2.5-7b-instruct (Default)", "qwen2.5-7b-instruct"),
        ("qwen2.5-14b-instruct", "qwen2.5-14b-instruct"),
        ("qwen2.5-72b-instruct", "qwen2.5-72b-instruct"),
        ("deepseek-r1", "deepseek-r1"),
        ("deepseek-v3", "deepseek-v3"),
    ]

    try:
        r = requests.get(
            f"{BACKEND}/api/models",
            timeout=TIMEOUT_CONFIG["model_fetch_timeout"]
        )
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                # 将后端返回的模型转换为 (name, id) 元组列表
                model_choices = [(m.get("name", m.get("id")), m.get("id")) for m in data]
                # 如果列表不为空，使用第一个模型作为默认值
                if model_choices:
                    return gr.update(choices=model_choices, value=model_choices[0][1])
    except Exception as e:
        print(f"⚠️ 获取模型列表失败: {e}，使用默认列表")

    # 返回默认模型列表和第一个作为默认值
    return gr.update(choices=default_models, value=default_models[0][1])


# ============== Export Handlers ==============
def export_markdown_handler(one_liner, detailed, mermaid, citation_style):
    """Export summary as Markdown"""
    try:
        content = f"## Core Insight\n\n{one_liner}\n\n## Detailed Summary\n\n{detailed}\n\n## Knowledge Graph\n\n```mermaid\n{mermaid}\n```"

        markdown = ExportManager.export_to_markdown(
            title="Paper Analysis Report",
            content=content,
            metadata={"source": "ResearchPal AI"}
        )

        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = ExportManager.save_export(markdown, filename, "md")

        return f"✅ Exported to: {filepath}"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def export_docx_handler(one_liner, detailed, citation_style):
    """Export summary as Word document"""
    try:
        content = f"{one_liner}\n\n{detailed}"

        docx_bytes = ExportManager.export_to_docx(
            title="Paper Analysis Report",
            content=content,
            metadata={"source": "ResearchPal AI"}
        )

        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = ExportManager.save_export(docx_bytes, filename, "docx")

        return f"✅ Exported to: {filepath}"
    except ImportError:
        return "❌ python-docx not installed. Install with: pip install python-docx"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


def export_bib_handler(citation_style):
    """Export citation as BibTeX"""
    try:
        # Placeholder - would need actual paper metadata
        bib_content = f"""@article{{placeholder,
  title={{Paper Title}},
  author={{Author Name}},
  journal={{Journal Name}},
  year={{2024}},
  note={{Citation format: {citation_style}}}
}}"""

        filename = f"citation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib"
        filepath = ExportManager.save_export(bib_content, filename, "bib")

        return f"✅ Exported to: {filepath}"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"


# ============== History Management ==============
def add_to_history(history, filename, summary_preview):
    """Add analysis to history"""
    from datetime import datetime

    history_item = {
        "filename": filename or "Untitled",
        "preview": summary_preview[:100] + "..." if len(summary_preview) > 100 else summary_preview,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Keep only last 10 items
    history = [history_item] + history[:9]
    return history


def render_history(history):
    """Render history as HTML"""
    if not history:
        return "<p style='text-align: center; color: var(--neutral-500);'>No history yet</p>"

    html = "<div class='history-list'>"
    for item in history:
        html += f"""
        <div class='history-item'>
            <div class='history-item-title'>{item['filename']}</div>
            <div class='history-item-preview'>{item['preview']}</div>
            <div class='history-item-time'>{item['timestamp']}</div>
        </div>
        """
    html += "</div>"
    return html


def clear_history():
    """Clear all history"""
    return []


# ============== Quick Actions ==============
def copy_all_results(one_liner, detailed, mermaid):
    """Copy all results to clipboard"""
    content = f"Core Insight:\n{one_liner}\n\nDetailed Summary:\n{detailed}\n\nKnowledge Graph:\n{mermaid}"
    return content


def save_results(one_liner, detailed, mermaid):
    """Save results to file"""
    try:
        content = f"Core Insight:\n{one_liner}\n\nDetailed Summary:\n{detailed}\n\nKnowledge Graph:\n{mermaid}"
        filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        import os
        os.makedirs("exports", exist_ok=True)
        filepath = os.path.join("exports", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ Saved to: {filepath}"
    except Exception as e:
        return f"❌ Save failed: {str(e)}"


# Custom CSS - combining external styles with app-specific overrides
custom_css = external_css + """
/* App-specific CSS overrides */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

body {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;
}

.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Header - Compact navigation bar */
.header-container {
    text-align: left;
    margin-bottom: 0 !important;
    margin-top: 0;
    padding-bottom: 8px;
    padding-top: 8px;
    border-bottom: 1px solid var(--border-color-primary);
    align-items: center !important;
    min-height: 50px !important;
    gap: 0 !important;
}

.header-container + .gr-tabs {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

.tabs {
    margin-top: 0 !important;
}

.header-container > .row {
    gap: 0.5rem !important;
    align-items: center !important;
    flex-wrap: nowrap !important;
    overflow: visible !important;
}

.logo-text {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 1.2rem !important;
    letter-spacing: -1px;
    color: #171717;
}

.dark .logo-text {
    color: #f5f5f5;
}

#subtitle {
    font-size: 0.7rem !important;
}

/* Tab styles */
.tabs {
    border: none !important;
    gap: 0.5rem;
}

.tab-nav {
    border: 1px solid var(--border-color-primary) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    background: var(--background-fill-secondary);
}

button.selected {
    background: var(--background-fill-primary) !important;
    border: 1px solid var(--border-color-primary) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Panel container */
.panel-container {
    border: 1px solid var(--border-color-primary);
    border-radius: 16px;
    padding: 0.75rem;
    background: var(--background-fill-primary);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}

/* Button styles */
button.primary {
    background: var(--neutral-900) !important;
    color: white !important;
    border: 1px solid var(--neutral-900) !important;
    transition: all 0.2s;
}

.dark button.primary {
    background: var(--neutral-50) !important;
    color: black !important;
    border: 1px solid var(--neutral-50) !important;
}

button.primary:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* Input fields */
textarea, input {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
}

/* Theme toggle button */
#theme-toggle {
    padding: 4px 10px !important;
    min-width: 50px !important;
    height: 64px !important;
    min-height: 64px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    background: #171717 !important;
    border: 1px solid #171717 !important;
}

.dark #theme-toggle {
    background: #ffffff !important;
    border: 1px solid #ffffff !important;
}

/* Header settings unified styles */
.header-settings .gradio-dropdown,
.header-settings .gradio-radio,
.header-settings .gradio-button {
    border-radius: 8px !important;
    border: 1px solid var(--border-color-primary) !important;
    background: var(--background-fill-secondary) !important;
    height: 32px !important;
    min-height: 32px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.header-settings .gradio-dropdown > div,
.header-settings .gradio-dropdown .wrap,
.header-settings .gradio-dropdown form {
    height: 30px !important;
    min-height: 30px !important;
}

.header-settings .gradio-radio {
    padding: 4px 8px !important;
    gap: 4px !important;
}

.header-settings .gradio-dropdown button {
    border-radius: 8px !important;
    height: 30px !important;
    min-height: 30px !important;
    padding: 2px 8px !important;
}

.header-settings .gradio-dropdown {
    height: 28px !important;
}

.header-settings .gradio-dropdown button.trigger,
.header-settings .gradio-dropdown .secondary {
    height: 28px !important;
    min-height: 28px !important;
    line-height: 20px !important;
}

.header-settings .gradio-dropdown input,
.header-settings .gradio-dropdown span {
    height: 28px !important;
    min-height: 28px !important;
    line-height: 20px !important;
}

.header-settings .gradio-dropdown > label,
.header-settings .gradio-dropdown .gp-label {
    display: none !important;
}

.header-settings .gradio-dropdown .wrap .border {
    height: 28px !important;
    min-height: 28px !important;
}

.header-settings .gradio-radio button {
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 4px 8px !important;
}

#lang-toggle, #theme-toggle {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 4px 10px !important;
    min-width: 50px !important;
    height: 64px !important;
    min-height: 64px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

/* Hide footer */
footer { display: none !important; }

/* History sidebar */
.history-sidebar {
    position: fixed;
    right: -320px;
    top: 80px;
    width: 300px;
    height: calc(100vh - 100px);
    background: var(--background-fill-primary);
    border: 1px solid var(--border-color-primary);
    border-radius: 12px 0 0 12px;
    padding: 1rem;
    transition: right 0.3s ease;
    z-index: 100;
    overflow-y: auto;
    box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
}

.history-sidebar.visible {
    right: 0;
}

.history-item {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: var(--background-fill-secondary);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.history-item:hover {
    transform: translateX(-4px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item-title {
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
    color: var(--text-primary);
}

.history-item-preview {
    font-size: 0.8rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.history-item-time {
    font-size: 0.75rem;
    color: var(--neutral-500);
    margin-top: 0.25rem;
}

/* Quick actions bar */
.quick-actions-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    padding: 0.5rem;
    background: var(--background-fill-secondary);
    border-radius: 8px;
}

.quick-actions-bar button {
    flex: 1;
    font-size: 0.85rem !important;
    padding: 0.5rem !important;
}

/* Metric cards for style diagnostics */
.metric-card {
    background: var(--background-fill-secondary);
    border: 1px solid var(--border-color-primary);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
}

.metric-card:hover {
    border-color: var(--neutral-400);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.dark .metric-card {
    background: var(--background-fill-primary);
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.metric-icon {
    font-size: 1.2rem;
}

.metric-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--neutral-700);
}

.dark .metric-name {
    color: var(--neutral-300);
}

.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1rem;
    font-weight: 500;
    margin-bottom: 4px;
    letter-spacing: 1px;
}

.metric-value-full {
    font-size: 0.9rem;
    color: var(--neutral-600);
    word-break: break-word;
}

.dark .metric-value-full {
    color: var(--neutral-400);
}

.metric-desc {
    font-size: 0.85rem;
    color: var(--neutral-500);
    font-style: italic;
}
"""

# 黑白极简主题配置
theme = gr.themes.Monochrome(
    primary_hue="neutral",
    radius_size=gr.themes.sizes.radius_lg,
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "ui-sans-serif", "system-ui", "sans-serif"],
).set(
    body_background_fill="var(--neutral-50)",
    body_background_fill_dark="#0a0a0a",
    block_background_fill="white",
    block_background_fill_dark="#171717",
    block_border_width="1px",
    block_shadow="none",
    button_primary_background_fill="var(--neutral-900)",
    button_primary_background_fill_dark="var(--neutral-50)",
    button_primary_text_color="white",
    button_primary_text_color_dark="black",
)

# 国际化配置
i18n = {
    "en": {
        "title": "ResearchPal AI",
        "subtitle": "Research Intelligence Suite v2.0",
        "tab_parse": "PAPER ANALYSIS",
        "tab_write": "WRITING ASSISTANT",
        "source_doc": "### SOURCE DOCUMENT",
        "upload_label": "Upload PDF",
        "config_title": "### PROCESSING CONFIG",
        "mode_label": "Analysis Depth",
        "mode_info": "Select processing granularity",
        "modes": [("MVP Demo", "mvp"), ("Quick Scan", "fast"), ("Deep Read", "deep")],
        "summary_btn": "GENERATE INTELLIGENCE",
        "report_title": "### INTELLIGENCE REPORT",
        "exec_summary": "EXECUTIVE SUMMARY",
        "core_insight": "Core Insight",
        "detailed_summary": "Detailed Summary",
        "knowledge_graph": "KNOWLEDGE GRAPH",
        "graph_desc": "Mermaid Relationship Graph",
        "graph_code": "Graph Code",
        "raw_data": "RAW DATA",
        "full_text": "Full Text",
        "parsed_content": "Parsed Content",
        "json_struct": "JSON Structure",
        "struct_data": "Structured Data",
        "draft_input": "### DRAFT INPUT",
        "content_label": "Content",
        "content_ph": "Paste your draft here...",
        "target_params": "### TARGET PARAMETERS",
        "domain_label": "Domain",
        "domains": [("Computer Science", "cs"), ("Biology", "bio"), ("Medicine", "med")],
        "venue_label": "Target Venue",
        "formality_label": "Formality Level",
        "analyze_btn": "ANALYZE STYLE",
        "enhance_btn": "ENHANCE WRITING",
        "enhance_output": "### ENHANCEMENT OUTPUT",
        "revised_ver": "REVISED VERSION",
        "polished_text": "Polished Text",
        "enhance_notes": "Enhancement Notes",
        "style_metrics": "STYLE METRICS",
        "diag_report": "Diagnostic Report",
        "lexical": "Lexical Analysis",
        "structural": "Structural Analysis",
        "processing": "Processing...",
        "waiting": "Waiting for analysis..."
    },
    "zh": {
        "title": "ResearchPal AI",
        "subtitle": "科研智能辅助套件 v2.0",
        "tab_parse": "论文深度解析",
        "tab_write": "学术写作助手",
        "source_doc": "### 源文档",
        "upload_label": "上传 PDF 文件",
        "config_title": "### 处理配置",
        "mode_label": "解析深度",
        "mode_info": "选择处理粒度",
        "modes": [("MVP 演示", "mvp"), ("快速速览", "fast"), ("深度研读", "deep")],
        "summary_btn": "生成智能摘要",
        "report_title": "### 智能分析报告",
        "exec_summary": "核心摘要",
        "core_insight": "核心洞察",
        "detailed_summary": "详细摘要",
        "knowledge_graph": "知识图谱",
        "graph_desc": "Mermaid 关系图谱",
        "graph_code": "图谱代码",
        "raw_data": "原始数据",
        "full_text": "全文内容",
        "parsed_content": "解析内容",
        "json_struct": "JSON 结构",
        "struct_data": "结构化数据",
        "draft_input": "### 草稿输入",
        "content_label": "正文内容",
        "content_ph": "在此粘贴您的论文草稿...",
        "target_params": "### 目标参数",
        "domain_label": "学科领域",
        "domains": [("计算机科学", "cs"), ("生物学", "bio"), ("医学", "med")],
        "venue_label": "目标期刊/会议",
        "formality_label": "正式程度",
        "analyze_btn": "风格诊断",
        "enhance_btn": "润色改写",
        "enhance_output": "### 优化结果",
        "revised_ver": "修订版本",
        "polished_text": "润色后文本",
        "enhance_notes": "修改建议",
        "style_metrics": "风格指标",
        "diag_report": "诊断报告",
        "lexical": "词汇分析",
        "structural": "结构分析",
        "processing": "正在处理中...",
        "waiting": "等待分析..."
    }
}

# 语言切换逻辑
def get_i18n(lang):
    return i18n[lang]

# 注入 JS 实现深色模式切换和语言切换
js_func = """
() => {
    // 语言切换辅助（可选）
}
"""

def toggle_theme():
    """切换深色模式的 JS，同时切换图标并保存到localStorage"""
    return """() => {
        const body = document.body;
        const btn = document.getElementById('theme-toggle');
        body.classList.toggle('dark');
        const isDark = body.classList.contains('dark');

        if (isDark) {
            btn.innerHTML = '☀️';
            localStorage.setItem('researchpal_theme', 'dark');
        } else {
            btn.innerHTML = '🌙';
            localStorage.setItem('researchpal_theme', 'light');
        }
    }"""

def toggle_lang():
    """切换语言的 JS，同时切换按钮文字并保存到localStorage"""
    return """() => {
        const btn = document.getElementById('lang-toggle');
        const currentLang = btn.innerHTML;
        let newLang;

        if (currentLang === 'EN') {
            btn.innerHTML = '中文';
            newLang = 'zh';
        } else {
            btn.innerHTML = 'EN';
            newLang = 'en';
        }

        localStorage.setItem('researchpal_lang', newLang);
        return newLang;
    }"""

with gr.Blocks(title="ResearchPal AI", theme=theme, css=custom_css) as demo:
    # 状态变量
    lang_state = gr.State("en")
    history_state = gr.State([])

    # Inject keyboard shortcuts handler
    keyboard_handler = get_keyboard_shortcuts()
    keyboard_js = gr.HTML(visible=False, elem_classes=["keyboard-handler"])

    with gr.Row(elem_classes="header-container"):
        with gr.Column(scale=1):
            gr.HTML("""
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 32px; height: 32px; background: currentColor; border-radius: 8px;"></div>
                    <div>
                        <div class="logo-text">ResearchPal / AI</div>
                        <div id="subtitle" style="font-size: 0.9rem; opacity: 0.6; margin-top: -0px;">Research Intelligence Suite v2.0</div>
                    </div>
                </div>
            """)
        with gr.Column(scale=3):
            with gr.Row(equal_height=True, variant="compact", elem_classes="header-settings"):
                model_select = gr.Dropdown(choices=[], label="Model", interactive=True, scale=10, min_width=500, show_label=False)
                history_toggle_btn = gr.Button("📜", variant="secondary", scale=1, min_width=32, elem_id="history-toggle", elem_classes=["history-btn"])
                lang_btn = gr.Button("EN", variant="secondary", scale=1, min_width=32, elem_id="lang-toggle")
                dark_btn = gr.Button("🌙", variant="secondary", scale=1, min_width=32, elem_id="theme-toggle")
                
    # 绑定深色模式切换事件
    dark_btn.click(None, None, None, js=toggle_theme())

    # 页面加载时获取模型列表和注入键盘快捷键
    def on_load():
        models = get_models()
        keyboard_script = keyboard_handler.generate_javascript_handler()

        # Add settings restoration and file validation script
        settings_script = """
        <script>
        // Restore settings from localStorage
        (function() {
            const settings = JSON.parse(localStorage.getItem('researchpal_settings') || '{}');

            // Restore theme
            const theme = localStorage.getItem('researchpal_theme');
            if (theme === 'dark') {
                document.body.classList.add('dark');
                const themeBtn = document.getElementById('theme-toggle');
                if (themeBtn) themeBtn.innerHTML = '☀️';
            }

            // Restore language
            const lang = localStorage.getItem('researchpal_lang');
            if (lang === 'zh') {
                const langBtn = document.getElementById('lang-toggle');
                if (langBtn) langBtn.innerHTML = '中文';
            }

            console.log('Settings restored:', { theme, lang });

            // Client-side file validation
            setTimeout(() => {
                const fileInputs = document.querySelectorAll('input[type="file"]');
                fileInputs.forEach(input => {
                    input.addEventListener('change', function(e) {
                        const file = e.target.files[0];
                        if (!file) return;

                        // Check file type
                        if (!file.name.toLowerCase().endsWith('.pdf')) {
                            alert('❌ Please upload a PDF file only');
                            e.target.value = '';
                            return;
                        }

                        // Check file size (50MB = 52428800 bytes)
                        if (file.size > 52428800) {
                            alert('❌ File size exceeds 50MB limit');
                            e.target.value = '';
                            return;
                        }

                        console.log('✅ File validation passed:', file.name, (file.size / 1024 / 1024).toFixed(2) + 'MB');
                    });
                });
            }, 1000);
        })();
        </script>
        """

        full_script = keyboard_script + settings_script
        return models, gr.update(value=full_script, visible=True)

    demo.load(on_load, outputs=[model_select, keyboard_js])

    with gr.Tabs() as tabs:
        # ==================== Tab 1: 论文深度解析 ====================
        with gr.TabItem("PAPER ANALYSIS", id="tab_parse") as t1:
            with gr.Row():
                # 左侧：上传与操作区
                with gr.Column(scale=1, min_width=280, elem_classes="panel-container"):
                    md_source = gr.Markdown("### SOURCE DOCUMENT")

                    # Example papers section
                    with gr.Accordion("📚 Example Papers", open=False):
                        gr.Markdown("Try these classic papers:")
                        example_transformer = gr.Button("🔥 Attention Is All You Need", size="sm")
                        example_bert = gr.Button("🔥 BERT: Pre-training", size="sm")
                        example_resnet = gr.Button("🔥 Deep Residual Learning", size="sm")

                    pdf_input = gr.File(
                        label="Upload PDF",
                        file_types=[".pdf"],
                        file_count="single",
                        height=80
                    )
                    
                    md_config = gr.Markdown("### PROCESSING CONFIG")
                    mode_select = gr.Radio(
                        choices=i18n["en"]["modes"],
                        value="fast",
                        label="Analysis Depth",
                        info="Select processing granularity"
                    )
                    summary_btn = gr.Button("GENERATE INTELLIGENCE", variant="primary", elem_id="summary-btn", elem_classes=["action-btn"])

                    # 隐藏的中间结果
                    parsed_text_hidden = gr.Textbox(visible=False)

                # 右侧：结果展示区
                with gr.Column(scale=4, elem_classes="panel-container"):
                    md_report = gr.Markdown("### INTELLIGENCE REPORT")

                    # Quick actions bar
                    with gr.Row(elem_classes=["quick-actions-bar"]):
                        copy_all_btn = gr.Button("📋 Copy All", size="sm", elem_classes=["quick-action"])
                        save_btn = gr.Button("💾 Save", size="sm", elem_classes=["quick-action"], elem_id="save-btn")
                        export_quick_btn = gr.Button("📥 Export", size="sm", elem_classes=["quick-action"], elem_id="export-btn")

                    with gr.Tabs():
                        with gr.TabItem("EXECUTIVE SUMMARY") as t1_sub1:
                            one_liner_output = gr.Textbox(
                                label="Core Insight",
                                placeholder="Processing...",
                                lines=5,
                                show_copy_button=True,
                                elem_id="core-insight"
                            )
                            detailed_output = gr.Markdown(
                                value="Waiting for analysis...",
                            )
                        
                        with gr.TabItem("KNOWLEDGE GRAPH") as t1_sub2:
                            md_graph = gr.Markdown("Mermaid Relationship Graph")
                            mermaid_output = gr.Code(
                                label="Graph Code",
                                language=None,
                                lines=25
                            )
                        
                        with gr.TabItem("METADATA") as t1_sub3:
                            metadata_title = gr.Textbox(label="Title", interactive=False, lines=2)
                            metadata_authors = gr.Textbox(label="Authors", interactive=False, lines=2)
                            with gr.Row():
                                metadata_pages = gr.Number(label="Pages", interactive=False)
                                metadata_citations = gr.Number(label="Citations", interactive=False)

                        with gr.TabItem("EXPORT") as t1_sub4:
                            citation_style = gr.Dropdown(
                                choices=["APA", "MLA", "IEEE", "Chicago", "GB/T 7714"],
                                value="APA",
                                label="Citation Format",
                                interactive=True
                            )
                            with gr.Row():
                                export_md_btn = gr.Button("📥 Export Markdown", variant="secondary")
                                export_docx_btn = gr.Button("📥 Export Word", variant="secondary")
                                export_bib_btn = gr.Button("📥 Export BibTeX", variant="secondary")
                            export_status = gr.Textbox(label="Export Status", interactive=False, lines=2)

                        with gr.TabItem("RAW DATA") as t1_sub5:
                            with gr.Accordion("Full Text", open=False) as acc1:
                                parsed_text_display = gr.Textbox(
                                    label="Parsed Content",
                                    lines=25,
                                    interactive=False,
                                    show_copy_button=True
                                )
                            with gr.Accordion("JSON Structure", open=False) as acc2:
                                raw_json_output = gr.JSON(label="Structured Data")

            # 绑定事件 - 上传文件自动解析
            pdf_input.change(
                call_parse,
                inputs=[pdf_input],
                outputs=[parsed_text_hidden, raw_json_output, metadata_title, metadata_authors, metadata_pages, metadata_citations]
            ).then(
                lambda x: x, inputs=[parsed_text_hidden], outputs=[parsed_text_display]
            )

            # Example paper handlers
            def load_example_paper(paper_name):
                """Load example paper text"""
                examples = {
                    "transformer": """Attention Is All You Need

Abstract: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature.""",

                    "bert": """BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

Abstract: We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.""",

                    "resnet": """Deep Residual Learning for Image Recognition

Abstract: Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth. On the ImageNet dataset we evaluate residual nets with a depth of up to 152 layers—8× deeper than VGG nets but still having lower complexity."""
                }
                return examples.get(paper_name, "")

            example_transformer.click(
                lambda: load_example_paper("transformer"),
                outputs=[parsed_text_hidden]
            )

            example_bert.click(
                lambda: load_example_paper("bert"),
                outputs=[parsed_text_hidden]
            )

            example_resnet.click(
                lambda: load_example_paper("resnet"),
                outputs=[parsed_text_hidden]
            )

            # Summary button with history tracking
            summary_btn.click(
                # 使用生成器函数实现真正的流式输出
                call_summary_stream,
                inputs=[parsed_text_hidden, mode_select, model_select, lang_state],
                outputs=[one_liner_output, detailed_output, mermaid_output]
            )

            # Quick actions
            copy_all_btn.click(
                copy_all_results,
                inputs=[one_liner_output, detailed_output, mermaid_output],
                outputs=None,
                js="""(one_liner, detailed, mermaid) => {
                    const content = `Core Insight:\\n${one_liner}\\n\\nDetailed Summary:\\n${detailed}\\n\\nKnowledge Graph:\\n${mermaid}`;
                    navigator.clipboard.writeText(content).then(() => {
                        alert('✅ Copied to clipboard!');
                    }).catch(err => {
                        console.error('Copy failed:', err);
                    });
                }"""
            )

            save_btn.click(
                save_results,
                inputs=[one_liner_output, detailed_output, mermaid_output],
                outputs=None,
                js="""(one_liner, detailed, mermaid) => {
                    alert('💾 Results saved!');
                }"""
            )

            # Export handlers
            export_md_btn.click(
                export_markdown_handler,
                inputs=[one_liner_output, detailed_output, mermaid_output, citation_style],
                outputs=[export_status]
            )

            export_docx_btn.click(
                export_docx_handler,
                inputs=[one_liner_output, detailed_output, citation_style],
                outputs=[export_status]
            )

            export_bib_btn.click(
                export_bib_handler,
                inputs=[citation_style],
                outputs=[export_status]
            )

        # ==================== Tab 2: 学术写作助手 ====================
        with gr.TabItem("WRITING ASSISTANT", id="tab_write") as t2:
            with gr.Row():
                # 左侧：输入与设置
                with gr.Column(scale=1, elem_classes="panel-container"):
                    md_draft = gr.Markdown("### DRAFT INPUT")
                    text_input = gr.Textbox(
                        label="Content",
                        placeholder="Paste your draft here...",
                        lines=10,
                        value="Our experiment shows that the method works well."
                    )
                    
                    md_params = gr.Markdown("### TARGET PARAMETERS")
                    with gr.Row():
                        domain_select = gr.Dropdown(
                            choices=i18n["en"]["domains"],
                            value="cs",
                            label="Domain"
                        )
                        journal_select = gr.Dropdown(
                            choices=["Nature", "Science", "ACL", "IEEE", "CVPR"],
                            value="Nature",
                            label="Target Venue",
                            allow_custom_value=True
                        )
                    formality_slider = gr.Slider(
                        minimum=0, maximum=1, value=0.85, step=0.05,
                        label="Formality Level"
                    )

                    with gr.Row():
                        analyze_btn = gr.Button("ANALYZE STYLE", size="lg", elem_id="analyze-btn")
                        transfer_btn = gr.Button("ENHANCE WRITING", variant="primary", size="lg", elem_id="enhance-btn")

                # 右侧：反馈与结果
                with gr.Column(scale=1, elem_classes="panel-container"):
                    md_enhance = gr.Markdown("### ENHANCEMENT OUTPUT")
                    
                    with gr.Tabs():
                        with gr.TabItem("REVISED VERSION") as t2_sub1:
                            rewritten_output = gr.Textbox(
                                label="Polished Text",
                                lines=12,
                                show_copy_button=True,
                                interactive=False
                            )
                            suggestions_output = gr.Markdown(
                                label="Enhancement Notes",
                                value=""
                            )
                        
                        with gr.TabItem("STYLE METRICS") as t2_sub2:
                            diagnostics_output = gr.Markdown(label="Diagnostic Report")
                            with gr.Row():
                                lexical_json = gr.JSON(label="Lexical Analysis")
                                structural_json = gr.JSON(label="Structural Analysis")

            # 绑定事件
            analyze_btn.click(
                call_profile_formatted,
                inputs=[text_input, domain_select, lang_state],
                outputs=[lexical_json, structural_json, diagnostics_output]
            )
            
            transfer_btn.click(
                # 使用生成器函数实现真正的流式输出
                call_transfer_stream,
                inputs=[text_input, journal_select, formality_slider, domain_select, model_select],
                outputs=[rewritten_output, suggestions_output]
            )

    # 语言切换事件处理
    def change_lang(lang):
        t = i18n[lang]
        return (
            # Tabs
            gr.update(label=t["tab_parse"]),
            gr.update(label=t["tab_write"]),
            # Tab 1 Content
            gr.update(value=t["source_doc"]),
            gr.update(label=t["upload_label"]),
            gr.update(value=t["config_title"]),
            gr.update(label=t["mode_label"], info=t["mode_info"], choices=t["modes"]),
            gr.update(value=t["summary_btn"]),
            gr.update(value=t["report_title"]),
            gr.update(label=t["exec_summary"]),
            gr.update(label=t["core_insight"], placeholder=t["processing"]),
            gr.update(value=t["waiting"]),
            gr.update(label=t["knowledge_graph"]),
            gr.update(value=t["graph_desc"]),
            gr.update(label=t["graph_code"]),
            gr.update(label="METADATA"),
            gr.update(label="EXPORT"),
            gr.update(label=t["raw_data"]),
            gr.update(label=t["full_text"]),
            gr.update(label=t["parsed_content"]),
            gr.update(label=t["json_struct"]),
            gr.update(label=t["struct_data"]),
            # Tab 2 Content
            gr.update(value=t["draft_input"]),
            gr.update(label=t["content_label"], placeholder=t["content_ph"]),
            gr.update(value=t["target_params"]),
            gr.update(label=t["domain_label"], choices=t["domains"]),
            gr.update(label=t["venue_label"]),
            gr.update(label=t["formality_label"]),
            gr.update(value=t["analyze_btn"]),
            gr.update(value=t["enhance_btn"]),
            gr.update(value=t["enhance_output"]),
            gr.update(label=t["revised_ver"]),
            gr.update(label=t["polished_text"]),
            gr.update(label=t["enhance_notes"]),
            gr.update(label=t["style_metrics"]),
            gr.update(label=t["diag_report"]),
            gr.update(label=t["lexical"]),
            gr.update(label=t["structural"]),
            # 返回新的语言值
            lang,
        )

    lang_btn.click(
        change_lang,
        inputs=[lang_btn],
        outputs=[
            t1, t2,
            md_source, pdf_input, md_config, mode_select, summary_btn,
            md_report, t1_sub1, one_liner_output, detailed_output, t1_sub2, md_graph, mermaid_output,
            t1_sub3, t1_sub4, t1_sub5, acc1, parsed_text_display, acc2, raw_json_output,
            md_draft, text_input, md_params, domain_select, journal_select, formality_slider,
            analyze_btn, transfer_btn, md_enhance, t2_sub1, rewritten_output, suggestions_output,
            t2_sub2, diagnostics_output, lexical_json, structural_json,
            lang_state
        ],
        js=toggle_lang()
    )

if __name__ == "__main__":
    print("启动 Gradio 服务中... 请稍候")
    print("如果不自动弹出浏览器，请手动访问: http://127.0.0.1:7860")
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)