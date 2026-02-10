# 技术架构

本文档描述项目的技术架构和核心技术。

---

## 一、系统架构

### 1.1 三层架构设计

```
┌─────────────────────────────────────────┐
│         PDF读取层 (pdf_reader.py)        │
│  - 读取PDF文件                            │
│  - 提取页面对象                           │
│  - 管理文件资源                           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      表格提取层 (table_extractor.py)     │
│  - 识别表格区域                           │
│  - 提取表格数据                           │
│  - 处理跨页表格                           │
│  - 数据清洗和格式化                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       解析器层 (parsers/)                │
│  - 动态列结构识别 ⭐                      │
│  - 项目名称匹配                           │
│  - 数据提取和验证                         │
│  - LLM辅助识别（可选）                    │
└─────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
main.py
  └─> pdf_reader.py
  └─> table_extractor.py
  └─> parsers/
        ├─> balance_sheet.py
        │     └─> column_analyzer.py ⭐
        │     └─> hybrid_column_analyzer.py (可选)
        │           ├─> llm_client.py
        │           ├─> result_comparator.py
        │           └─> user_choice_handler.py
        └─> config_loader.py
```

---

## 二、核心技术

### 2.1 动态列结构识别

**问题背景**：
- 不同公司的财务报表格式不同
- 列数可能是3列、4列或更多
- 表头格式多样（期末/期初、日期格式等）
- 跨页时列数可能变化

**传统方法的局限**：
```python
# ❌ 硬编码方式
if len(row) == 4:
    current_period_col = 2
    previous_period_col = 3
elif len(row) == 3:
    current_period_col = 1
    previous_period_col = 2
```

**我们的解决方案**：

#### 三层识别策略

```
第一层：关键字匹配
  ├─ 使用正则表达式匹配表头关键字
  ├─ 支持多种格式（期末/期初、日期等）
  └─ 快速准确

第二层：特征推断
  ├─ 基于内容特征推断列类型
  ├─ 识别金额格式、附注格式
  └─ 补充关键字匹配的不足

第三层：LLM辅助（可选）
  ├─ 使用大语言模型智能识别
  ├─ 处理复杂和特殊格式
  └─ 与规则匹配结果对比
```

#### 智能缓存机制

```python
# 首次分析：完整识别
column_map = analyzer.analyze_row_structure(row, use_cache=False)

# 后续行：快速验证
if len(row) == cached_row_length:
    # 使用缓存，无需重新分析
    return cached_column_map
else:
    # 列数变化，重新分析
    column_map = analyzer.analyze_row_structure(row, use_cache=False)
```

**性能优势**：
- 首次分析：~10ms
- 缓存命中：~0.1ms
- 性能提升：100倍

### 2.2 混合识别方案（LLM集成）

**架构设计**：

```
┌─────────────────────────────────────────┐
│     HybridColumnAnalyzer                │
│  (混合列分析器)                          │
└───┬─────────────────────────────────┬───┘
    │                                 │
    ▼                                 ▼
┌─────────────┐              ┌─────────────┐
│ColumnAnalyzer│              │ LLMClient   │
│ (规则匹配)   │              │ (LLM识别)   │
└──────┬──────┘              └──────┬──────┘
       │                            │
       │  结果A                     │  结果B
       │                            │
       └──────────┬─────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ ResultComparator │
         │  (结果对比)       │
         └────────┬─────────┘
                  │
         ┌────────┴────────┐
         │                 │
    一致 │                 │ 不一致
         ▼                 ▼
  ┌──────────┐      ┌──────────────┐
  │ 自动使用  │      │ 用户选择      │
  └──────────┘      └──────────────┘
```

**工作流程**：

1. **规则匹配**：使用 ColumnAnalyzer 进行快速识别
2. **LLM识别**：调用 LLM API 进行智能识别
3. **结果对比**：使用 ResultComparator 对比两个结果
4. **决策**：
   - 如果一致 → 自动使用规则结果
   - 如果不一致 → 提示用户选择

**优势**：
- ✅ 保留规则匹配的速度和可控性
- ✅ 增加LLM的智能和灵活性
- ✅ 用户可以干预和学习
- ✅ 支持多种LLM provider

---

## 三、数据流

### 3.1 完整数据流

```
PDF文件
  │
  ▼ (pdf_reader.py)
页面对象
  │
  ▼ (table_extractor.py)
表格数据 (List[List[str]])
  │
  ▼ (column_analyzer.py)
列结构映射 (Dict[ColumnType, int])
  │
  ▼ (balance_sheet.py)
结构化数据 (Dict)
  │
  ├─> assets (资产)
  ├─> liabilities (负债)
  ├─> equity (所有者权益)
  └─> validation (验证信息)
  │
  ▼ (export_to_excel.py)
Excel文件
```

### 3.2 数据结构

#### 表格数据
```python
[
    ['项目', '附注', '期末', '期初'],  # 表头
    ['流动资产：', None, None, None],  # 分类行
    ['货币资金', '七、1', '1000000', '900000'],  # 数据行
    ...
]
```

#### 列结构映射
```python
{
    ColumnType.ITEM_NAME: 0,
    ColumnType.NOTE: 1,
    ColumnType.CURRENT_PERIOD: 2,
    ColumnType.PREVIOUS_PERIOD: 3
}
```

#### 解析结果
```python
{
    'assets': {
        'current_assets': [
            {'name': '货币资金', 'current': 1000000, 'previous': 900000},
            ...
        ],
        'non_current_assets': [...]
    },
    'liabilities': {...},
    'equity': {...},
    'validation': {
        'balance_check': True,
        'completeness': 0.95
    }
}
```

---

## 四、关键算法

### 4.1 关键字匹配算法

```python
def _match_by_keywords(self, row):
    matches = {}
    for col_idx, cell in enumerate(row):
        cell_text = str(cell).strip()
        for col_type, keywords in self.column_keywords.items():
            for keyword in keywords:
                if re.search(keyword, cell_text):
                    matches[col_type] = col_idx
                    break
    return matches
```

**特点**：
- 使用正则表达式
- 支持多种格式
- 优先匹配原则

### 4.2 特征推断算法

```python
def _infer_by_features(self, row, keyword_matches):
    inferred = {}
    for col_idx, cell in enumerate(row):
        if col_idx in keyword_matches.values():
            continue

        # 识别金额格式
        if self._is_amount_format(cell):
            if ColumnType.CURRENT_PERIOD not in keyword_matches:
                inferred[ColumnType.CURRENT_PERIOD] = col_idx
            elif ColumnType.PREVIOUS_PERIOD not in keyword_matches:
                inferred[ColumnType.PREVIOUS_PERIOD] = col_idx

    return inferred
```

**特点**：
- 基于内容特征
- 补充关键字匹配
- 智能推断

### 4.3 缓存验证算法

```python
def _validate_cached_pattern(self, row, cached_pattern):
    # 检查列数是否变化
    max_col_idx = max(cached_pattern.values())
    if max_col_idx >= len(row):
        return False  # 列数减少，缓存失效

    return True  # 缓存有效
```

**特点**：
- 快速验证
- 自动失效
- 性能优化

---

## 五、数据导出层

### 5.1 财务科目标准化

**模块**: `src/parsers/statement_labels.py`

**功能描述**：
- 提供财务科目的中英文映射
- 将解析器内部的英文键名转换为标准中文财务科目
- 支持三种报表类型

**数据结构**：
```python
# 资产负债表科目映射（70+项）
BALANCE_SHEET_LABELS = {
    'cash': '货币资金',
    'accounts_receivable': '应收账款',
    'fixed_assets': '固定资产',
    # ...
}

# 利润表科目映射（30+项）
INCOME_STATEMENT_LABELS = {
    'operating_revenue': '营业收入',
    'operating_cost': '营业成本',
    'net_profit': '净利润',
    # ...
}

# 现金流量表科目映射（40+项）
CASH_FLOW_LABELS = {
    'sales_goods_cash': '销售商品、提供劳务收到的现金',
    'operating_net_cash_flow': '经营活动产生的现金流量净额',
    # ...
}
```

**使用方法**：
```python
from src.parsers.statement_labels import get_label

# 获取标准中文名称
label = get_label('cash', 'balance_sheet')
# 返回: '货币资金'
```

**特点**：
- 集中管理所有科目名称
- 易于维护和扩展
- 向后兼容（找不到映射时返回原键名）

### 5.2 综合导出工具

**模块**: `tools/export_all_statements.py`

**架构设计**：
```
配置层 (TEST_CASES)
    ↓
解析层 (parse_statement)
    ↓
转换层 (*_to_dataframe)
    ↓
导出层 (export_company_to_excel)
```

**核心组件**：

1. **配置层**：
```python
TEST_CASES = [
    {
        'name': '福耀玻璃',
        'file': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
        'balance_sheet': (89, 91),
        'income_statement': (93, 95),
        'cash_flow': (96, 97)
    },
    # ...
]
```

2. **解析层**：
```python
def parse_statement(pdf_file, pages, parser_class, statement_name):
    # 1. 读取PDF
    # 2. 提取表格
    # 3. 合并数据
    # 4. 解析报表
    return result
```

3. **转换层**：
```python
def balance_sheet_to_dataframe(company_name, result):
    rows = []
    for item_name, item_data in result['assets']['current_assets'].items():
        rows.append({
            '公司': company_name,
            '类别': '流动资产',
            '项目': get_label(item_name, 'balance_sheet'),  # 使用标准名称
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })
    return pd.DataFrame(rows)
```

4. **导出层**：
```python
def export_company_to_excel(test_case):
    # 解析三张报表
    balance_sheet_result = parse_statement(...)
    income_statement_result = parse_statement(...)
    cash_flow_result = parse_statement(...)

    # 转换为DataFrame
    df_balance = balance_sheet_to_dataframe(...)
    df_income = income_statement_to_dataframe(...)
    df_cash = cash_flow_to_dataframe(...)

    # 导出到Excel（一个文件，三个工作表）
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_balance.to_excel(writer, sheet_name='资产负债表', index=False)
        df_income.to_excel(writer, sheet_name='利润表', index=False)
        df_cash.to_excel(writer, sheet_name='现金流量表', index=False)
```

**特点**：
- 模块化设计，职责单一
- 统一的数据格式
- 批量处理能力
- 容错机制
- 可扩展性强

**输出格式**：
- 文件名：`{公司名}_三表合一_{时间戳}.xlsx`
- 位置：`output/` 目录
- 结构：3个工作表（资产负债表、利润表、现金流量表）
- 列结构：公司、类别、项目、本期金额、上期金额、附注

---

## 六、扩展性设计

### 6.1 插件化架构

```python
# 添加新的解析器
class IncomeStatementParser:
    def __init__(self):
        self.column_analyzer = ColumnAnalyzer()

    def parse_income_statement(self, table_data):
        # 使用相同的列识别技术
        pass
```

### 6.2 配置驱动

```json
{
  "column_keywords": {
    "current_period": ["期末", "本期末", "..."],
    "previous_period": ["期初", "上期末", "..."]
  }
}
```

### 6.3 LLM Provider抽象

```python
class LLMClient:
    def __init__(self, provider):
        self.provider = provider

    def analyze_header(self, header_row):
        if self.provider == "anthropic":
            return self._call_anthropic_api(header_row)
        elif self.provider == "openai":
            return self._call_openai_api(header_row)
        # 易于添加新的provider
```

---

## 七、性能优化

### 7.1 缓存策略

- **列模式缓存**：避免重复分析相同结构
- **LLM响应缓存**：避免重复调用API
- **表格数据缓存**：避免重复读取PDF

### 6.2 并行处理（计划中）

```python
# 批量处理多个PDF
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_pdf, pdf) for pdf in pdfs]
    results = [f.result() for f in futures]
```

### 6.3 内存优化

- 流式处理大型PDF
- 及时释放不需要的数据
- 使用生成器而非列表

---

## 七、安全性

### 7.1 API Key管理

- ✅ 从环境变量读取
- ✅ 不在代码中硬编码
- ✅ 不提交到版本控制

### 7.2 数据验证

- ✅ 输入验证
- ✅ 类型检查
- ✅ 边界检查

### 7.3 错误处理

- ✅ 异常捕获
- ✅ 优雅降级
- ✅ 详细日志

---

## 八、技术栈

### 8.1 核心库

| 库 | 版本 | 用途 |
|---|------|------|
| pdfplumber | 0.10.0+ | PDF解析 |
| pandas | 2.0.0+ | 数据处理 |
| openpyxl | 3.1.0+ | Excel导出 |
| requests | 2.31.0+ | HTTP请求 |

### 8.2 开发工具

| 工具 | 用途 |
|------|------|
| venv | 虚拟环境 |
| pytest | 单元测试 |
| black | 代码格式化 |
| flake8 | 代码检查 |

---

## 九、设计模式

### 9.1 使用的设计模式

- **策略模式**：多种列识别策略
- **工厂模式**：LLM客户端创建
- **单例模式**：配置加载器
- **观察者模式**：用户选择记录

### 9.2 SOLID原则

- **单一职责**：每个类只负责一个功能
- **开闭原则**：对扩展开放，对修改关闭
- **里氏替换**：子类可以替换父类
- **接口隔离**：接口最小化
- **依赖倒置**：依赖抽象而非具体实现

---

**当前版本**: v1.5.0
**最后更新**: 2026-02-10
