# PDF财务报表数据提取工具

> 基于AI的PDF财务报表智能解析系统，专注于A股上市公司年报数据提取

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## 📋 项目简介

专业的PDF财务报表数据提取工具，能够从A股上市公司年报PDF中自动提取和解析财务报表数据。

**支持的报表类型**：
- ✅ 合并资产负债表
- ✅ 合并利润表
- ✅ 合并现金流量表
- ✅ 合并财务报表项目注释（标题+内容+表格）

**核心特性**：
- ✅ 动态列结构识别 - 自动适应不同格式
- ✅ 规则匹配 + LLM智能识别 - 混合识别方案
- ✅ 跨页支持 - 自动处理跨页表格
- ✅ 三层级平衡性验证 - 细粒度数据验证
- ✅ Excel导出 - 一键导出结构化数据
- ✅ 财务科目标准化 - 使用标准中文财务科目名称
- ✅ 注释章节智能提取 - 基于LLM的标题+内容+表格提取
- 🚀 批量处理优化 - 性能提升2.2倍，成本降低80%

**当前版本**: v1.4.0

## 🚀 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd pdf_context_extractor_agent

# 创建并激活虚拟环境（重要！）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

**⚠️ 重要**: 本项目使用虚拟环境，所有命令都需要在激活虚拟环境后执行。

### 2. 基本使用

#### 解析资产负债表

```python
from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser

# 读取PDF并提取表格
with PDFReader('path/to/annual_report.pdf') as pdf_reader:
    table_extractor = TableExtractor()
    pages = pdf_reader.get_pages((89, 91))
    tables = table_extractor.extract_tables_from_pages(pages)

    # 解析资产负债表
    parser = BalanceSheetParser()
    merged_data = []
    for table_dict in tables:
        merged_data.extend(table_dict['data'])

    result = parser.parse_balance_sheet(merged_data)
```

#### 解析利润表

```python
from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.income_statement import IncomeStatementParser

# 读取PDF并提取表格
with PDFReader('path/to/annual_report.pdf') as pdf_reader:
    table_extractor = TableExtractor()
    pages = pdf_reader.get_pages((93, 95))
    tables = table_extractor.extract_tables_from_pages(pages)

    # 解析利润表
    parser = IncomeStatementParser()
    merged_data = []
    for table_dict in tables:
        merged_data.extend(table_dict['data'])

    result = parser.parse_income_statement(merged_data)
```

#### 解析现金流量表

```python
from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.cash_flow import CashFlowParser

# 读取PDF并提取表格
with PDFReader('path/to/annual_report.pdf') as pdf_reader:
    table_extractor = TableExtractor()
    pages = pdf_reader.get_pages((96, 97))
    tables = table_extractor.extract_tables_from_pages(pages)

    # 解析现金流量表
    parser = CashFlowParser()
    merged_data = []
    for table_dict in tables:
        merged_data.extend(table_dict['data'])

    result = parser.parse_cash_flow(merged_data)
```

#### 提取财务报表注释（批量处理 - 推荐）

**方法1: 使用命令行脚本（最简单）**

```bash
# 激活虚拟环境
source venv/bin/activate

# 提取福耀玻璃年报注释（125-174页）
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174

# 提取深信服年报注释（162-199页）
python scripts/extract_full_notes.py \
    data/深信服2024年年度报告.pdf \
    162 199

# 自定义输出路径
python scripts/extract_full_notes.py \
    data/report.pdf 125 174 \
    -o output/custom_output.json
```

**性能优势**:
- ⚡ 速度提升2.2倍（27.6秒/页 vs 60秒/页）
- 💰 成本降低80%（批量调用LLM）
- ✅ 成功率100%
- 📊 完整提取标题、文本和表格

**方法2: 使用Python API**

```python
from src.parsers.batch_notes_extractor import BatchNotesExtractor
from src.parsers.config_loader import load_llm_config

# 加载配置
config = load_llm_config()

# 创建批量提取器
extractor = BatchNotesExtractor(
    provider=config['provider'],
    model=config['model'],
    api_key=config.get('api_key'),
    base_url=config.get('base_url')
)

# 批量提取（5页/批次，自动优化）
result = extractor.extract_notes_batch(
    pdf_path='data/福耀玻璃2024年年度报告.pdf',
    start_page=125,
    end_page=174,
    batch_size=5  # 推荐配置
)

# 查看结果
print(f"提取的注释数量: {result['total_notes']}")
print(f"包含表格的注释: {sum(1 for n in result['notes'] if n.get('has_table'))}")

# 保存结果
import json
with open('output/notes_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

**详细文档**:
- [批量提取使用指南](docs/full_extraction_guide.md)
- [性能测试报告](docs/batch_extraction_report.md)
- [工作总结](docs/BATCH_EXTRACTION_SUMMARY.md)

### 3. 批量导出（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate

# 一次性导出所有公司的三张报表
python tools/export_all_statements.py
```

**输出**：
- 每个公司生成一个Excel文件
- 包含3个工作表：资产负债表、利润表、现金流量表
- 使用标准中文财务科目名称（货币资金、营业收入、经营活动现金流量净额等）
- 文件保存在 `output/` 目录
- 文件命名：`{公司名}_三表合一_{时间戳}.xlsx`

### 4. 单独导出

如果只需要导出特定报表：

```bash
# 激活虚拟环境
source venv/bin/activate

# 导出资产负债表数据
python tools/export_to_excel.py

# 导出利润表数据
python tools/export_income_statement.py
```

## 📚 文档导航

### 核心文档
- **[环境配置](docs/SETUP.md)** - 环境配置指南（虚拟环境、依赖安装、LLM配置）
- **[功能说明](docs/FEATURES.md)** - 详细功能介绍和使用方法
- **[开发进展](docs/DEVELOPMENT.md)** - 当前状态、已知问题、路线图
- **[技术架构](docs/ARCHITECTURE.md)** - 系统架构和核心技术

### 批量提取文档（新）
- **[批量提取使用指南](docs/full_extraction_guide.md)** - 完整的使用说明和最佳实践
- **[性能测试报告](docs/batch_extraction_report.md)** - 详细的性能测试数据
- **[工作总结](docs/BATCH_EXTRACTION_SUMMARY.md)** - 批量提取优化工作总结

历史文档归档在 `docs/archive/` 目录

## 📁 项目结构

```
pdf_context_extractor_agent/
├── README.md                # 项目入口（本文件）
├── requirements.txt         # 项目依赖
├── venv/                    # 虚拟环境（需创建）
│
├── src/                     # 源代码
│   ├── pdf_reader.py
│   ├── table_extractor.py
│   └── parsers/             # 解析器模块
│       ├── balance_sheet.py           # 资产负债表解析器
│       ├── income_statement.py        # 利润表解析器
│       ├── cash_flow.py               # 现金流量表解析器
│       ├── notes_extractor.py         # 注释提取器
│       ├── batch_notes_extractor.py   # 批量注释提取器（新）
│       ├── column_analyzer.py
│       ├── hybrid_column_analyzer.py  # 混合识别
│       └── llm_client.py              # LLM客户端
│
├── scripts/                 # 脚本工具
│   └── extract_full_notes.py          # 完整文档注释提取脚本（新）
│
├── tests/                   # 测试文件
├── tools/                   # 工具脚本
├── config/                  # 配置文件
├── output/                  # 输出文件
└── docs/                    # 文档
```

## 🧪 运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 单元测试
python tests/test_column_analyzer.py

# 集成测试
python tests/test_integration.py

# 真实PDF测试 - 资产负债表
python tests/test_real_pdf.py

# 真实PDF测试 - 利润表
python tests/test_income_statement.py

# 真实PDF测试 - 现金流量表
python tests/test_cash_flow.py

# LLM集成测试
python tests/test_llm_integration.py

# 批量注释提取测试
python tests/test_batch_notes_extractor.py
```

## 💡 常见问题

### Q: 为什么要使用虚拟环境？
A: 虚拟环境可以隔离项目依赖，避免与系统Python包冲突。本项目所有命令都需要在虚拟环境中执行。

### Q: 如何启用LLM功能？
A: 参考 [LLM配置指南](docs/guides/llm_config.md) 进行配置。

### Q: 测试数据在哪里？
A: 测试PDF文件位于 `tests/sample_pdfs/` 目录。

### Q: 批量提取和逐页提取有什么区别？
A: 批量提取将多页合并处理，性能提升2.2倍，成本降低80%。推荐使用批量提取（5页/批次）。详见[性能测试报告](docs/batch_extraction_report.md)。

### Q: 如何处理大文档（50+页）？
A: 使用 `scripts/extract_full_notes.py` 脚本，自动分批处理，支持断点续传。详见[使用指南](docs/full_extraction_guide.md)。

## 📧 联系方式

项目路径: `/Users/qin.cui/Project/fr_beta04/pdf_context_extractor_agent`

---

**最后更新**: 2026-02-06 | **版本**: v1.4.0

## 🎉 最新更新 (v1.4.0)

### 批量提取优化
- ✅ 实现批量处理方法，性能提升2.2倍
- ✅ LLM调用减少80%，大幅降低成本
- ✅ 完整提取标题、文本和表格内容
- ✅ 提供命令行脚本，开箱即用
- ✅ 完整的文档和测试

**性能对比**:
| 方法 | 速度 | LLM调用(50页) | 成本 |
|------|------|---------------|------|
| 逐页处理 | 60秒/页 | 50次 | ¥0.50 |
| **批量处理** | **27.6秒/页** | **10次** | **¥0.10** |
| **提升** | **2.2x** | **5x** | **80%↓** |

详见: [批量提取工作总结](docs/BATCH_EXTRACTION_SUMMARY.md)
