"""
Gradio UI Components for ResearchPal
Professional academic UI with modern interactions
"""
import gradio as gr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UIComponents:
    """Reusable UI component library for ResearchPal"""

    @staticmethod
    def create_upload_zone():
        """Create enhanced drag-drop upload zone with visual feedback"""
        return gr.File(
            label="📄 上传PDF论文",
            file_types=[".pdf"],
            type="filepath",
            elem_classes=["upload-zone"]
        )

    @staticmethod
    def create_progress_indicator():
        """Create animated progress indicator with time estimate"""
        return gr.HTML(
            value='<div class="progress-container"><div class="progress-spinner"></div><span>处理中...</span></div>',
            visible=False,
            elem_classes=["progress-wrapper"]
        )

    @staticmethod
    def create_result_card(title: str, content: str, copy_button: bool = True):
        """Create collapsible result card with copy functionality"""
        with gr.Column():
            with gr.Row():
                title_html = gr.HTML(f'<h3 class="card-title">{title}</h3>')
                if copy_button:
                    copy_btn = gr.Button("📋 复制", size="sm", elem_classes=["copy-btn"])

            content_box = gr.Textbox(
                value=content,
                lines=10,
                max_lines=20,
                show_label=False,
                interactive=False,
                elem_classes=["result-content"]
            )

            if copy_button:
                return title_html, content_box, copy_btn
            return title_html, content_box

    @staticmethod
    def create_history_sidebar():
        """Create history panel showing recent analyses"""
        return gr.Column(
            elem_classes=["history-sidebar"],
            visible=False
        )

    @staticmethod
    def create_settings_panel():
        """Create settings panel with persistence"""
        with gr.Column(elem_classes=["settings-panel"]):
            language = gr.Radio(
                choices=[("中文", "zh"), ("English", "en")],
                value="zh",
                label="语言 / Language",
                interactive=True
            )
            theme = gr.Radio(
                choices=[("浅色", "light"), ("深色", "dark")],
                value="light",
                label="主题 / Theme"
            )
            model = gr.Dropdown(
                choices=[],
                label="模型 / Model",
                interactive=True
            )
            return language, theme, model

    @staticmethod
    def create_export_panel():
        """Create export options panel"""
        with gr.Row():
            with gr.Column(scale=1):
                citation_style = gr.Dropdown(
                    choices=["APA", "MLA", "IEEE", "Chicago", "GB/T 7714"],
                    value="APA",
                    label="引用格式",
                    interactive=True
                )
            with gr.Column(scale=2):
                with gr.Row():
                    export_md = gr.Button("📥 导出 Markdown", variant="secondary")
                    export_docx = gr.Button("📥 导出 Word", variant="secondary")
                    export_bib = gr.Button("📥 导出引用", variant="secondary")

        return citation_style, export_md, export_docx, export_bib

    @staticmethod
    def create_onboarding_tour():
        """Create interactive onboarding tour overlay"""
        tour_steps = [
            {
                "title": "欢迎使用 ResearchPal! 🎉",
                "content": "让我带你快速了解核心功能",
                "target": "#main-header"
            },
            {
                "title": "上传论文 📄",
                "content": "拖拽PDF文件到这里，AI会自动解析内容",
                "target": ".upload-zone"
            },
            {
                "title": "智能摘要 📝",
                "content": "选择摘要模式，快速掌握论文要点",
                "target": "#summary-section"
            },
            {
                "title": "写作润色 ✍️",
                "content": "粘贴文本，选择期刊风格，获得专业建议",
                "target": "#polish-section"
            },
            {
                "title": "开始使用! 🚀",
                "content": "现在就试试上传一篇论文吧",
                "target": None
            }
        ]

        return gr.HTML(
            value='<div class="tour-overlay" id="tour-overlay" style="display:none;"></div>',
            elem_classes=["tour-container"]
        ), tour_steps

    @staticmethod
    def create_error_display(error_type: str, message: str, recovery: str, lang: str = "zh"):
        """Create user-friendly error display with recovery steps"""
        icons = {
            "network": "🌐",
            "file": "📄",
            "server": "⚙️",
            "timeout": "⏱️",
            "validation": "⚠️"
        }

        icon = icons.get(error_type, "❌")

        if lang == "zh":
            error_html = f"""
            <div class="error-container error-{error_type}">
                <div class="error-icon">{icon}</div>
                <div class="error-content">
                    <h4>错误</h4>
                    <p>{message}</p>
                    <div class="error-recovery">
                        <strong>解决方法：</strong> {recovery}
                    </div>
                </div>
            </div>
            """
        else:
            error_html = f"""
            <div class="error-container error-{error_type}">
                <div class="error-icon">{icon}</div>
                <div class="error-content">
                    <h4>Error</h4>
                    <p>{message}</p>
                    <div class="error-recovery">
                        <strong>How to fix:</strong> {recovery}
                    </div>
                </div>
            </div>
            """

        return gr.HTML(value=error_html, elem_classes=["error-display"])

    @staticmethod
    def create_keyboard_hints():
        """Create keyboard shortcut hints overlay"""
        hints = [
            ("Ctrl + U", "上传文件"),
            ("Ctrl + Enter", "开始分析"),
            ("Ctrl + S", "保存结果"),
            ("Ctrl + E", "导出"),
            ("?", "显示帮助")
        ]

        hints_html = "<div class='keyboard-hints'><h4>快捷键</h4><ul>"
        for key, action in hints:
            hints_html += f"<li><kbd>{key}</kbd> {action}</li>"
        hints_html += "</ul></div>"

        return gr.HTML(value=hints_html, elem_classes=["hints-overlay"], visible=False)
