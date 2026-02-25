from __future__ import annotations
import os
import time
import requests
import gradio as gr

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def call_parse(pdf_file):
    # 1) 没有上传文件
    if pdf_file is None:
        return "", {"error": "请先上传一个PDF文件再点击解析。"}

    # 2) Gradio File 可能返回：str 路径 / dict / 临时文件对象
    path = None
    if isinstance(pdf_file, str):
        path = pdf_file
    elif isinstance(pdf_file, dict):
        path = pdf_file.get("path") or pdf_file.get("name")
    else:
        path = getattr(pdf_file, "name", None)

    if not path:
        return "", {"error": f"无法识别上传文件对象：{type(pdf_file)}"}

    with open(path, "rb") as f:
        r = requests.post(f"{BACKEND}/api/paper/parse", files={"file": f})
    r.raise_for_status()
    data = r.json()
    return data.get("full_text", ""), data

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
    if not text:
        yield "", "请先解析PDF文件", ""
        return

    try:
        with requests.post(
            f"{BACKEND}/api/paper/summary/stream",
            json={"text": text, "mode": mode, "model": model, "language": language},
            stream=True,
            timeout=120
        ) as r:
            r.raise_for_status()

            one_liner_text = ""
            detailed_text = ""
            mermaid_text = ""

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
    except Exception as e:
        yield f"Error: {str(e)}", "", ""


def call_transfer_stream(text, journal, formality, domain, model):
    """
    流式调用润色改写API
    使用 Gradio 生成器实现真正的流式输出
    """
    if not text:
        yield "", "请先输入要润色的文本"
        return

    try:
        with requests.post(
            f"{BACKEND}/api/write/transfer/stream",
            json={"text": text, "target_journal": journal, "formality": formality, "domain": domain, "model": model},
            stream=True,
            timeout=120
        ) as r:
            r.raise_for_status()

            rewritten_text = ""
            suggestions_text = ""

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
    except Exception as e:
        yield f"Error: {str(e)}", ""


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
    
    # 添加重试逻辑，等待后端就绪
    max_retries = 5
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            r = requests.get(f"{BACKEND}/api/models", timeout=3)
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    # 将后端返回的模型转换为 (name, id) 元组列表
                    model_choices = [(m.get("name", m.get("id")), m.get("id")) for m in data]
                    # 如果列表不为空，使用第一个模型作为默认值
                    if model_choices:
                        # 返回 gr.update 对象，同时设置 choices 和 value
                        return gr.update(choices=model_choices, value=model_choices[0][1])
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Backend not ready (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to fetch models after {max_retries} attempts: {e}")
        except Exception as e:
            print(f"Unexpected error fetching models: {e}")
            break
    
    # 返回默认模型列表和第一个作为默认值
    return gr.update(choices=default_models, value=default_models[0][1])

# 自定义CSS
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

body {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;
}

.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto;
}

/* 标题区域 */
.header-container {
    text-align: left;
    margin-bottom: 0.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color-primary);
    align-items: center !important;
}
.header-container > .row {
    gap: 0.5rem !important;
    align-items: center !important;
}
.logo-text {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 2rem;
    letter-spacing: -1px;
    /* 浅色模式下：使用深色文字 */
    color: #171717;
}
.dark .logo-text {
    /* 深色模式下：使用浅色文字 */
    color: #f5f5f5;
}

/* Tab 样式 */
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

/* 卡片式容器 */
.panel-container {
    border: 1px solid var(--border-color-primary);
    border-radius: 16px;
    padding: 1.5rem;
    background: var(--background-fill-primary);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
}

/* 按钮样式 */
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

/* 输入框 */
textarea, input {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
}

/* 主题按钮样式 - 基础样式 */
#theme-toggle {
    font-size: 1.2rem !important;
    padding: 8px 12px !important;
    min-width: 44px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

/* 浅色模式下：深色背景 + 月亮图标 */
#theme-toggle {
    background: #171717 !important;
    border: 1px solid #171717 !important;
}

/* 深色模式下：白色背景 + 太阳图标 */
.dark #theme-toggle {
    background: #ffffff !important;
    border: 1px solid #ffffff !important;
}

/* 统一设置区域按钮样式 */
.header-settings .gradio-dropdown,
.header-settings .gradio-radio,
.header-settings .gradio-button {
    border-radius: 8px !important;
    border: 1px solid var(--border-color-primary) !important;
    background: var(--background-fill-secondary) !important;
}

.header-settings .gradio-radio {
    padding: 4px 8px !important;
    gap: 4px !important;
}

.header-settings .gradio-dropdown button {
    border-radius: 8px !important;
}

.header-settings .gradio-radio button {
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 4px 8px !important;
}

/* 语言切换按钮样式 */
#lang-toggle {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 6px 12px !important;
    min-width: 50px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

/* 隐藏footer */
footer { display: none !important; }

/* 简单响应式适配 - 平板 */
@media (max-width: 1024px) {
    .header-container .row {
        flex-wrap: wrap !important;
    }
}

/* 简单响应式适配 - 小屏幕手机 */
@media (max-width: 768px) {
    .gradio-container {
        max-width: 100% !important;
        padding: 0.5rem !important;
    }
    .header-container {
        flex-direction: column !important;
        gap: 1rem !important;
    }
    .header-container .column {
        width: 100% !important;
    }
    .panel-container {
        padding: 1rem !important;
    }
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
        "parse_btn": "INITIALIZE PARSING",
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
        "parse_btn": "开始解析",
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
    """切换深色模式的 JS，同时切换图标"""
    return """() => {
        const body = document.body;
        const btn = document.getElementById('theme-toggle');
        body.classList.toggle('dark');
        if (body.classList.contains('dark')) {
            btn.innerHTML = '☀️';
        } else {
            btn.innerHTML = '🌙';
        }
    }"""

def toggle_lang():
    """切换语言的 JS，同时切换按钮文字"""
    return """() => {
        const btn = document.getElementById('lang-toggle');
        const currentLang = btn.innerHTML;
        if (currentLang === 'EN') {
            btn.innerHTML = '中文';
            return 'zh';
        } else {
            btn.innerHTML = 'EN';
            return 'en';
        }
    }"""

with gr.Blocks(title="ResearchPal AI", theme=theme, css=custom_css) as demo:
    # 状态变量
    lang_state = gr.State("en")

    with gr.Row(elem_classes="header-container"):
        with gr.Column(scale=4):
            gr.HTML("""
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 32px; height: 32px; background: currentColor; border-radius: 8px;"></div>
                    <div>
                        <div class="logo-text">ResearchPal / AI</div>
                        <div id="subtitle" style="font-size: 0.9rem; opacity: 0.6; margin-top: -4px;">Research Intelligence Suite v2.0</div>
                    </div>
                </div>
            """)
        with gr.Column(scale=2):
            with gr.Row(equal_height=True, variant="compact", elem_classes="header-settings"):
                model_select = gr.Dropdown(choices=[], label="Model", interactive=True, scale=3, min_width=220)
                lang_btn = gr.Button("EN", variant="secondary", scale=1, min_width=50, elem_id="lang-toggle")
                dark_btn = gr.Button("🌙", variant="secondary", scale=1, min_width=44, elem_id="theme-toggle")
                
    # 绑定深色模式切换事件
    dark_btn.click(None, None, None, js=toggle_theme())
    
    # 页面加载时获取模型列表
    demo.load(get_models, outputs=[model_select])

    with gr.Tabs() as tabs:
        # ==================== Tab 1: 论文深度解析 ====================
        with gr.TabItem("PAPER ANALYSIS", id="tab_parse") as t1:
            with gr.Row():
                # 左侧：上传与操作区
                with gr.Column(scale=1, elem_classes="panel-container"):
                    md_source = gr.Markdown("### SOURCE DOCUMENT")
                    pdf_input = gr.File(
                        label="Upload PDF",
                        file_types=[".pdf"],
                        file_count="single",
                        height=120
                    )
                    
                    with gr.Row():
                        parse_btn = gr.Button("INITIALIZE PARSING", variant="primary", scale=1)
                    
                    md_config = gr.Markdown("### PROCESSING CONFIG")
                    mode_select = gr.Radio(
                        choices=i18n["en"]["modes"],
                        value="mvp",
                        label="Analysis Depth",
                        info="Select processing granularity"
                    )
                    summary_btn = gr.Button("GENERATE INTELLIGENCE", variant="primary")

                    # 隐藏的中间结果
                    parsed_text_hidden = gr.Textbox(visible=False)

                # 右侧：结果展示区
                with gr.Column(scale=2, elem_classes="panel-container"):
                    md_report = gr.Markdown("### INTELLIGENCE REPORT")
                    
                    with gr.Tabs():
                        with gr.TabItem("EXECUTIVE SUMMARY") as t1_sub1:
                            one_liner_output = gr.Textbox(
                                label="Core Insight",
                                placeholder="Processing...",
                                lines=2,
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
                                lines=15
                            )
                        
                        with gr.TabItem("RAW DATA") as t1_sub3:
                            with gr.Accordion("Full Text", open=False) as acc1:
                                parsed_text_display = gr.Textbox(
                                    label="Parsed Content",
                                    lines=10,
                                    interactive=False,
                                    show_copy_button=True
                                )
                            with gr.Accordion("JSON Structure", open=False) as acc2:
                                raw_json_output = gr.JSON(label="Structured Data")

            # 绑定事件 - 上传文件自动解析
            pdf_input.change(
                call_parse,
                inputs=[pdf_input],
                outputs=[parsed_text_hidden, raw_json_output]
            ).then(
                lambda x: x, inputs=[parsed_text_hidden], outputs=[parsed_text_display]
            )

            # 保留手动解析按钮作为备用
            parse_btn.click(
                call_parse,
                inputs=[pdf_input],
                outputs=[parsed_text_hidden, raw_json_output]
            ).then(
                lambda x: x, inputs=[parsed_text_hidden], outputs=[parsed_text_display]
            )

            summary_btn.click(
                # 使用生成器函数实现真正的流式输出
                call_summary_stream,
                inputs=[parsed_text_hidden, mode_select, model_select, lang_state],
                outputs=[one_liner_output, detailed_output, mermaid_output]
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
                        analyze_btn = gr.Button("ANALYZE STYLE", size="lg")
                        transfer_btn = gr.Button("ENHANCE WRITING", variant="primary", size="lg")

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
                call_profile,
                inputs=[text_input, domain_select],
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
            gr.update(value=t["parse_btn"]),
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
            md_source, pdf_input, parse_btn, md_config, mode_select, summary_btn,
            md_report, t1_sub1, one_liner_output, detailed_output, t1_sub2, md_graph, mermaid_output,
            t1_sub3, acc1, parsed_text_display, acc2, raw_json_output,
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