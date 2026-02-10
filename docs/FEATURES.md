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

### 1.3 财务报表解析

#### 资产负债表解析

**功能描述**：
- 解析合并资产负债表
- 自动分类资产、负债、所有者权益
- 三层级数据验证和平衡性检查

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

#### 利润表解析

**功能描述**：
- 解析合并利润表
- 自动分类营业收入、成本、利润等
- 三层级验证机制

**使用方法**：
```python
from src.parsers.income_statement import IncomeStatementParser

parser = IncomeStatementParser()
result = parser.parse_income_statement(table_data)
```

#### 现金流量表解析

**功能描述**：
- 解析合并现金流量表
- 自动分类经营/投资/筹资活动
- 三层级验证机制

**使用方法**：
```python
from src.parsers.cash_flow import CashFlowParser

parser = CashFlowParser()
result = parser.parse_cash_flow(table_data)
```

### 1.4 LLM智能识别

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

---

## 二、财务报表注释提取（批量处理）

### 2.1 批量提取功能

**功能描述**：
- 智能提取财务报表注释章节的标题和内容
- 批量处理多页文档，性能提升2.2倍
- 自动提取文本、表格和层级结构
- 成本降低80%（LLM调用减少）

**核心特性**：
- ✅ 标题识别（一级/二级标题）
- ✅ 内容提取（文本+表格）
- ✅ 层级结构（父子关系）
- ✅ 位置感知表格分配
- ✅ 批量处理优化（5页/批次）

### 2.2 使用方法

#### 命令行方式（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate

# 提取福耀玻璃年报注释（125-174页）
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174

# 自定义输出路径
python scripts/extract_full_notes.py \
    data/report.pdf 125 174 \
    -o output/notes_full.json

# 自定义批次大小
python scripts/extract_full_notes.py \
    data/report.pdf 125 174 \
    -b 3  # 使用3页/批次
```

#### Python API方式

```python
from src.parsers.batch_notes_extractor import BatchNotesExtractor
from src.parsers.config_loader import ConfigLoader

# 加载配置
config_loader = ConfigLoader()
config = config_loader.load_config()
llm_config = config['llm_api']

# 创建批量提取器
extractor = BatchNotesExtractor(llm_config, batch_size=5)

# 批量提取
with PDFReader(pdf_path) as pdf_reader:
    pages = pdf_reader.get_pages((125, 174))
    result = extractor.extract_notes_from_pages_batch(
        pages,
        start_page_num=125
    )

# 查看结果
print(f"提取注释数: {result['total_notes']}")
```

### 2.3 输出格式

**JSON结构**：
```json
{
  "success": true,
  "notes": [
    {
      "number": "1",
      "level": 1,
      "title": "货币资金",
      "full_title": "1、 货币资金",
      "page_num": 125,
      "content": {
        "text": "文本内容...",
        "tables": [[["列1", "列2"], ["数据1", "数据2"]]],
        "table_count": 1
      },
      "has_table": true,
      "is_complete": true
    }
  ],
  "total_pages": 50,
  "total_notes": 120,
  "errors": []
}
```

### 2.4 性能指标

| 指标 | 逐页处理 | 批量处理 | 提升 |
|------|----------|----------|------|
| 处理速度 | 60秒/页 | 27.6秒/页 | **2.2x** |
| LLM调用（50页） | 50次 | 10次 | **5x** |
| API成本 | 基准 | -80% | **节省80%** |
| 成功率 | 高 | 100% | 稳定 |

**推荐配置**: 5页/批次（默认），性能和稳定性最佳平衡

### 2.5 批次大小选择

| 批次大小 | 优点 | 缺点 | 适用场景 |
|----------|------|------|----------|
| 3页 | 稳定性最高 | 速度较慢 | 网络不稳定时 |
| **5页** | **平衡最优** | - | **推荐默认** |
| 10页 | 速度最快 | 可能超时 | 网络极好时 |

---

## 三、Excel导出功能

### 3.1 财务报表Excel导出

#### 综合导出工具（推荐）

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

#### 单独导出工具

**使用方法**：
```bash
# 导出资产负债表
python tools/export_to_excel.py

# 导出利润表
python tools/export_income_statement.py
```

### 3.2 注释Excel导出

**功能描述**：
- 将批量提取的注释数据导出为格式化Excel文件
- 目录sheet：一级标题概览
- 内容sheet：每个一级标题独立sheet
- 完整格式化（颜色、字体、边框、对齐）

**使用方法**：
```bash
# 导出注释到Excel
python tools/export_notes_to_excel.py \
    output/notes_full.json \
    -c 福耀玻璃 \
    -o output/福耀玻璃_财务报表注释.xlsx
```

**Excel文件结构**：

#### Sheet 1: 目录
- 所有一级标题概览
- 列：序号、标题、页码、子项数量、表格数量、工作表名称
- 特性：冻结首行、自动筛选、斑马纹样式

#### Sheet 2-N: 内容工作表
- 命名规则：`{序号}_{标题}`（如"1_货币资金"）
- 区域1：标题信息区（注释标题、页码、层级、表格数量）
- 区域2：内容区（层级、标题、页码、内容）
- 区域3：表格区（格式化的财务表格）

**样式设计**：
- 字体：微软雅黑
- 颜色方案：蓝色主题（目录）、绿色主题（内容）
- 特性：冻结窗格、自动换行、对齐优化

**性能指标**：
- 处理速度：~5秒/10个注释
- 文件大小：~20KB/10个注释
- 无限制支持任意数量的注释和表格

---

## 四、支持的表头格式

### 4.1 标准格式

| 格式类型 | 示例 | 支持状态 |
|---------|------|---------|
| 期末/期初 | 期末、期初 | ✅ |
| 本期/上期 | 本期末、上期末 | ✅ |
| 年份格式 | 本年末、上年末 | ✅ |
| 日期格式 | 2024年12月31日 | ✅ |
| 带空格日期 | 2024 年12月 31日 | ✅ (LLM) |

### 4.2 列数支持

- ✅ 3列格式：项目、期末、期初
- ✅ 4列格式：项目、附注、期末、期初
- ✅ 多列格式：自动识别（如11列）
- ✅ 跨页列数变化：自动适应

---

## 五、数据验证

### 5.1 平衡性检查

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

### 5.2 完整性检查

**检查项目**：
- 必填项目是否存在
- 数据格式是否正确
- 未匹配项目比例

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

### 6.2 批量处理优化

**特性**：
- 支持批量处理多页文档
- 自动分批调用LLM
- 结果自动合并
- 错误处理和重试机制

---

## 七、扩展性

### 7.1 添加新的报表类型

**步骤**：
1. 创建新的解析器类
2. 继承或参考现有解析器
3. 使用 `ColumnAnalyzer` 进行列识别
4. 添加测试用例

**示例**：
```python
class NewStatementParser:
    def __init__(self):
        self.column_analyzer = ColumnAnalyzer()

    def parse_statement(self, table_data):
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

---

## 八、限制和注意事项

### 8.1 当前支持

- ✅ 合并资产负债表
- ✅ 合并利润表
- ✅ 合并现金流量表
- ✅ 财务报表注释（标题+内容+表格）
- ⚠️ 部分特殊格式需要LLM辅助
- ⚠️ 不支持图片格式的表格
- ⚠️ 不支持所有者权益变动表（计划中）

### 8.2 使用注意事项

1. **虚拟环境**：必须在虚拟环境中运行
2. **PDF质量**：PDF需要是文本格式，不能是扫描件
3. **页码范围**：需要准确指定表格所在页码
4. **LLM配置**：使用LLM功能需要正确配置API
5. **Excel限制**：Sheet名称最大31字符，最多255个sheet

---

**最后更新**: 2026-02-10 | **版本**: v1.5.0
