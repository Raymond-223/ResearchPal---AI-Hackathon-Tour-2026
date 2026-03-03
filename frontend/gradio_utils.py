"""
Gradio工具函数
包含缓存、错误处理、性能优化等辅助功能
"""
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta

# 简单的内存缓存实现
class SimpleCache:
    def __init__(self, ttl: int = 3600, max_size: int = 100):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.max_size = max_size

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry["expires"]:
                return entry["value"]
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 删除最旧的条目
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created"])
            del self.cache[oldest_key]

        self.cache[key] = {
            "value": value,
            "created": datetime.now(),
            "expires": datetime.now() + timedelta(seconds=self.ttl)
        }

    def clear(self):
        """清空缓存"""
        self.cache.clear()

# 全局缓存实例
_cache = SimpleCache(ttl=3600, max_size=100)

def cached(ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _cache._generate_key(func.__name__, *args, **kwargs)
            cached_result = _cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

def timed(func: Callable) -> Callable:
    """性能计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"⏱️ {func.__name__} 执行时间: {elapsed:.2f}秒")
        return result
    return wrapper

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def validate_pdf_file(file_path: str, max_size: int = 50 * 1024 * 1024) -> tuple[bool, str]:
    """
    验证PDF文件
    返回: (是否有效, 错误消息)
    """
    import os

    if not file_path:
        return False, "未选择文件"

    if not os.path.exists(file_path):
        return False, "文件不存在"

    if not file_path.lower().endswith('.pdf'):
        return False, "仅支持PDF文件"

    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        return False, f"文件过大（{format_file_size(file_size)}），最大支持{format_file_size(max_size)}"

    if file_size == 0:
        return False, "文件为空"

    return True, ""

def create_error_message(error: str, lang: str = "zh") -> str:
    """创建格式化的错误消息"""
    emoji = "❌"
    prefix = "错误" if lang == "zh" else "Error"
    return f"{emoji} {prefix}: {error}"

def create_success_message(message: str, lang: str = "zh") -> str:
    """创建格式化的成功消息"""
    emoji = "✅"
    prefix = "成功" if lang == "zh" else "Success"
    return f"{emoji} {prefix}: {message}"

def create_info_message(message: str, lang: str = "zh") -> str:
    """创建格式化的信息消息"""
    emoji = "ℹ️"
    return f"{emoji} {message}"

def create_loading_message(message: str = "处理中", lang: str = "zh") -> str:
    """创建格式化的加载消息"""
    emoji = "⏳"
    default_msg = "处理中，请稍候..." if lang == "zh" else "Processing..."
    return f"{emoji} {message or default_msg}"

def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    import re
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    return filename

def get_timestamp() -> str:
    """获取当前时间戳字符串"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """错误重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"⚠️ 尝试 {attempt + 1}/{max_retries} 失败: {str(e)}, {delay}秒后重试...")
                        time.sleep(delay)
                    else:
                        print(f"❌ 所有重试失败")
            raise last_exception
        return wrapper
    return decorator

# 导出缓存实例供外部使用
def clear_cache():
    """清空全局缓存"""
    _cache.clear()
    print("✅ 缓存已清空")

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return {
        "size": len(_cache.cache),
        "max_size": _cache.max_size,
        "ttl": _cache.ttl
    }
