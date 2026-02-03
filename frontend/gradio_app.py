from __future__ import annotations
import os
import requests
import gradio as gr

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def call_parse(pdf_file):
    with open(pdf_file, "rb") as f:
        r = requests.post(f"{BACKEND}/api/paper/parse", files={"file": f})
    r.raise_for_status()
    data = r.json()
    return data.get("full_text", ""), data

def call_summary(text, mode):
    r = requests.post(f"{BACKEND}/api/paper/summary", json={"text": text, "mode": mode})
    r.raise_for_status()
    d = r.json()
    return d["one_liner"], d["detailed"], d["mermaid"]

def call_profile(text, domain):
    r = requests.post(f"{BACKEND}/api/write/profile", json={"text": text, "domain": domain})
    r.raise_for_status()
    d = r.json()
    return d["lexical"], d["structural"], "\n".join(d["diagnostics"])

def call_transfer(text, journal, formality, domain):
    r = requests.post(
        f"{BACKEND}/api/write/transfer",
        json={"text": text, "target_journal": journal, "formality": formality, "domain": domain},
    )
    r.raise_for_status()
    d = r.json()
    return d["rewritten"], "\n".join(d["suggestions"])

with gr.Blocks(title="ResearchPal MVP") as demo:
    gr.Markdown("# 研途助手 ResearchPal (MVP)\n仅用于48小时闭环联调：mock→可替换模型")

    with gr.Tabs():
        with gr.Tab("论文解读"):
            pdf = gr.File(label="上传PDF", file_types=[".pdf"])
            parse_btn = gr.Button("解析PDF")
            parsed_text = gr.Textbox(label="解析后全文(用于摘要输入)", lines=8)
            raw_json = gr.JSON(label="解析结果JSON")

            mode = gr.Dropdown(choices=["mvp", "fast", "deep"], value="mvp", label="摘要模式")
            sum_btn = gr.Button("生成摘要")
            one = gr.Textbox(label="1分钟速览", lines=3)
            detailed = gr.Textbox(label="10分钟精读", lines=8)
            mermaid = gr.Textbox(label="Mermaid图(复制到Mermaid渲染)", lines=6)

            parse_btn.click(call_parse, inputs=[pdf], outputs=[parsed_text, raw_json])
            sum_btn.click(call_summary, inputs=[parsed_text, mode], outputs=[one, detailed, mermaid])

        with gr.Tab("写作助手"):
            text = gr.Textbox(label="输入/粘贴段落", lines=8, value="Our experiment shows that the method works well.")
            domain = gr.Dropdown(choices=["cs", "bio", "med"], value="cs", label="领域")

            prof_btn = gr.Button("风格分析")
            lexical = gr.JSON(label="lexical")
            structural = gr.JSON(label="structural")
            diagnostics = gr.Textbox(label="诊断建议", lines=6)

            journal = gr.Dropdown(choices=["Nature", "ACL", "IEEE"], value="Nature", label="目标期刊")
            formality = gr.Slider(0, 1, value=0.85, step=0.05, label="正式程度")
            trans_btn = gr.Button("风格迁移/改写")
            rewritten = gr.Textbox(label="改写结果", lines=8)
            suggestions = gr.Textbox(label="改写建议", lines=6)

            prof_btn.click(call_profile, inputs=[text, domain], outputs=[lexical, structural, diagnostics])
            trans_btn.click(call_transfer, inputs=[text, journal, formality, domain], outputs=[rewritten, suggestions])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)