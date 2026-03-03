"""
Keyboard shortcuts handler for ResearchPal
Provides keyboard-first navigation for power users
"""
import gradio as gr
from typing import Callable, Dict, List

class KeyboardShortcuts:
    """Manage keyboard shortcuts for Gradio interface"""

    def __init__(self):
        self.shortcuts: Dict[str, Dict] = {}
        self._register_default_shortcuts()

    def _register_default_shortcuts(self):
        """Register default keyboard shortcuts"""
        self.shortcuts = {
            "Ctrl+U": {
                "description": "上传文件 / Upload file",
                "action": "upload",
                "icon": "📄"
            },
            "Ctrl+Enter": {
                "description": "开始分析 / Start analysis",
                "action": "submit",
                "icon": "▶️"
            },
            "Ctrl+S": {
                "description": "保存结果 / Save results",
                "action": "save",
                "icon": "💾"
            },
            "Ctrl+E": {
                "description": "导出结果 / Export results",
                "action": "export",
                "icon": "📥"
            },
            "Ctrl+H": {
                "description": "显示历史 / Show history",
                "action": "history",
                "icon": "📜"
            },
            "Ctrl+,": {
                "description": "打开设置 / Open settings",
                "action": "settings",
                "icon": "⚙️"
            },
            "Escape": {
                "description": "关闭面板 / Close panel",
                "action": "close",
                "icon": "❌"
            },
            "?": {
                "description": "显示帮助 / Show help",
                "action": "help",
                "icon": "❓"
            }
        }

    def register(self, key: str, description: str, action: str, icon: str = "⌨️"):
        """Register a custom keyboard shortcut"""
        self.shortcuts[key] = {
            "description": description,
            "action": action,
            "icon": icon
        }

    def get_shortcuts_by_action(self) -> Dict[str, str]:
        """Get shortcuts mapped by action for quick lookup"""
        return {
            details["action"]: key
            for key, details in self.shortcuts.items()
        }

    def get_shortcuts_list(self, lang: str = "zh") -> List[str]:
        """Get formatted list of shortcuts for display"""
        lines = []
        for key, details in self.shortcuts.items():
            desc = details["description"]
            icon = details["icon"]
            lines.append(f"{icon} `{key}` {desc}")
        return lines

    def generate_javascript_handler(self) -> str:
        """Generate JavaScript keyboard event handler for Gradio"""
        js_code = """
        <script>
        (function() {
            const shortcuts = {
        """

        shortcut_map = []
        for key, details in self.shortcuts.items():
            # Convert key combination to event properties
            if "Ctrl+" in key:
                key_part = key.replace("Ctrl+", "").lower()
                shortcut_map.append(
                    f'"{key}": {{ctrl: true, key: "{key_part}", action: "{details["action"]}"}}'
                )
            elif key == "Escape":
                shortcut_map.append(f'"{key}": {{key: "Escape", action: "{details["action"]}"}}')
            elif key == "?":
                shortcut_map.append(f'"{key}": {{key: "?", shift: true, action: "{details["action"]}"}}')

        js_code += ",\n        ".join(shortcut_map)
        js_code += """
            };

            document.addEventListener('keydown', function(e) {
                for (const [combo, config] of Object.entries(shortcuts)) {
                    const ctrlMatch = config.ctrl ? e.ctrlKey || e.metaKey : true;
                    const shiftMatch = config.shift ? e.shiftKey : !e.shiftKey;
                    const keyMatch = e.key.toLowerCase() === config.key;

                    if (ctrlMatch && shiftMatch && keyMatch) {
                        e.preventDefault();

                        // Dispatch custom event
                        const event = new CustomEvent('researchpal:shortcut', {
                            detail: { action: config.action, combo: combo }
                        });
                        document.dispatchEvent(event);

                        console.log(`Shortcut triggered: ${combo} -> ${config.action}`);
                        break;
                    }
                }
            });

            // Listen for custom events
            document.addEventListener('researchpal:shortcut', function(e) {
                const action = e.detail.action;

                // Find and click corresponding button
                const button = document.querySelector(`[data-action="${action}"]`);
                if (button) {
                    button.click();
                }
            });
        })();
        </script>
        """

        return js_code

    def create_help_display(self, lang: str = "zh") -> str:
        """Create keyboard shortcuts help display"""
        if lang == "zh":
            title = "## ⌨️ 快捷键列表\n"
            subtitle = "使用键盘快捷键提高效率\n\n"
        else:
            title = "## ⌨️ Keyboard Shortcuts\n"
            subtitle = "Improve efficiency with keyboard shortcuts\n\n"

        shortcuts_list = self.get_shortcuts_list(lang)
        return title + subtitle + "\n".join(f"- {item}" for item in shortcuts_list)

    def apply_to_gradio(self, component) -> any:
        """Apply keyboard shortcuts to a Gradio component"""
        js_handler = self.generate_javascript_handler()
        # Return JavaScript as HTML component
        return gr.HTML(value=js_handler, elem_classes=["keyboard-handler"])


class ShortcutActions:
    """Predefined shortcut action handlers"""

    @staticmethod
    def trigger_upload():
        """Trigger file upload button"""
        return gr.File(value=None, interactive=True)

    @staticmethod
    def trigger_submit():
        """Trigger submit/analyze button"""
        return gr.Button(value="开始分析", variant="primary", interactive=True)

    @staticmethod
    def trigger_export():
        """Trigger export button"""
        return gr.Button(value="导出", variant="secondary")

    @staticmethod
    def toggle_panel(panel_visible: bool) -> bool:
        """Toggle panel visibility"""
        return not panel_visible

    @staticmethod
    def close_modal():
        """Close modal/overlay"""
        return gr.update(visible=False)


# Global keyboard shortcuts instance
keyboard_shortcuts = KeyboardShortcuts()


def get_keyboard_shortcuts():
    """Get global keyboard shortcuts instance"""
    return keyboard_shortcuts
