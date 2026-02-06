# 功能说明

本文档详细介绍项目的各项功能和使用方法。

---

## 一、核心功能

### 1.1 PDF读取和表格提取

**功能描述**：
- 读取PDF文件并提取指定页面
- 自动识别表格区域
- 提取表格数据为结构化格式

**使用方法**：
```python
from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor

with PDFReader('path/to/pdf') as pdf_reader:
    table_extractor = TableExtractor()
    pages = pdf_reader.get_pages((89, 91))  # 页码范围
    tables = table_extractor.extract_tables_from_pages(pages)
```

### 1.2 动态列结构识别

**功能描述**：
- 自动识别表头列结构
- 支持任意列数和格式
- 智能缓存机制

**核心技术**：
- 关键字匹配
- 特征推断
- 缓存验证

**使用方法**：
```python
from src.parsers.column_analyzer import ColumnAnalyzer

analyzer = ColumnAnalyzer()
header_row = ['项目', '附注', '期末', '期初']
column_map = analyzer.analyze_row_structure(header_row)
```

### 1.3 资产负债表解析

**功能描述**：
- 解析合并资产负债表
- 自动分类资产、负债、所有者权益
- 数据验证和平衡性检查

**使用方法**：
```python
from src.parsers.balance_sheet import BalanceSheetParser

parser = BalanceSheetParser()
result = parser.parse_balance_sheet(table_data)

# 访问结果
assets = result['assets']
liabilities = result['liabilities']
equity = result['equity']
```

### 1.4 LLM智能识别（新功能）

**功能描述**：
- 规则匹配 + LLM智能识别的混合方案
- 结果对比和用户选择
- 支持多种LLM provider

**工作流程**：
```
规则匹配 → LLM识别 → 结果对比 → 决策:
  ├─ 一致 → 自动使用
  └─ 不一致 → 用户选择
```

**使用方法**：
```python
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer

# 创建混合分析器（自动加载配置）
analyzer = HybridColumnAnalyzer()

# 分析表头
result = analyzer.analyze_row_structure(header_row)
```

**配置要求**：
- 配置文件：`config/llm_config.json`
- 环境变量：`export LLM_API_KEY='your_key'`
- 详见：[LLM配置指南](guides/llm_config.md)

---

## 二、数据导出

### 2.1 综合导出工具（推荐）

**功能描述**：
- 一次性导出三张报表（资产负债表、利润表、现金流量表）
- 批量处理多个公司
- 使用标准中文财务科目名称
- 自动生成带时间戳的文件

**使用方法**：
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行综合导出工具
python tools/export_all_statements.py
```

**输出文件**：
- 位置：`output/{公司名}_三表合一_{时间戳}.xlsx`
- 结构：每个公司一个Excel文件，包含3个工作表
  - 资产负债表
  - 利润表
  - 现金流量表
- 列结构：公司、类别、项目、本期金额、上期金额、附注

**财务科目标准化**：
- 资产负债表：货币资金、应收账款、固定资产、长期股权投资等
- 利润表：营业收入、营业成本、销售费用、管理费用、净利润等
- 现金流量表：销售商品、提供劳务收到的现金、经营活动产生的现金流量净额等

### 2.2 单独导出工具

**功能描述**：
- 单独导出特定报表
- 适用于只需要某一张报表的场景

**使用方法**：
```bash
# 激活虚拟环境
source venv/bin/activate

# 导出资产负债表
python tools/export_to_excel.py

# 导出利润表
python tools/export_income_statement.py
```

**输出文件**：
- 位置：`output/balance_sheet_results_*.xlsx` 或 `output/income_statement_results_*.xlsx`
- 内容：
  - 汇总统计表
  - 各公司完整数据
  - 未匹配项目汇总

---

## 三、支持的表头格式

### 3.1 标准格式

| 格式类型 | 示例 | 支持状态 |
|---------|------|---------|
| 期末/期初 | 期末、期初 | ✅ |
| 本期/上期 | 本期末、上期末 | ✅ |
| 年份格式 | 本年末、上年末 | ✅ |
| 日期格式 | 2024年12月31日 | ✅ |
| 带空格日期 | 2024 年12月 31日 | ✅ (LLM) |

### 3.2 列数支持

- ✅ 3列格式：项目、期末、期初
- ✅ 4列格式：项目、附注、期末、期初
- ✅ 多列格式：自动识别（如11列）
- ✅ 跨页列数变化：自动适应

---

## 四、数据验证

### 4.1 平衡性检查

**验证规则**：
```
资产总计 = 负债总计 + 所有者权益总计
```

**使用方法**：
```python
result = parser.parse_balance_sheet(table_data)
validation = result['validation']

if validation['balance_check']:
    print("✓ 平衡性检查通过")
```

### 4.2 完整性检查

**检查项目**：
- 必填项目是否存在
- 数据格式是否正确
- 未匹配项目比例

---

## 五、测试功能

### 5.1 单元测试

**测试内容**：
- ColumnAnalyzer 功能测试
- 各种表头格式测试
- 缓存机制测试

**运行方法**：
```bash
python tests/test_column_analyzer.py
```

### 5.2 集成测试

**测试内容**：
- 完整流程测试
- 跨页处理测试
- 多格式兼容性测试

**运行方法**：
```bash
python tests/test_integration.py
```

### 5.3 真实PDF测试

**测试数据**：
- 福耀玻璃 2024年报
- 海尔智家 2024年报
- 海天味业 2024年报
- 金山办公 2024年报

**运行方法**：
```bash
python tests/test_real_pdf.py
```

### 5.4 LLM集成测试

**测试内容**：
- LLM API连接测试
- 混合识别流程测试
- 用户选择界面测试

**运行方法**：
```bash
python tests/test_llm_integration.py
```

---

## 六、性能特性

### 6.1 智能缓存

**工作原理**：
1. 首次分析：完整的列结构识别
2. 快速验证：检查列数是否变化
3. 自动失效：列数变化时重新分析

**性能提升**：
- 大部分行只需检查列数
- 避免重复的复杂分析

### 6.2 批量处理

**特性**：
- 支持批量处理多个PDF
- 自动生成汇总报告
- 并行处理（计划中）

---

## 七、扩展性

### 7.1 添加新的报表类型

**步骤**：
1. 创建新的解析器类
2. 继承或参考 `BalanceSheetParser`
3. 使用 `ColumnAnalyzer` 进行列识别
4. 添加测试用例

**示例**：
```python
class IncomeStatementParser:
    def __init__(self):
        self.column_analyzer = ColumnAnalyzer()

    def parse_income_statement(self, table_data):
        # 实现解析逻辑
        pass
```

### 7.2 扩展关键字库

**位置**：`src/parsers/column_analyzer.py`

**方法**：
```python
self.column_keywords = {
    ColumnType.CURRENT_PERIOD: [
        r'期末', r'本期末', r'本年末',
        r'你的新关键字',  # 添加这里
    ],
}
```

### 7.3 添加新的LLM Provider

**位置**：`src/parsers/llm_client.py`

**方法**：
1. 在 `ProviderType` 枚举中添加新类型
2. 实现对应的 API 调用方法
3. 更新配置文件模板

---

## 八、限制和注意事项

### 8.1 当前限制

- ✅ 支持合并资产负债表
- ✅ 支持合并利润表
- ✅ 支持合并现金流量表
- ⚠️ 部分特殊格式需要LLM辅助
- ⚠️ 不支持图片格式的表格
- ⚠️ 不支持所有者权益变动表（计划中）

### 8.2 使用注意事项

1. **虚拟环境**：必须在虚拟环境中运行
2. **PDF质量**：PDF需要是文本格式，不能是扫描件
3. **页码范围**：需要准确指定表格所在页码
4. **LLM配置**：使用LLM功能需要正确配置API

---

**最后更新**: 2026-02-06
