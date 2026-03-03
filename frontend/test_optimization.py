"""
ResearchPal Gradio优化测试脚本
用于验证各项优化功能是否正常工作
"""
import sys
import os
import io

# 设置UTF-8编码输出（Windows兼容）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试模块导入"""
    print("📦 测试模块导入...")
    try:
        from frontend.gradio_config import (
            GRADIO_CONFIG,
            FILE_UPLOAD_CONFIG,
            TIMEOUT_CONFIG,
            get_gradio_launch_config
        )
        from frontend.gradio_utils import (
            validate_pdf_file,
            create_error_message,
            create_success_message,
            cached,
            timed,
            retry_on_error,
            clear_cache,
            get_cache_stats
        )
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_config():
    """测试配置"""
    print("\n⚙️  测试配置...")
    try:
        from frontend.gradio_config import (
            GRADIO_CONFIG,
            FILE_UPLOAD_CONFIG,
            TIMEOUT_CONFIG,
            get_gradio_launch_config
        )

        assert GRADIO_CONFIG["server_port"] == 7860
        assert FILE_UPLOAD_CONFIG["max_file_size"] == 50 * 1024 * 1024
        assert TIMEOUT_CONFIG["parse_timeout"] == 60

        config = get_gradio_launch_config()
        assert "server_name" in config
        assert "server_port" in config

        print("✅ 配置测试通过")
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def test_utils():
    """测试工具函数"""
    print("\n🔧 测试工具函数...")
    try:
        from frontend.gradio_utils import (
            validate_pdf_file,
            create_error_message,
            create_success_message,
            create_loading_message,
            format_file_size,
            sanitize_filename,
            get_cache_stats
        )

        # 测试文件大小格式化
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"

        # 测试文件名清理
        assert sanitize_filename("test<>file.pdf") == "test__file.pdf"

        # 测试消息创建
        error_msg = create_error_message("测试错误", "zh")
        assert "❌" in error_msg

        success_msg = create_success_message("测试成功", "zh")
        assert "✅" in success_msg

        loading_msg = create_loading_message("加载中", "zh")
        assert "⏳" in loading_msg

        # 测试缓存统计
        stats = get_cache_stats()
        assert "size" in stats
        assert "max_size" in stats

        print("✅ 工具函数测试通过")
        return True
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False

def test_cache():
    """测试缓存功能"""
    print("\n💾 测试缓存功能...")
    try:
        from frontend.gradio_utils import cached, clear_cache, get_cache_stats

        call_count = 0

        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # 第二次调用（应该使用缓存）
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 没有增加，说明使用了缓存

        # 清空缓存
        clear_cache()
        stats = get_cache_stats()
        assert stats["size"] == 0

        print("✅ 缓存功能测试通过")
        return True
    except Exception as e:
        print(f"❌ 缓存功能测试失败: {e}")
        return False

def test_decorators():
    """测试装饰器"""
    print("\n🎨 测试装饰器...")
    try:
        from frontend.gradio_utils import timed, retry_on_error
        import time

        # 测试计时装饰器
        @timed
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()
        assert result == "done"

        # 测试重试装饰器
        attempt_count = 0

        @retry_on_error(max_retries=3, delay=0.1)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("模拟错误")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert attempt_count == 2  # 第一次失败，第二次成功

        print("✅ 装饰器测试通过")
        return True
    except Exception as e:
        print(f"❌ 装饰器测试失败: {e}")
        return False

def test_file_validation():
    """测试文件验证"""
    print("\n📄 测试文件验证...")
    try:
        from frontend.gradio_utils import validate_pdf_file

        # 测试空路径
        is_valid, error = validate_pdf_file("", max_size=50*1024*1024)
        assert not is_valid
        assert "未选择文件" in error or "文件" in error

        # 测试不存在的文件
        is_valid, error = validate_pdf_file("/nonexistent/file.pdf", max_size=50*1024*1024)
        assert not is_valid
        assert "不存在" in error or "文件" in error

        # 测试非PDF文件（使用当前脚本作为测试）
        current_file = __file__
        is_valid, error = validate_pdf_file(current_file, max_size=50*1024*1024)
        assert not is_valid
        assert "PDF" in error or "pdf" in error.lower()

        print("✅ 文件验证测试通过")
        return True
    except AssertionError as e:
        print(f"❌ 文件验证测试失败: 断言错误 - {e}")
        return False
    except Exception as e:
        print(f"❌ 文件验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 ResearchPal Gradio优化测试")
    print("=" * 60)

    tests = [
        test_imports,
        test_config,
        test_utils,
        test_cache,
        test_decorators,
        test_file_validation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    if failed == 0:
        print("🎉 所有测试通过！优化功能正常工作。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
