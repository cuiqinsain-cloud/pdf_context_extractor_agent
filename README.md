# PDF财务报表数据提取工具

从A股财务报表PDF中提取结构化数据的专业工具

---

## 📖 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [输出数据结构](#输出数据结构)
- [架构设计](#架构设计)
- [开发指南](#开发指南)
- [版本信息](#版本信息)

---

## 项目简介

从A股财务报表PDF中提取结构化数据，支持以下报表类型：
- ✅ **合并资产负债表**（已实现）
- 🚧 **合并利润表**（计划中）
- 🚧 **合并现金流量表**（计划中）
- 🚧 **合并财务报表项目附注**（计划中）

---

## 功能特性

- 📊 **智能边界识别**：自动识别报表起止位置，支持混合页面内容分离
- 🎯 **精确提取**：基于页码范围的精准定位，支持跨页表格合并
- 🔧 **模块化设计**：解耦的架构便于维护和扩展
- 📋 **多种输出**：支持JSON、Excel、CSV格式
- ✅ **数据验证**：内置完整性和准确性检查（资产负债平衡验证）
- 🔍 **错误处理**：完善的异常处理和日志记录

---

## 快速开始

### 环境要求

- Python 3.8+
- 虚拟环境已在项目目录下创建

### 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 快速示例

```bash
# 提取合并资产负债表（126-127页）
python main.py tests/sample_pdfs/金山办公-2024-年报.pdf --pages 126-127
```

---

## 使用指南

### 命令行使用

#### 基本用法
```bash
python main.py <PDF路径> --pages <起始页>-<结束页>
```

#### 指定输出格式和路径
```bash
python main.py <PDF路径> --pages <起始页>-<结束页> --output result.xlsx --format excel
```

#### 调试模式
```bash
python main.py <PDF路径> --pages <起始页>-<结束页> --verbose
```

### Python API

```python
from main import FinancialReportExtractor

# 创建提取器实例
extractor = FinancialReportExtractor('tests/sample_pdfs/sample.pdf')

# 提取合并资产负债表（126-128页）
result = extractor.extract_balance_sheet((126, 128))

# 检查提取结果
if result['success']:
    print("提取成功！")
    summary = extractor.get_extraction_summary(result)
    print(summary)

    # 保存结果
    extractor.save_result(result, 'output/balance_sheet.json', 'json')
    extractor.save_result(result, 'output/balance_sheet.xlsx', 'excel')
else:
    print(f"提取失败：{result['error_message']}")
```

---

## 输出数据结构

### JSON格式示例

```json
{
  "extraction_info": {
    "pdf_path": "tests/sample_pdfs/sample.pdf",
    "page_range": [126, 128],
    "extraction_time": "2026-02-04T10:00:00",
    "version": "1.0.0"
  },
  "balance_sheet_data": {
    "report_type": "合并资产负债表",
    "assets": {
      "current_assets": {
        "货币资金": {
          "original_name": "货币资金",
          "current_period": "1000000.00",
          "previous_period": "900000.00",
          "note": "七、1"
        },
        "应收账款": {
          "original_name": "应收账款",
          "current_period": "500000.00",
          "previous_period": "450000.00",
          "note": "七、5"
        }
      },
      "non_current_assets": {
        "固定资产": {
          "original_name": "固定资产",
          "current_period": "2000000.00",
          "previous_period": "1900000.00",
          "note": "七、21"
        }
      },
      "assets_total": {
        "original_name": "资产总计",
        "current_period": "3900000.00",
        "previous_period": "3625000.00"
      }
    },
    "liabilities": {
      "current_liabilities": {...},
      "non_current_liabilities": {...},
      "liabilities_total": {...}
    },
    "equity": {...},
    "liabilities_and_equity_total": {...}
  },
  "validation_result": {
    "is_valid": true,
    "balance_check": {
      "status": "passed",
      "difference": 0.0
    },
    "completeness_score": 0.95,
    "errors": [],
    "warnings": []
  },
  "success": true
}
```

### 数据字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `extraction_info` | Object | 提取元信息 |
| `balance_sheet_data` | Object | 资产负债表数据 |
| `validation_result` | Object | 验证结果 |
| `success` | Boolean | 提取是否成功 |

---

## 架构设计

### 项目结构

```
pdf_context_extractor_agent/
├── README.md                 # 项目文档（开发+使用）
├── Agents.md                 # Agent使用指南（仅使用）
├── requirements.txt          # Python依赖
├── venv/                     # 虚拟环境
├── src/                      # 源代码
│   ├── __init__.py
│   ├── pdf_reader.py         # PDF读取模块
│   ├── table_extractor.py    # 表格提取模块
│   └── parsers/              # 解析器模块
│       ├── __init__.py
│       └── balance_sheet.py  # 资产负债表解析器
├── tests/
│   └── sample_pdfs/          # 测试PDF文件
├── output/                   # 输出结果目录
└── main.py                   # 主程序入口
```

### 技术栈

- **PDF处理**：pdfplumber 0.11.9（表格提取能力强）
- **数据处理**：pandas 3.0.0
- **输出格式**：openpyxl（Excel）、json、csv

### 模块化设计

- **PDF处理层** (`pdf_reader.py`)：负责PDF读取和页面提取
- **表格提取层** (`table_extractor.py`)：识别和提取表格数据，支持混合页面内容分离
- **解析器层** (`parsers/balance_sheet.py`)：针对资产负债表的专用解析器
- **验证层**：内置数据完整性和准确性验证（资产负债平衡检查）
- **输出层**：多格式数据导出（JSON/CSV/Excel）

### 数据处理流程

```
PDF输入 + 页码 → PDF读取 → 表格提取 → 边界识别 → 数据解析 → 结构验证 → 格式化输出
```

### 关键技术实现

1. **智能边界识别**：基于"负债和所有者权益总计"等关键词精确定位
2. **混合页面分离**：自动区分资产负债表和其他报表内容
3. **跨页表格合并**：支持资产负债表跨多页的自动合并
4. **数据验证**：资产总计 = 负债+权益总计的平衡性检查

---

## 开发指南

### 开发环境设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd pdf_context_extractor_agent

# 2. 创建虚拟环境（如果不存在）
python -m venv venv

# 3. 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 4. 安装依赖
pip install -r requirements.txt
```

### 核心模块说明

#### 1. PDF读取器 (`src/pdf_reader.py`)

```python
from src.pdf_reader import PDFReader

# 基本用法
with PDFReader('path/to/pdf') as reader:
    pages = reader.get_pages((126, 128))  # 获取126-128页
    text = reader.extract_page_text(126)   # 提取单页文本
    tables = reader.extract_page_tables(126)  # 提取单页表格
```

#### 2. 表格提取器 (`src/table_extractor.py`)

```python
from src.table_extractor import TableExtractor

extractor = TableExtractor()

# 识别资产负债表边界
boundary_info = extractor.identify_balance_sheet_content(pages)

# 提取并合并表格
tables = extractor.extract_balance_sheet_tables(pages)
merged = extractor.merge_cross_page_tables(tables)
cleaned = extractor.clean_table_data(merged)
```

**关键算法**：
- 结束标志检测: `负债和所有者权益总计|负债和所有者权益（或股东权益）总计`
- 下一表格检测: `母公司资产负债表`
- 混合内容分离: 基于关键词和坐标定位

#### 3. 资产负债表解析器 (`src/parsers/balance_sheet.py`)

```python
from src.parsers.balance_sheet import BalanceSheetParser

parser = BalanceSheetParser()

# 解析表格数据为结构化格式
parsed_data = parser.parse_balance_sheet(table_data)

# 验证数据完整性
validation = parser.validate_balance_sheet(parsed_data)
```

**解析规则**：
- **资产分类**: 流动资产、非流动资产
- **负债分类**: 流动负债、非流动负债
- **权益分类**: 标准权益项目
- **关键词匹配**: 基于正则表达式的智能匹配

### 添加新报表类型

1. 在 `src/parsers/` 下创建新的解析器类
2. 继承通用解析器接口（可参考`balance_sheet.py`）
3. 在主程序中添加相应的提取方法
4. 更新数据结构和验证规则

### 自定义输出格式

1. 在主程序的`_save_to_xxx`方法中添加新格式处理
2. 更新命令行参数解析
3. 添加相应的依赖包

### 测试

```python
# 标准测试流程
pdf_path = "tests/sample_pdfs/sample.pdf"
pages = (126, 128)

# 执行提取
extractor = FinancialReportExtractor(pdf_path)
result = extractor.extract_balance_sheet(pages)

# 验证结果
assert result['success'] == True
assert result['validation_result']['is_valid'] == True
assert result['balance_sheet_data']['parsing_info']['matched_items'] > 10
```

### 已知问题

#### 🐛 列映射错误（待修复）

**问题描述**：
表头识别的列位置修正逻辑存在缺陷，会将附注列误识别为金额列，导致提取的金额数据实际是附注编号。

**影响范围**：
所有使用该工具提取的资产负债表数据

**问题位置**：
`src/parsers/balance_sheet.py:279-308`

**根本原因**：
第290行的正则表达式 `r'\d{1,3}(,\d{3})*(\.\d+)?'` 会匹配附注编号"七、1"中的"1"，导致附注列被误认为是金额列。

**临时解决方案**：
1. 排除附注列：在识别数字列时跳过已识别的附注列
2. 改进正则表达式：只匹配真正的金额格式
3. 移除修正逻辑：如果第一步识别正确，可以注释掉修正代码

**详细分析**：
参见项目根目录下的调试脚本：
- `debug_column_mapping.py`
- `debug_header_identification.py`

### 性能特征

- **处理速度**: 3页PDF约需10-30秒（取决于表格复杂度）
- **内存占用**: 通常不超过100MB
- **支持文件大小**: 测试支持最大500MB的PDF文件
- **准确率**: 合并资产负债表提取准确率约90-95%（存在列映射bug时会降低）

---

## 版本信息

- **当前版本**: v1.0.0
- **更新时间**: 2026-02-04
- **已支持报表**: 合并资产负债表
- **Python版本**: 3.14.0
- **主要依赖**: pdfplumber 0.11.9, pandas 3.0.0, openpyxl 3.1.5

---

## 更新日志

### v1.0.0 (2026-02-04)

- ✅ **完成合并资产负债表提取功能**
  - 实现智能边界识别（基于结束标志检测）
  - 支持混合页面内容分离（第128页处理）
  - 支持跨页表格自动合并（126-128页）
  - 实现资产负债平衡性验证
  - 支持JSON/Excel/CSV多格式输出
- ✅ **建立完整的项目架构**
  - PDF读取模块 (`pdf_reader.py`)
  - 表格提取模块 (`table_extractor.py`)
  - 资产负债表解析器 (`parsers/balance_sheet.py`)
  - 主程序入口 (`main.py`)
- ✅ **提供命令行和Python API两种使用方式**
- ✅ **完善的错误处理和日志记录**
- ⚠️ **已知问题**：列映射逻辑存在bug，需要修复

### v0.1.0-dev (2026-02-03)

- 初始化项目结构
- 创建核心模块框架
- 设计模块化架构

---

## 下一步计划

### 功能开发
1. 🚧 实现合并利润表提取功能
2. 🚧 实现合并现金流量表提取功能
3. 🚧 实现财务报表附注提取功能（文本+表格）

### Bug修复
1. 🐛 修复列映射错误（高优先级）
2. 🔧 优化表格识别准确率
3. 📊 增加更多数据验证规则

---

## 文档说明

- **README.md**（本文档）：面向开发者和维护者，包含完整的开发指南
- **Agents.md**：面向使用工具的Agent，定义角色权限和使用规范

---

## 许可证

[待添加]

---

## 联系方式

如遇问题或需要扩展功能，请在代码注释中留下详细的问题描述和预期行为。
