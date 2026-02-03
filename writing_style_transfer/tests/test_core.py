"""
学术写作风格迁移模块测试
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.text_analyzer import TextAnalyzer
from core.style_scorer import StyleScorer, AcademicDomain
from core.grammar_checker import GrammarChecker
from core.style_transfer import StyleTransfer, JournalStyle
from core.version_diff import VersionDiff


def test_text_analyzer():
    """测试文本分析器"""
    print("\n" + "="*50)
    print("测试文本分析器")
    print("="*50)
    
    analyzer = TextAnalyzer(use_modelscope=False)
    
    # 中文测试
    cn_text = "深度学习模型在自然语言处理任务中取得了显著的成果。然而，模型的可解释性仍然是一个重要的研究方向。"
    result = analyzer.analyze(cn_text)
    
    print(f"\n输入文本: {cn_text}")
    print(f"分词数量: {result.word_count}")
    print(f"句子数量: {result.sentence_count}")
    print(f"平均句长: {result.avg_sentence_length:.2f}")
    print(f"前5个词: {[t.word for t in result.tokens[:5]]}")
    
    # 英文测试
    en_text = "Deep learning models have achieved significant results in NLP tasks. However, model interpretability remains an important research direction."
    result_en = analyzer.analyze(en_text)
    
    print(f"\n英文文本词数: {result_en.word_count}")
    print(f"句子数: {result_en.sentence_count}")
    
    print("\n[PASS] 文本分析器测试通过")
    return True


def test_style_scorer():
    """测试风格评分器"""
    print("\n" + "="*50)
    print("测试风格评分器")
    print("="*50)
    
    scorer = StyleScorer()
    
    # 学术风格文本
    academic_text = """
    本研究提出了一种基于Transformer架构的深度学习模型，
    旨在解决自然语言处理中的文本分类问题。
    实验结果表明，该方法在多个基准数据集上取得了显著的性能提升。
    因此，我们认为该模型具有良好的泛化能力。
    """
    
    # 口语化文本
    casual_text = """
    我们做了一个很厉害的模型，效果非常好。
    好像比以前的方法都要强一些。
    所以我觉得这个东西还是挺有用的。
    """
    
    # 评分测试
    score1 = scorer.score(academic_text, AcademicDomain.COMPUTER_SCIENCE)
    score2 = scorer.score(casual_text, AcademicDomain.COMPUTER_SCIENCE)
    
    print(f"\n学术文本评分:")
    print(f"  正式程度: {score1.formality_score}")
    print(f"  被动语态比例: {score1.passive_voice_ratio}")
    print(f"  术语匹配度: {score1.terminology_score}")
    print(f"  综合评分: {score1.overall_score}")
    
    print(f"\n口语文本评分:")
    print(f"  正式程度: {score2.formality_score}")
    print(f"  被动语态比例: {score2.passive_voice_ratio}")
    print(f"  术语匹配度: {score2.terminology_score}")
    print(f"  综合评分: {score2.overall_score}")
    
    # 验证学术文本分数应该更高
    assert score1.overall_score > score2.overall_score, "学术文本评分应高于口语文本"
    
    # 获取改进建议
    suggestions = scorer.get_improvement_suggestions(score2)
    print(f"\n口语文本改进建议:")
    for s in suggestions:
        print(f"  - {s}")
    
    print("\n[PASS] 风格评分器测试通过")
    return True


def test_grammar_checker():
    """测试语法检查器"""
    print("\n" + "="*50)
    print("测试语法检查器")
    print("="*50)
    
    checker = GrammarChecker(use_language_tool=False)
    
    # 包含问题的文本
    test_text = "这个研究很有意思，所以我们决定进一步探索。a lot of experiments were conducted."
    
    suggestions = checker.check(test_text)
    
    print(f"\n输入文本: {test_text}")
    print(f"发现问题数: {len(suggestions)}")
    
    for i, s in enumerate(suggestions, 1):
        print(f"\n问题 {i}:")
        print(f"  类型: {s.type.value}")
        print(f"  原文: '{s.original}'")
        print(f"  建议: {s.message}")
        if s.replacement:
            print(f"  替换: '{s.replacement}'")
    
    # 应用建议
    corrected = checker.apply_suggestions(test_text, suggestions)
    if corrected != test_text:
        print(f"\n修正后: {corrected}")
    
    print("\n[PASS] 语法检查器测试通过")
    return True


def test_style_transfer():
    """测试风格迁移器"""
    print("\n" + "="*50)
    print("测试风格迁移器")
    print("="*50)
    
    transfer = StyleTransfer(use_modelscope=False)
    
    # 测试文本
    test_text = "我们做了一个模型，效果很好。实验表明它比其他方法都强。"
    
    # 测试不同风格
    for style in [JournalStyle.GENERAL_ACADEMIC, JournalStyle.NATURE]:
        result = transfer.transfer(test_text, style)
        
        print(f"\n目标风格: {style.value}")
        print(f"原文: {result.original_text}")
        print(f"迁移后: {result.transferred_text}")
        print(f"改动: {result.changes_made}")
        print(f"置信度: {result.confidence}")
    
    # 获取可用风格列表
    styles = transfer.list_available_styles()
    print(f"\n可用风格列表: {[s['id'] for s in styles]}")
    
    print("\n[PASS] 风格迁移器测试通过")
    return True


def test_version_diff():
    """测试版本对比器"""
    print("\n" + "="*50)
    print("测试版本对比器")
    print("="*50)
    
    diff = VersionDiff(cache_dir="./test_cache")
    
    # 测试版本保存
    doc_id = "test_doc_001"
    
    v1 = diff.save_version(doc_id, "这是第一个版本的文本内容。", label="原稿")
    v2 = diff.save_version(doc_id, "这是第二个版本的文本，做了一些修改。", label="修改版")
    
    print(f"\n保存版本 1: {v1.version_id}")
    print(f"保存版本 2: {v2.version_id}")
    
    # 获取版本列表
    versions = diff.get_versions(doc_id)
    print(f"版本总数: {len(versions)}")
    
    # 文本对比
    text_a = "深度学习模型取得了很好的效果。"
    text_b = "深度学习模型在实验中取得了显著的效果。"
    
    result = diff.compare(text_a, text_b)
    
    print(f"\n文本对比:")
    print(f"  相似度: {result.similarity}")
    print(f"  统计摘要: {result.summary}")
    print(f"  差异片段数: {len(result.segments)}")
    
    # 显示HTML差异
    print(f"\nHTML差异预览 (前200字符):")
    print(f"  {result.html_diff[:200]}...")
    
    # 清理测试数据
    diff.clear_versions(doc_id)
    
    # 清理测试缓存目录
    import shutil
    if os.path.exists("./test_cache"):
        shutil.rmtree("./test_cache")
    
    print("\n[PASS] 版本对比器测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("学术写作风格迁移模块 - 功能测试")
    print("="*60)
    
    tests = [
        ("文本分析器", test_text_analyzer),
        ("风格评分器", test_style_scorer),
        ("语法检查器", test_grammar_checker),
        ("风格迁移器", test_style_transfer),
        ("版本对比器", test_version_diff),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name} 测试失败: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
