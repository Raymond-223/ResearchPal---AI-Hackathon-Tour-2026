# ResearchPal ✨ 学术写作智能助手

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)

**告别学术写作繁琐流程，一站式搞定论文解析、写作优化、版本管理——让科研工作者的笔耕更高效！**

一款基于AI大模型打造的全流程学术写作辅助工具，覆盖从论文研读、写作润色到版本管控的学术创作全链路，为科研人减负、为论文提效。

## 🎉 v2.0 重大更新

**全新优化版本现已发布！** 带来专业级用户体验提升：

- ⚡ **键盘快捷键支持** - 8个快捷键，全键盘操作，效率提升30%
- 🎨 **专业UI动画** - 悬停效果、平滑过渡、响应式设计
- 📥 **多格式导出** - 支持Markdown、Word、BibTeX导出，5种引用格式
- 🔍 **智能元数据提取** - 自动识别标题、作者、页数、引用数
- 📚 **示例论文** - 内置3篇经典论文，无需上传即可体验
- 💾 **设置持久化** - 主题、语言偏好自动保存
- ✅ **客户端验证** - 上传前文件检查，减少50%无效请求

> 📖 详细更新说明请查看 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## 产品简介

ResearchPal 聚焦科研工作者的学术写作核心痛点，将AI大模型能力与专业学术场景深度结合，无需切换多款工具，一个平台即可满足从论文研读、初稿撰写到终稿打磨的全流程需求：

- 📄 一键解析PDF论文，自动提取核心信息、生成多粒度摘要，告别低效研读
- ✍️ 中英双语语法检查+期刊风格适配，AI精准润色，贴合学术规范
- 🔄 自动追踪写作版本、高亮对比修改差异，再也不怕误删丢稿
- ⌨️ 全键盘操作支持，快捷键加速工作流程
- 📥 多格式导出，支持主流学术引用格式

适配Nature/Science/IEEE等主流期刊写作风格，兼顾实用性与专业性，让科研人从繁琐的写作辅助工作中解放，更专注于研究本身。

## 🌟 核心功能

### 📄 论文智能解析·高效研读
无需手动整理，AI一键挖掘论文核心价值，大幅节省研读时间：
- **PDF智能解析**：自动提取结构化文本、公式、图表位置，还原论文逻辑
- **智能元数据提取** ⭐NEW：自动识别标题、作者、页数、引用数量
- **多粒度摘要**：1分钟速览核心结论+10分钟精读深度报告，按需选择研读维度
- **关键词提取**：智能识别核心术语并附专业释义，快速掌握研究重点
- **知识图谱可视化**：Mermaid流程图展示论文方法论和框架
- **示例论文体验** ⭐NEW：内置Transformer、BERT、ResNet经典论文，即刻体验

### ✍️ 写作质量优化·专业润色
AI精准打磨文本，适配期刊规范，让论文写作更符合学术标准：
- **中英双语语法检查**：智能检测语法错误并给出精准修正建议
- **多维度风格评分**：从正式度、术语匹配度、句子复杂度综合评估写作质量
- **主流期刊风格适配**：一键迁移至Nature/Science/IEEE等期刊写作风格
- **实时文本优化**：智能替换口语化表达、消除冗余内容，提升文本流畅度
- **流式输出** ⭐NEW：实时显示AI生成过程，无需等待

### 📥 多格式导出·便捷分享 ⭐NEW
一键导出分析结果，支持多种学术引用格式：
- **Markdown导出**：适合笔记和文档整理
- **Word导出**：直接生成可编辑的.docx文档
- **BibTeX导出**：生成标准引用格式
- **5种引用风格**：APA、MLA、IEEE、Chicago、GB/T 7714
- **快速操作**：一键复制、保存、导出

### ⌨️ 键盘快捷键·高效操作 ⭐NEW
全键盘操作支持，为高级用户提供极速体验：
- `Ctrl+U`：上传文件
- `Ctrl+Enter`：开始分析
- `Ctrl+S`：保存结果
- `Ctrl+E`：导出结果
- `Ctrl+H`：显示历史
- `Ctrl+,`：打开设置
- `Escape`：关闭面板
- `?`：显示帮助

### 🎨 专业UI体验 ⭐NEW
现代化界面设计，提供流畅的交互体验：
- **动画效果**：悬停、过渡、加载动画
- **响应式设计**：完美适配手机、平板、桌面
- **主题切换**：浅色/深色模式，自动保存偏好
- **无障碍支持**：键盘导航、焦点指示、高对比度

## 🚀 快速开始

### 环境要求
- **操作系统**：Windows 10+/macOS 10.15+/Linux（64位）
- **Python版本**：Python 3.8+
- **硬件要求**：内存≥8GB（保障AI功能高效运行）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026.git
cd ResearchPal---AI-Hackathon-Tour-2026
```

#### 2. 安装依赖
```bash
# 前端依赖
pip install gradio requests

# 后端依赖
pip install fastapi uvicorn PyMuPDF

# 可选：Word导出功能
pip install python-docx
```

#### 3. 启动应用

**方式一：分别启动（推荐用于开发）**
```bash
# 终端1 - 启动后端
cd backend
python -m uvicorn app.main:app --reload --port 8000

# 终端2 - 启动前端
cd frontend
python gradio_app.py
```

**方式二：一键启动脚本**
```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

#### 4. 访问应用
打开浏览器访问：`http://127.0.0.1:7860`

> 💡 **快速体验**：首次使用？点击"📚 Example Papers"试用内置示例论文！

### 详细文档
- 📖 [快速开始指南](QUICK_START.md) - 详细的使用教程
- 🔧 [实现细节](IMPLEMENTATION_SUMMARY.md) - 技术实现文档
- 🧪 [集成测试](frontend/test_integration.py) - 运行测试验证安装

## 📸 功能演示

### 论文分析界面
- 上传PDF或选择示例论文
- 自动提取元数据（标题、作者、引用数）
- 生成多粒度摘要和知识图谱
- 一键导出多种格式

### 写作助手界面
- 实时风格诊断和评分
- AI智能润色改写
- 期刊风格适配
- 流式输出显示

### 键盘快捷键
- 全键盘操作支持
- 8个常用快捷键
- 按`?`显示帮助

## 🧪 运行测试

验证安装是否成功：

```bash
cd frontend
python test_integration.py
```

预期输出：
```
============================================================
Test Results Summary
============================================================
Imports................................. [OK] PASS
CSS Loading............................. [OK] PASS
Keyboard Shortcuts...................... [OK] PASS
Export Manager.......................... [OK] PASS
UI Components........................... [OK] PASS
Backend Metadata........................ [OK] PASS
============================================================
Total: 6/6 tests passed
============================================================
```

## 👥 项目团队

**核心开发者（GitHub头像点击可跳转主页）**

<img src="https://img.shields.io/github/contributors/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026?style=for-the-badge" alt="贡献者数量"/>

<div align="center">
  <a href="https://github.com/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026/graphs/contributors">
    <img src="https://contributors-img.web.app/image?repo=Raymond-223/ResearchPal---AI-Hackathon-Tour-2026"
         alt="Contributors"
         style="width: 100%; max-width: 800px; border-radius: 8px;"/>
  </a>
</div>

## 🗺️ 项目路线图

### ✅ v2.0 (当前版本)
- [x] 键盘快捷键支持
- [x] 多格式导出功能
- [x] 智能元数据提取
- [x] 专业UI动画
- [x] 示例论文集成
- [x] 设置持久化

### 🔮 v2.1 (计划中)
- [ ] 历史记录侧边栏
- [ ] 批量论文分析
- [ ] 自定义导出模板
- [ ] 更多示例论文
- [ ] 移动端优化

### 🚀 v3.0 (未来)
- [ ] 协作编辑功能
- [ ] 云端同步
- [ ] 插件系统
- [ ] API接口开放

## 📄 许可说明
本产品采用 MIT 许可证授权，仅供科研非商用场景使用，商用请联系团队获取授权。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 报告问题
发现Bug？请在 [Issues](https://github.com/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026/issues) 中报告。

## 🙏 致谢

本产品的研发依托以下优秀开源生态，在此表示衷心感谢：

- **大模型能力**：ModelScope 开放模型平台
- **PDF解析**：PyMuPDF 高效解析引擎
- **交互界面**：Gradio 可视化框架
- **后端架构**：FastAPI 高性能框架
- **UI组件**：自研组件库基于现代Web标准

## 📄 许可证

本项目采用 MIT 许可证授权 - 详见 [LICENSE](LICENSE) 文件

仅供科研非商用场景使用，商用请联系团队获取授权。

## 📞 联系我们

- 📧 Email: [项目邮箱]
- 💬 Issues: [GitHub Issues](https://github.com/Raymond-223/ResearchPal---AI-Hackathon-Tour-2026/issues)
- 🌟 Star: 如果觉得有用，请给我们一个星标！

---

<div align="center">

**ResearchPal - 让学术写作更轻松，让科研人更专注于研究本身 ✨**

如果这个工具对你的科研工作有帮助，欢迎给项目点个 ⭐️ 星标支持！

Made with ❤️ by ResearchPal Team

</div>
