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
- 🚧 合并现金流量表（开发中）

**核心特性**：
- ✅ 动态列结构识别 - 自动适应不同格式
- ✅ 规则匹配 + LLM智能识别 - 混合识别方案
- ✅ 跨页支持 - 自动处理跨页表格
- ✅ 三层级平衡性验证 - 细粒度数据验证
- ✅ Excel导出 - 一键导出结构化数据

**当前版本**: v1.2.0-alpha

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

#### 解析现金流量表（开发中）

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

### 3. 批量处理

```bash
# 激活虚拟环境
source venv/bin/activate

# 导出资产负债表数据
python tools/export_to_excel.py

# 导出利润表数据
python tools/export_income_statement.py
```

## 📚 文档导航

- **[环境配置](docs/SETUP.md)** - 环境配置指南（虚拟环境、依赖安装、LLM配置）
- **[功能说明](docs/FEATURES.md)** - 详细功能介绍和使用方法
- **[开发进展](docs/DEVELOPMENT.md)** - 当前状态、已知问题、路线图
- **[技术架构](docs/ARCHITECTURE.md)** - 系统架构和核心技术

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
│       ├── cash_flow.py               # 现金流量表解析器（开发中）
│       ├── column_analyzer.py
│       ├── hybrid_column_analyzer.py  # 混合识别
│       └── llm_client.py              # LLM客户端
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

# 真实PDF测试 - 现金流量表（开发中）
python tests/test_cash_flow.py

# LLM集成测试
python tests/test_llm_integration.py
```

## 💡 常见问题

### Q: 为什么要使用虚拟环境？
A: 虚拟环境可以隔离项目依赖，避免与系统Python包冲突。本项目所有命令都需要在虚拟环境中执行。

### Q: 如何启用LLM功能？
A: 参考 [LLM配置指南](docs/guides/llm_config.md) 进行配置。

### Q: 测试数据在哪里？
A: 测试PDF文件位于 `tests/sample_pdfs/` 目录。

## 📧 联系方式

项目路径: `/Users/qin.cui/Project/fr_beta04/pdf_context_extractor_agent`

---

**最后更新**: 2026-02-06 | **版本**: v1.2.0-alpha
