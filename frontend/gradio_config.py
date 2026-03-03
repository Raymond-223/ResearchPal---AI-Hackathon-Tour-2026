"""
Gradio优化配置文件
包含性能优化、缓存策略、并发控制等配置
"""
import os
from functools import lru_cache
from typing import Dict, Any

# Gradio服务器配置
GRADIO_CONFIG = {
    "server_name": "127.0.0.1",
    "server_port": 7860,
    "share": False,  # 设置为True可生成公网链接
    "inbrowser": True,
    "show_error": True,
    "max_threads": 40,  # 最大并发线程数
    "auth": None,  # 可设置为 ("username", "password") 启用认证
}

# 文件上传配置
FILE_UPLOAD_CONFIG = {
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "allowed_extensions": [".pdf"],
    "temp_dir": os.path.join(os.path.dirname(__file__), "temp_uploads"),
}

# 缓存配置
CACHE_CONFIG = {
    "enable_cache": True,
    "cache_ttl": 3600,  # 缓存过期时间（秒）
    "max_cache_size": 100,  # 最大缓存条目数
}

# API超时配置
TIMEOUT_CONFIG = {
    "parse_timeout": 60,  # PDF解析超时
    "summary_timeout": 120,  # 摘要生成超时
    "transfer_timeout": 120,  # 润色改写超时
    "model_fetch_timeout": 5,  # 获取模型列表超时
}

# 性能优化配置
PERFORMANCE_CONFIG = {
    "enable_queue": True,  # 启用请求队列
    "queue_concurrency_count": 5,  # 队列并发数
    "enable_streaming": True,  # 启用流式输出
    "chunk_size": 1024,  # 流式输出块大小
}

# UI配置
UI_CONFIG = {
    "show_api": False,  # 是否显示API文档
    "show_progress": "full",  # 进度显示模式: "full", "minimal", "hidden"
    "enable_analytics": False,  # 禁用分析
}

@lru_cache(maxsize=1)
def get_backend_url() -> str:
    """获取后端URL（带缓存）"""
    return os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

def ensure_temp_dir():
    """确保临时目录存在"""
    temp_dir = FILE_UPLOAD_CONFIG["temp_dir"]
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def get_gradio_launch_config() -> Dict[str, Any]:
    """获取Gradio启动配置"""
    return {
        **GRADIO_CONFIG,
        "show_api": UI_CONFIG["show_api"],
        "enable_queue": PERFORMANCE_CONFIG["enable_queue"],
    }
