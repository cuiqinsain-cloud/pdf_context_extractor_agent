# 项目结构说明

本文档描述项目的目录结构和文件组织。

## 目录树

```
pdf_context_extractor_agent/
├── README.md                    # 项目主页 - 从这里开始 ⭐
├── main.py                      # 主程序入口
├── requirements.txt             # Python依赖包
├── PROJECT_STRUCTURE.md         # 本文件 - 项目结构说明
│
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── pdf_reader.py           # PDF读取器
│   ├── table_extractor.py      # 表格提取器
│   └── parsers/                # 解析器模块
│       ├── __init__.py
│       ├── balance_sheet.py    # 资产负债表解析器
│       ├── column_analyzer.py  # 动态列结构分析器 ⭐ 核心创新
│       └── llm_assistant.py    # LLM辅助模块（待完善）
│
├── tests/                       # 测试目录
│   ├── test_column_analyzer.py # 单元测试 - ColumnAnalyzer
│   ├── test_integration.py     # 集成测试 - 验证集成效果
│   ├── test_real_pdf.py        # 真实PDF测试 - 4家公司年报
│   ├── test_bug_fix.py         # Bug修复测试
│   ├── debug_regex.py          # 调试脚本
│   └── sample_pdfs/            # 测试用PDF文件
│       ├── 福耀玻璃：福耀玻璃2024年年度报告.pdf
│       ├── 海尔智家：海尔智家股份有限公司2024年年度报告.pdf
│       ├── 海天味业：海天味业2024年年度报告.pdf
│       └── 金山办公-2024-年报.pdf
│
├── tools/                       # 工具脚本目录
│   └── export_to_excel.py      # Excel导出工具
│
├── output/                      # 输出文件目录
│   └── balance_sheet_results_*.xlsx  # 生成的Excel文件
│
├── examples/                    # 示例代码目录
│   └── enhanced_parser_example.py    # 增强解析器示例
│
└── docs/                        # 文档目录
    ├── README.md               # 文档索引 ⭐
    ├── design/                 # 设计文档
    │   ├── parser_optimization.md  # 列结构分析器设计 ⭐ 核心技术
    │   └── agents.md               # Agent权限定义
    └── reports/                # 测试和进展报告
        ├── test_report.md          # 单元测试报告
        ├── integration_notes.md    # 集成测试说明
        ├── real_pdf_test_report.md # 真实PDF测试报告
        └── progress_report.md      # 项目进展报告 ⭐ 当前状态
```

## 核心文件说明

### 源代码 (src/)

| 文件 | 说明 | 重要性 |
|------|------|--------|
| `pdf_reader.py` | PDF文件读取，提供页面对象 | ⭐⭐⭐ |
| `table_extractor.py` | 从PDF页面提取表格数据 | ⭐⭐⭐ |
| `parsers/balance_sheet.py` | 资产负债表解析器，已集成ColumnAnalyzer | ⭐⭐⭐⭐ |
| `parsers/column_analyzer.py` | **动态列结构分析器** - 核心创新 | ⭐⭐⭐⭐⭐ |
| `parsers/llm_assistant.py` | LLM辅助模块（框架已实现，API待集成） | ⭐⭐ |

### 测试文件 (tests/)

| 文件 | 说明 | 运行命令 |
|------|------|---------|
| `test_column_analyzer.py` | ColumnAnalyzer单元测试（7个测试用例） | `python tests/test_column_analyzer.py` |
| `test_integration.py` | 集成测试（3个测试用例） | `python tests/test_integration.py` |
| `test_real_pdf.py` | 真实PDF测试（4家公司） | `python tests/test_real_pdf.py` |

### 工具脚本 (tools/)

| 文件 | 说明 | 运行命令 |
|------|------|---------|
| `export_to_excel.py` | 导出解析结果到Excel | `python tools/export_to_excel.py` |

### 文档 (docs/)

| 文件 | 说明 | 适合 |
|------|------|------|
| `README.md` | 文档索引 | 所有人 |
| `design/parser_optimization.md` | 核心技术设计文档 | 开发者 ⭐ |
| `design/agents.md` | 系统架构说明 | 架构师 |
| `reports/test_report.md` | 单元测试报告 | 测试人员 |
| `reports/integration_notes.md` | 集成说明 | 开发者 |
| `reports/real_pdf_test_report.md` | 真实PDF测试报告 | 所有人 |
| `reports/progress_report.md` | 项目进展报告 | 所有人 ⭐ |

## 快速导航

### 我想...

**了解项目**
→ [README.md](README.md)

**理解核心技术**
→ [docs/design/parser_optimization.md](docs/design/parser_optimization.md)

**查看当前进展**
→ [docs/reports/progress_report.md](docs/reports/progress_report.md)

**运行测试**
→ 查看上面的"测试文件"表格

**导出Excel**
→ `python tools/export_to_excel.py`

**查看测试结果**
→ [docs/reports/real_pdf_test_report.md](docs/reports/real_pdf_test_report.md)

## 文件命名规范

- **源代码**: 小写+下划线 (snake_case)
  - 例如: `column_analyzer.py`, `balance_sheet.py`

- **测试文件**: `test_` 前缀
  - 例如: `test_column_analyzer.py`

- **文档文件**: 小写+下划线，使用描述性名称
  - 例如: `parser_optimization.md`, `progress_report.md`

- **输出文件**: 描述性名称+时间戳
  - 例如: `balance_sheet_results_20260204_185245.xlsx`

## 目录用途

| 目录 | 用途 | 提交到Git |
|------|------|----------|
| `src/` | 源代码 | ✅ 是 |
| `tests/` | 测试代码和测试数据 | ✅ 是 |
| `tools/` | 工具脚本 | ✅ 是 |
| `docs/` | 文档 | ✅ 是 |
| `examples/` | 示例代码 | ✅ 是 |
| `output/` | 生成的输出文件 | ❌ 否（.gitignore） |
| `venv/` | Python虚拟环境 | ❌ 否（.gitignore） |
| `__pycache__/` | Python缓存 | ❌ 否（.gitignore） |

## 依赖关系

```
main.py
  └─> src/pdf_reader.py
  └─> src/table_extractor.py
  └─> src/parsers/balance_sheet.py
        └─> src/parsers/column_analyzer.py ⭐
        └─> src/parsers/llm_assistant.py (可选)
```

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v1.0.0 | 2026-02-04 | 实现动态列结构识别，集成到BalanceSheetParser |
| v0.1.0 | 之前 | 初始版本，硬编码列识别 |

---

**最后更新**: 2026-02-04
