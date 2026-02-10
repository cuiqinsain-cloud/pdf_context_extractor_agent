# PDF财务报表数据提取工具

> 基于AI的PDF财务报表智能解析系统，专注于A股上市公司年报数据提取

[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)](https://github.com)
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

详细配置说明请参考 [环境配置文档](docs/SETUP.md)。

### 2. 基本使用

#### 解析三大财务报表

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

支持的解析器：
- `BalanceSheetParser()` - 资产负债表
- `IncomeStatementParser()` - 利润表
- `CashFlowParser()` - 现金流量表

#### 提取财务报表注释（批量处理）

```bash
# 激活虚拟环境
source venv/bin/activate

# 提取年报注释（批量处理，性能提升2.2倍）
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174

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

#### 导出Excel报表

```bash
# 激活虚拟环境
source venv/bin/activate

# 一次性导出所有公司的三张报表
python tools/export_all_statements.py

# 将提取的注释导出为Excel文件
python tools/export_notes_to_excel.py \
    output/notes_full.json \
    -c 福耀玻璃 \
    -o output/福耀玻璃_财务报表注释.xlsx
```

**Excel文件特性**：
- 包含3个工作表：资产负债表、利润表、现金流量表
- 使用标准中文财务科目名称
- 完整的格式化样式（颜色、字体、边框）
- 自动筛选、冻结窗格、斑马纹

### 3. Python API

```python
from src.parsers.batch_notes_extractor import BatchNotesExtractor
from src.parsers.config_loader import ConfigLoader

# 加载配置
config_loader = ConfigLoader()
config = config_loader.load_config()
llm_config = config['llm_api']

# 创建批量提取器
extractor = BatchNotesExtractor(llm_config, batch_size=5)

# 批量提取（5页/批次，推荐配置）
with PDFReader('data/report.pdf') as pdf_reader:
    pages = pdf_reader.get_pages((125, 174))
    result = extractor.extract_notes_from_pages_batch(
        pages,
        start_page_num=125
    )

# 查看结果
print(f"提取的注释数量: {result['total_notes']}")
print(f"包含表格的注释: {sum(1 for n in result['notes'] if n.get('has_table'))}")
```

## 📚 文档导航

### 核心文档
- **[环境配置](docs/SETUP.md)** - 环境配置、依赖安装、LLM配置
- **[功能说明](docs/FEATURES.md)** - 完整功能介绍、使用指南、性能数据
- **[技术架构](docs/ARCHITECTURE.md)** - 系统架构和核心技术
- **[开发进展](docs/DEVELOPMENT.md)** - 开发状态、版本历史、性能指标

### 查看历史版本

```bash
# 查看版本历史
git log --oneline

# 查看特定版本更新
git show v1.5.0
```

历史文档归档在 `docs/archive/` 目录。

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
│       ├── batch_notes_extractor.py   # 批量注释提取器
│       ├── column_analyzer.py         # 动态列识别
│       └── llm_client.py              # LLM客户端
│
├── scripts/                 # 脚本工具
│   └── extract_full_notes.py          # 注释提取脚本
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

# 真实PDF测试
python tests/test_real_pdf.py              # 资产负债表
python tests/test_income_statement.py      # 利润表
python tests/test_cash_flow.py             # 现金流量表

# 批量注释提取测试
python tests/test_batch_extractor.py
```

## 💡 常见问题

### Q: 为什么要使用虚拟环境？
A: 虚拟环境可以隔离项目依赖，避免与系统Python包冲突。本项目所有命令都需要在虚拟环境中执行。

### Q: 如何启用LLM功能？
A: 参考 [环境配置文档](docs/SETUP.md) 的LLM配置章节进行配置。

### Q: 测试数据在哪里？
A: 测试PDF文件位于 `tests/sample_pdfs/` 目录。

### Q: 批量提取和逐页提取有什么区别？
A: 批量提取将多页合并处理，性能提升2.2倍，成本降低80%。推荐使用批量提取（5页/批次）。详见 [功能说明文档](docs/FEATURES.md)。

### Q: 如何处理大文档（50+页）？
A: 使用 `scripts/extract_full_notes.py` 脚本，自动分批处理。详见 [功能说明文档](docs/FEATURES.md)。

### Q: 支持哪些表头格式？
A: 支持期末/期初、本期末/上期末、年末/年初、日期格式等多种表头格式。系统会自动识别并处理。详见 [功能说明文档](docs/FEATURES.md)。

## 📧 联系方式

项目路径: `/Users/qin.cui/Project/fr_beta04/pdf_context_extractor_agent`

---

**当前版本**: v1.5.0
**最后更新**: 2026-02-10
