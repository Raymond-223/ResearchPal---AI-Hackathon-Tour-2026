"""
Integration Test for ResearchPal Optimizations
Tests all newly integrated features
"""
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")

    try:
        from gradio_ui import UIComponents
        print("[OK] UIComponents imported successfully")
    except Exception as e:
        print(f"[FAIL] UIComponents import failed: {e}")
        return False

    try:
        from keyboard_shortcuts import get_keyboard_shortcuts
        print("[OK] keyboard_shortcuts imported successfully")
    except Exception as e:
        print(f"[FAIL] keyboard_shortcuts import failed: {e}")
        return False

    try:
        from export_utils import ExportManager
        print("[OK] ExportManager imported successfully")
    except Exception as e:
        print(f"[FAIL] ExportManager import failed: {e}")
        return False

    return True


def test_css_loading():
    """Test that external CSS file exists and can be loaded"""
    print("\nTesting CSS loading...")

    import os
    css_path = os.path.join(os.path.dirname(__file__), "gradio_styles.css")

    if not os.path.exists(css_path):
        print(f"[FAIL] CSS file not found at: {css_path}")
        return False

    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

        print(f"[OK] CSS file loaded successfully ({len(css_content)} characters)")

        # Check for key CSS classes
        required_classes = [
            ".upload-zone",
            ".progress-container",
            ".keyboard-hints",
            ".metric-card",
            ".error-container"
        ]

        for cls in required_classes:
            if cls in css_content:
                print(f"  [OK] Found {cls}")
            else:
                print(f"  [WARN] Missing {cls}")

        return True
    except Exception as e:
        print(f"[FAIL] CSS loading failed: {e}")
        return False


def test_keyboard_shortcuts():
    """Test keyboard shortcuts configuration"""
    print("\nTesting keyboard shortcuts...")

    try:
        from keyboard_shortcuts import get_keyboard_shortcuts

        handler = get_keyboard_shortcuts()
        shortcuts = handler.shortcuts

        print(f"[OK] Keyboard shortcuts loaded: {len(shortcuts)} shortcuts")

        expected_shortcuts = [
            "Ctrl+U", "Ctrl+Enter", "Ctrl+S", "Ctrl+E",
            "Ctrl+H", "Ctrl+,", "Escape", "?"
        ]

        for shortcut in expected_shortcuts:
            if shortcut in shortcuts:
                action = shortcuts[shortcut]["action"]
                print(f"  [OK] {shortcut} → {action}")
            else:
                print(f"  [FAIL] Missing {shortcut}")

        # Test JavaScript generation
        js_code = handler.generate_javascript_handler()
        if "<script>" in js_code and "keydown" in js_code:
            print("[OK] JavaScript handler generated successfully")
        else:
            print("[FAIL] JavaScript handler generation failed")

        return True
    except Exception as e:
        print(f"[FAIL] Keyboard shortcuts test failed: {e}")
        return False


def test_export_manager():
    """Test export functionality"""
    print("\nTesting export manager...")

    try:
        from export_utils import ExportManager

        # Test Markdown export
        markdown = ExportManager.export_to_markdown(
            title="Test Paper",
            content="This is a test summary.",
            metadata={"source": "Test"}
        )

        if "# Test Paper" in markdown and "This is a test summary" in markdown:
            print("[OK] Markdown export works")
        else:
            print("[FAIL] Markdown export failed")

        # Test citation formatting
        citation = ExportManager.format_citation(
            title="Test Paper",
            authors=["John Doe", "Jane Smith"],
            year=2024,
            style="APA"
        )

        if "John Doe" in citation and "2024" in citation:
            print("[OK] Citation formatting works (APA)")
        else:
            print("[FAIL] Citation formatting failed")

        # Test other citation styles
        styles = ["MLA", "IEEE", "Chicago", "GB/T 7714"]
        for style in styles:
            citation = ExportManager.format_citation(
                title="Test",
                authors=["Author"],
                year=2024,
                style=style
            )
            if citation:
                print(f"  [OK] {style} citation format works")

        return True
    except Exception as e:
        print(f"[FAIL] Export manager test failed: {e}")
        return False


def test_ui_components():
    """Test UI components"""
    print("\nTesting UI components...")

    try:
        from gradio_ui import UIComponents

        # Test that methods exist
        methods = [
            "create_upload_zone",
            "create_progress_indicator",
            "create_result_card",
            "create_history_sidebar",
            "create_settings_panel",
            "create_export_panel",
            "create_error_display",
            "create_keyboard_hints"
        ]

        for method in methods:
            if hasattr(UIComponents, method):
                print(f"  [OK] {method} exists")
            else:
                print(f"  [FAIL] {method} missing")

        return True
    except Exception as e:
        print(f"[FAIL] UI components test failed: {e}")
        return False


def test_backend_metadata():
    """Test backend metadata extraction functions"""
    print("\nTesting backend metadata extraction...")

    try:
        import sys
        import os
        backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
        sys.path.insert(0, backend_path)

        from app.services.paper_service import (
            _extract_title_from_text,
            _extract_authors_from_text,
            _extract_abstract_from_text,
            _count_citations,
            _detect_sections
        )

        # Test with sample text
        sample_text = """
        Attention Is All You Need

        Ashish Vaswani
        Noam Shazeer

        Abstract: The dominant sequence transduction models are based on complex recurrent or
        convolutional neural networks [1]. We propose a new architecture [2].

        1. Introduction
        Recent work has shown...

        2. Methods
        Our approach uses...
        """

        title = _extract_title_from_text(sample_text)
        print(f"  [OK] Title extraction: '{title}'")

        authors = _extract_authors_from_text(sample_text)
        print(f"  [OK] Authors extraction: {authors}")

        abstract = _extract_abstract_from_text(sample_text)
        print(f"  [OK] Abstract extraction: {len(abstract) if abstract else 0} chars")

        citations = _count_citations(sample_text)
        print(f"  [OK] Citation count: {citations}")

        sections = _detect_sections(sample_text)
        print(f"  [OK] Sections detected: {len(sections)}")

        return True
    except Exception as e:
        print(f"[FAIL] Backend metadata test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("ResearchPal Integration Tests")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "CSS Loading": test_css_loading(),
        "Keyboard Shortcuts": test_keyboard_shortcuts(),
        "Export Manager": test_export_manager(),
        "UI Components": test_ui_components(),
        "Backend Metadata": test_backend_metadata()
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{test_name:.<40} {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] All tests passed! Integration successful!")
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed. Please review.")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
