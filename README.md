# 论文解析与摘要生成算法库

## 项目简介

本算法库旨在为学术论文提供自动化解析、摘要生成和可视化功能，帮助研究人员快速理解论文核心内容。通过"1分钟抓核心、10分钟知全貌"的设计理念，实现高效的论文阅读体验。

## 核心功能

### 1. PDF解析模块 (`paper_parser.py`)
- **文本提取**：支持PDF文件流和本地文件路径输入
- **章节结构化**：自动识别摘要、引言、方法、实验、结论等章节
- **公式图表识别**：标记公式和图表位置，生成占位符
- **元数据补全**：通过ArXiv API获取论文元数据（标题、作者、发表日期等）

### 2. 摘要生成模块 (`summary_generator.py`)
- **1分钟速览**：生成150词以内的核心贡献和创新点摘要
- **10分钟精读**：分章节生成详细摘要（研究背景、方法、结果、结论）
- **关键词提取**：自动提取TOP10核心关键词，包含词频和释义
- **智能降级**：当模型加载失败时，使用规则化方法生成摘要

### 3. 可视化辅助模块 (`visual_helper.py`)
- **引用关系图谱**：生成Mermaid格式的引用关系图
- **图表描述生成**：为论文中的图表生成结构化描述
- **经典论文识别**：自动标记经典论文，在图谱中突出显示

## 技术架构

### 依赖库
- `PyMuPDF` (fitz)：PDF文件解析
- `requests`：API调用
- `modelscope`（可选）：摘要生成模型
- `re`, `json`, `time`, `collections`：标准库

### 算法流程
1. **输入处理**：接收PDF文件（bytes或文件路径）
2. **文本提取**：逐页提取文本，进行章节结构化
3. **元数据获取**：调用ArXiv API补充论文元数据
4. **摘要生成**：基于结构化文本生成多粒度摘要
5. **关键词提取**：统计词频并结合专业术语知识库
6. **可视化生成**：创建引用图谱和图表描述
7. **结果输出**：返回统一格式的JSON结果

## 使用示例

### 基础API使用

```python
from paper_parser import parse_paper
from summary_generator import pack_summary_result
from visual_helper import generate_citation_graph, generate_figure_description

# 1. 解析PDF
parse_result = parse_paper("example_paper.pdf")

# 2. 生成摘要
summary_result = pack_summary_result(parse_result['text_data']['structured_text'])

# 3. 生成可视化数据
citation_graph = generate_citation_graph(parse_result['text_data']['structured_text'])
figure_descriptions = generate_figure_description(
    parse_result['text_data']['structured_text'],
    parse_result['text_data']['figures']
)

# 4. 获取结果
short_summary = summary_result['short_summary']
long_summary = summary_result['long_summary']['full_text']
keywords = summary_result['keywords']
mermaid_code = citation_graph['mermaid_code']
```

详细使用示例请参考 `example_usage.py`。

### 论文分析工具使用

```python
from paper_analyzer import PaperAnalyzer

# 创建分析器
analyzer = PaperAnalyzer()

# 分析论文
if analyzer.analyze_paper("example_paper.pdf"):
    # 生成短概要
    short_summary = analyzer.generate_short_summary()
    print("短概要：")
    print(short_summary)
    
    # 生成详细分析报告
    long_summary = analyzer.generate_long_summary()
    print("\n详细分析报告：")
    print(long_summary)
    
    # 保存结果
    analyzer.save_results("analysis_results")
```

命令行使用：
```bash
python paper_analyzer.py example_paper.pdf --output-dir analysis_results --mode both
```

## 核心API

### `parse_paper(pdf_input, arxiv_id=None, doi=None, title=None)`
- **功能**：完整的论文解析流程
- **参数**：
  - `pdf_input`：PDF输入（bytes或文件路径）
  - `arxiv_id`：ArXiv ID（可选）
  - `doi`：DOI编号（可选）
  - `title`：论文标题（可选）
- **返回**：包含文本数据、元数据的字典

### `pack_summary_result(structured_text)`
- **功能**：封装摘要结果
- **参数**：`structured_text`：结构化的论文文本
- **返回**：包含短摘要、长摘要、关键词的字典

### `generate_citation_graph(structured_text)`
- **功能**：生成引用关系图谱
- **参数**：`structured_text`：结构化的论文文本
- **返回**：包含Mermaid代码和参考文献列表的字典

### `generate_figure_description(structured_text, figures)`
- **功能**：为图表生成文本描述
- **参数**：
  - `structured_text`：结构化的论文文本
  - `figures`：图表信息列表
- **返回**：图表描述列表

## 性能指标

- **处理速度**：单篇论文解析≤20秒，摘要生成≤10秒
- **内存占用**：支持处理≤20MB的PDF文件
- **并发能力**：支持5人并发调用无卡顿
- **准确率**：摘要内容准确率≥80%，图表描述匹配度≥70%

## 错误处理

### 常见错误类型
1. **文件格式错误**：无法解析的PDF格式
2. **加密文件错误**：加密的PDF文件
3. **API调用失败**：ArXiv API超时或无结果
4. **模型加载失败**：modelscope未安装或模型加载失败

### 降级策略
- 文件解析失败时返回明确错误信息
- API调用失败时使用空元数据
- 模型加载失败时使用规则化摘要方法

## 测试与验证

运行测试用例：
```bash
python test_cases.py
```

测试覆盖：
- PDF解析功能（文本提取、章节识别、公式图表标记）
- 摘要生成功能（长短摘要、关键词提取）
- 可视化功能（引用图谱、图表描述）
- 异常处理（文件错误、API失败、模型加载失败）

## 部署说明

### 安装依赖
```bash
pip install PyMuPDF requests
# 可选：安装modelscope以使用高级摘要模型
pip install modelscope>=1.10.0
```

### 环境要求
- Python 3.7+
- PyMuPDF 1.18.0+
- requests 2.0.0+
- modelscope 1.10.0+（可选）

## 后续优化方向

1. **多语言支持**：扩展对中文、日文等多语言论文的支持
2. **模型优化**：接入更多预训练模型，提升摘要质量
3. **知识图谱**：构建论文知识图谱，支持论文间关联分析
4. **交互式可视化**：提供更丰富的可视化交互功能
5. **批量处理**：支持批量论文解析和对比分析

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系：算法工程师A