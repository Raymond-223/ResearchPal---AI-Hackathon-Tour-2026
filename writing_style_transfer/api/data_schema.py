"""
数据交互格式定义
供前后端/算法模块之间协作参考

【重要】与全栈工程师的接口约定
"""

# ============ API接口清单 ============

API_ENDPOINTS = {
    "base_url": "http://localhost:8000",
    "endpoints": {
        # 文本分析
        "analyze": {
            "method": "POST",
            "path": "/write/analyze",  # 更新路径
            "description": "文本分词和词性标注"
        },
        # 风格评分
        "profile": {  # 更新端点名称
            "method": "POST", 
            "path": "/write/profile",  # 更新路径
            "description": "学术写作风格评分"
        },
        # 语法检查
        "check": {
            "method": "POST",
            "path": "/write/check",  # 更新路径
            "description": "语法检查和优化建议"
        },
        # 风格迁移
        "transfer": {
            "method": "POST",
            "path": "/write/transfer",  # 更新路径
            "description": "期刊风格迁移"
        },
        # 文本对比
        "diff": {
            "method": "POST",
            "path": "/write/diff",  # 更新路径
            "description": "版本差异对比"
        },
        # 综合分析
        "full_analysis": {
            "method": "POST",
            "path": "/write/full-analysis",  # 更新路径
            "description": "一站式综合分析"
        }
    }
}


# ============ 请求格式示例 ============

# 1. 文本分析请求
ANALYZE_REQUEST = {
    "text": "待分析的文本内容..."
}

# 2. 风格评分请求
SCORE_REQUEST = {
    "text": "待评分的文本内容...",
    "domain": "computer_science"  # 可选: general, computer_science, natural_science, medical, engineering, social_science
}

# 3. 语法检查请求
CHECK_REQUEST = {
    "text": "待检查的文本内容..."
}

# 4. 风格迁移请求
TRANSFER_REQUEST = {
    "text": "待迁移的文本内容...",
    "target_style": "nature"  # 可选: nature, science, acl, ieee, general
}

# 5. 文本对比请求
DIFF_REQUEST = {
    "text_a": "原始文本...",
    "text_b": "修改后文本...",
    "char_level": True  # True=字符级对比, False=行级对比
}

# 6. 综合分析请求
FULL_ANALYSIS_REQUEST = {
    "text": "待分析文本...",
    "domain": "computer_science",
    "target_style": "nature"  # 可选，如果提供则同时做风格迁移
}


# ============ 响应格式示例 ============

# 1. 文本分析响应
ANALYZE_RESPONSE = {
    "tokens": [
        {"word": "深度", "pos": "n", "start": 0, "end": 2},
        {"word": "学习", "pos": "v", "start": 2, "end": 4}
    ],
    "sentences": ["句子1", "句子2"],
    "statistics": {
        "word_count": 50,
        "sentence_count": 3,
        "avg_sentence_length": 16.67
    }
}

# 2. 风格评分响应
SCORE_RESPONSE = {
    "scores": {
        "formality": 75.5,          # 正式程度 0-100
        "passive_voice_ratio": 45.2, # 被动语态比例 0-100
        "terminology": 68.0,         # 术语匹配度 0-100
        "sentence_complexity": 72.3, # 句子复杂度 0-100
        "overall": 65.25             # 综合评分 0-100
    },
    "details": {
        "word_count": 100,
        "sentence_count": 5,
        "domain": "computer_science",
        "informal_words_found": ["很", "所以"],
        "formal_words_found": ["因此", "表明"]
    },
    "suggestions": [
        "建议减少口语化表达",
        "可适当增加领域术语"
    ]
}

# 3. 语法检查响应
CHECK_RESPONSE = {
    "suggestions": [
        {
            "type": "word_choice",
            "message": "建议将「很多」替换为更学术的表达：大量/众多",
            "original": "很多",
            "replacement": "大量",
            "position": {"start": 10, "end": 12},
            "severity": "info"  # error/warning/info
        }
    ],
    "corrected_text": "应用建议后的文本..."  # 如果没有可用建议则为null
}

# 4. 风格迁移响应
TRANSFER_RESPONSE = {
    "original": "原始文本...",
    "transferred": "迁移后文本...",
    "target_style": "nature",
    "changes": [
        "使用了更正式的连接词",
        "增加了被动语态使用"
    ],
    "confidence": 0.85  # 迁移置信度 0-1
}

# 5. 文本对比响应
DIFF_RESPONSE = {
    "similarity": 0.7823,  # 相似度 0-1
    "html_diff": "<span>相同部分</span><span class='diff-delete'>删除</span><span class='diff-insert'>新增</span>",
    "summary": {
        "insertions": 15,      # 新增字符数
        "deletions": 8,        # 删除字符数
        "replacements": 2,     # 替换处数
        "unchanged_chars": 85, # 未变字符数
        "total_changes": 23    # 总变化数
    },
    "segments": [
        {
            "type": "equal",    # equal/insert/delete/replace
            "original": "相同文本",
            "modified": "相同文本",
            "position": {"start": 0, "end": 4}
        },
        {
            "type": "replace",
            "original": "旧文本",
            "modified": "新文本",
            "position": {"start": 4, "end": 7}
        }
    ]
}


# ============ 前端集成示例代码 (Gradio) ============

GRADIO_INTEGRATION_EXAMPLE = '''
import gradio as gr
import requests

API_BASE = "http://localhost:8001"

def analyze_text(text):
    """调用文本分析接口"""
    resp = requests.post(f"{API_BASE}/writing/analyze", json={"text": text})
    return resp.json()

def score_style(text, domain):
    """调用风格评分接口"""
    resp = requests.post(f"{API_BASE}/writing/score", json={"text": text, "domain": domain})
    return resp.json()

def transfer_style(text, style):
    """调用风格迁移接口"""
    resp = requests.post(f"{API_BASE}/writing/transfer", json={"text": text, "target_style": style})
    return resp.json()

def compare_texts(text_a, text_b):
    """调用文本对比接口"""
    resp = requests.post(f"{API_BASE}/writing/diff", json={"text_a": text_a, "text_b": text_b})
    return resp.json()

# Gradio界面示例
with gr.Blocks() as demo:
    with gr.Tab("风格评分"):
        input_text = gr.Textbox(label="输入文本", lines=5)
        domain = gr.Dropdown(
            choices=["general", "computer_science", "natural_science", "medical"],
            value="general",
            label="学术领域"
        )
        score_btn = gr.Button("评分")
        score_output = gr.JSON(label="评分结果")
        score_btn.click(score_style, [input_text, domain], score_output)
    
    with gr.Tab("风格迁移"):
        input_text2 = gr.Textbox(label="输入文本", lines=5)
        style = gr.Dropdown(
            choices=["nature", "science", "acl", "ieee", "general"],
            value="nature",
            label="目标风格"
        )
        transfer_btn = gr.Button("迁移")
        transfer_output = gr.JSON(label="迁移结果")
        transfer_btn.click(transfer_style, [input_text2, style], transfer_output)

demo.launch()
'''


if __name__ == "__main__":
    print("数据交互格式定义")
    print("="*50)
    print("\nAPI端点:")
    for name, info in API_ENDPOINTS["endpoints"].items():
        print(f"  {info['method']} {info['path']} - {info['description']}")
