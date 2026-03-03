"""
ResearchPal Gradio应用 - 优化版启动脚本
包含性能优化、错误处理、缓存等功能
"""
from __future__ import annotations
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.gradio_app import demo
from frontend.gradio_config import get_gradio_launch_config, ensure_temp_dir
from frontend.gradio_utils import clear_cache, get_cache_stats

def main():
    """主启动函数"""
    print("=" * 60)
    print("🚀 ResearchPal AI - 学术写作智能助手")
    print("=" * 60)

    # 确保临时目录存在
    temp_dir = ensure_temp_dir()
    print(f"📁 临时文件目录: {temp_dir}")

    # 显示缓存状态
    cache_stats = get_cache_stats()
    print(f"💾 缓存配置: 最大{cache_stats['max_size']}条, TTL={cache_stats['ttl']}秒")

    # 获取启动配置
    config = get_gradio_launch_config()

    print(f"🌐 服务地址: http://{config['server_name']}:{config['server_port']}")
    print(f"⚙️  队列模式: {'启用' if config['enable_queue'] else '禁用'}")
    print("=" * 60)
    print("✨ 启动中，请稍候...")
    print()

    try:
        # 启动Gradio应用
        demo.queue() if config['enable_queue'] else None
        demo.launch(**config)
    except KeyboardInterrupt:
        print("\n\n👋 正在关闭服务...")
        clear_cache()
        print("✅ 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
