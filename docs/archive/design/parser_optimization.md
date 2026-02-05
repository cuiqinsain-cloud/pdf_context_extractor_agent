# 解析器层优化方案

## 一、优化目标

解决当前解析器的以下问题：
1. **硬编码问题**：当前代码硬编码了4列、3列格式，不够灵活
2. **跨页列数变化**：跨页后列数可能变化，需要每行重新识别
3. **表头识别不通用**：依赖固定关键词，无法处理变体
4. **缺乏智能辅助**：遇到不确定情况无法自动处理

## 二、核心设计思路

### 2.1 动态列结构识别

**原理**：每行独立分析列结构，不依赖全局表头

**实现**：
```python
# 旧方法（全局识别一次）
header_info = _identify_header_structure(table_data)  # 只在开始时调用一次
for row in table_data:
    values = _extract_values_from_row(row, header_info)  # 所有行使用同一个header_info

# 新方法（每行动态识别）
for row in table_data:
    column_map = column_analyzer.analyze_row_structure(row, use_cache=True)
    values = column_analyzer.extract_values_from_row(row, column_map)
```

**优势**：
- 自动适应跨页列数变化
- 无需硬编码列数
- 支持混合格式表格

### 2.2 三层识别策略

#### 第一层：关键字匹配
```python
# 基于可扩展的关键字库
column_keywords = {
    ColumnType.CURRENT_PERIOD: [
        r'期末', r'本期末', r'本年末', r'2024年.*期末',
        r'年末余额'  # 可以不断添加新关键字
    ],
    ColumnType.PREVIOUS_PERIOD: [
        r'期初', r'上期末', r'上年末', r'2023年.*期末',
        r'年初余额'
    ]
}

# 遍历每个单元格，匹配关键字
for col_idx, cell in enumerate(row):
    for col_type, keywords in column_keywords.items():
        for keyword in keywords:
            if re.search(keyword, cell):
                matches[col_type] = col_idx
```

#### 第二层：特征推断
```python
# 基于内容特征判断列类型

# 特征1：附注格式（"七、1"）
if re.search(r'[一二三四五六七八九十]+、\d+', cell):
    → NOTE列

# 特征2：金额格式（数字）
if re.match(r'^\s*-?(\d{1,3}(,\d{3})*|\d+)(\.\d+)?\s*$', cell):
    → 第一个金额列 = CURRENT_PERIOD
    → 第二个金额列 = PREVIOUS_PERIOD

# 特征3：位置推断
if col_idx == 0:
    → ITEM_NAME列（第一列通常是项目名称）
```

#### 第三层：LLM辅助
```python
# 当前两层都无法确定时，调用LLM
if confidence < 0.7:
    llm_result = llm_assistant.analyze_header_with_llm(row)
    if llm_result['confidence'] > 0.7:
        column_map = llm_result['column_map']
```

### 2.3 缓存机制

**问题**：每行都重新分析会影响性能

**解决**：使用智能缓存
```python
# 第一次分析后缓存列模式
column_pattern_cache = {
    ColumnType.ITEM_NAME: 0,
    ColumnType.NOTE: 1,
    ColumnType.CURRENT_PERIOD: 2,
    ColumnType.PREVIOUS_PERIOD: 3
}

# 后续行先验证缓存是否有效
def _validate_cached_pattern(row, cached_pattern):
    # 检查1：列数是否匹配
    if max(cached_pattern.values()) >= len(row):
        return False  # 列数变化，缓存失效

    # 检查2：关键列的内容特征是否匹配
    for col_type, col_idx in cached_pattern.items():
        if col_type == CURRENT_PERIOD:
            if not is_numeric_format(row[col_idx]):
                return False  # 期末列不是数字，缓存失效

    return True  # 缓存有效
```

**效果**：
- 第一行：完整分析（耗时）
- 后续行：快速验证缓存（高效）
- 列数变化时：自动重新分析

### 2.4 关键字库管理

**设计**：可扩展的关键字库
```python
# 默认关键字库（内置）
default_keywords = {
    'current_period': [r'期末', r'本期末', r'本年末'],
    'previous_period': [r'期初', r'上期末', r'上年末']
}

# 自定义关键字库（JSON文件）
# config/keywords.json
{
    "current_period": [
        "年末余额",
        "报告期末",
        "本报告期末"
    ],
    "previous_period": [
        "年初余额",
        "上年期末",
        "上年同期"
    ]
}

# 加载时合并
keyword_library = KeywordLibrary('config/keywords.json')
keywords = keyword_library.get_keywords('current_period')
# → ['期末', '本期末', '本年末', '年末余额', '报告期末', '本报告期末']
```

**优势**：
- 无需修改代码即可扩展关键字
- 支持不同公司、不同年份的报表格式
- 可以通过LLM自动建议新关键字

## 三、使用方法

### 3.1 基本使用（不启用LLM）

```python
from src.parsers.column_analyzer import ColumnAnalyzer

# 创建分析器
analyzer = ColumnAnalyzer()

# 分析单行
row = ['项目', '附注', '2024年12月31日', '2023年12月31日']
column_map = analyzer.analyze_row_structure(row)
# 结果: {
#     ColumnType.ITEM_NAME: 0,
#     ColumnType.NOTE: 1,
#     ColumnType.CURRENT_PERIOD: 2,
#     ColumnType.PREVIOUS_PERIOD: 3
# }

# 提取数值
data_row = ['货币资金', '七、1', '1000000.00', '900000.00']
values = analyzer.extract_values_from_row(data_row, column_map)
# 结果: {
#     'item_name': '货币资金',
#     'note': '七、1',
#     'current_period': '1000000.00',
#     'previous_period': '900000.00'
# }
```

### 3.2 处理跨页列数变化

```python
analyzer = ColumnAnalyzer()

# 第126页：4列格式
row1 = ['货币资金', '七、1', '1000000.00', '900000.00']
column_map1 = analyzer.analyze_row_structure(row1, use_cache=True)
# 第一次分析，建立缓存

# 第127页：继续4列格式
row2 = ['应收账款', '七、5', '500000.00', '450000.00']
column_map2 = analyzer.analyze_row_structure(row2, use_cache=True)
# 使用缓存，快速返回

# 第128页：变为3列格式（附注列消失）
row3 = ['资产总计', '3900000.00', '3625000.00']
column_map3 = analyzer.analyze_row_structure(row3, use_cache=True)
# 检测到列数变化，自动重新分析
# 结果: {
#     ColumnType.ITEM_NAME: 0,
#     ColumnType.CURRENT_PERIOD: 1,
#     ColumnType.PREVIOUS_PERIOD: 2
# }
```

### 3.3 启用LLM辅助

```python
from src.parsers.llm_assistant import LLMAssistant

# 创建LLM辅助器
llm_assistant = LLMAssistant(enable_llm=True)

# 遇到不确定的表头
uncertain_row = ['会计项目', '本报告期末', '上年同期']

# 调用LLM分析
result = llm_assistant.analyze_header_with_llm(uncertain_row)
# 结果: {
#     'column_map': {
#         'item_name': 0,
#         'current_period': 1,
#         'previous_period': 2
#     },
#     'confidence': 0.95,
#     'used_llm': True,
#     'reasoning': '第一列"会计项目"表示项目名称，第二列"本报告期末"表示期末数据...'
# }
```

### 3.4 扩展关键字库

```python
from src.parsers.llm_assistant import KeywordLibrary

# 加载关键字库
library = KeywordLibrary('config/keywords.json')

# 添加新关键字
library.add_keyword('current_period', r'报告期末')
library.add_keyword('previous_period', r'上年同期')

# 保存到文件
library.save_library()
```

## 四、与现有代码的集成

### 4.1 修改balance_sheet.py

```python
# 在BalanceSheetParser.__init__中添加
from src.parsers.column_analyzer import ColumnAnalyzer
from src.parsers.llm_assistant import LLMAssistant, KeywordLibrary

def __init__(self, enable_llm=False, keyword_library_path=None):
    # 原有的初始化代码...

    # 新增：初始化列分析器
    self.column_analyzer = ColumnAnalyzer()
    self.llm_assistant = LLMAssistant(enable_llm=enable_llm)
    self.keyword_library = KeywordLibrary(keyword_library_path)

    # 注入关键字库
    self.column_analyzer.column_keywords = {
        ColumnType.ITEM_NAME: self.keyword_library.get_keywords('item_name'),
        ColumnType.CURRENT_PERIOD: self.keyword_library.get_keywords('current_period'),
        ColumnType.PREVIOUS_PERIOD: self.keyword_library.get_keywords('previous_period'),
        ColumnType.NOTE: self.keyword_library.get_keywords('note')
    }
```

### 4.2 修改parse_balance_sheet方法

```python
def parse_balance_sheet(self, table_data):
    # 原有的初始化代码...

    # 重置列分析器缓存
    self.column_analyzer.reset_cache()

    # 逐行解析
    for row_idx, row in enumerate(table_data):
        # 旧代码（删除）：
        # values = self._extract_values_from_row(row, header_info)

        # 新代码：动态分析列结构
        column_map = self.column_analyzer.analyze_row_structure(row, use_cache=True)

        # 如果识别失败，尝试LLM辅助
        if not column_map or len(column_map) < 2:
            llm_result = self.llm_assistant.analyze_header_with_llm(row)
            if llm_result['used_llm'] and llm_result['confidence'] > 0.7:
                column_map = self._convert_llm_result(llm_result['column_map'])

        # 提取数值
        values = self.column_analyzer.extract_values_from_row(row, column_map)

        # 后续的匹配和存储逻辑保持不变...
```

### 4.3 删除硬编码的方法

可以删除或废弃以下方法：
- `_identify_header_structure`（全局表头识别）
- `_extract_values_from_row`中的硬编码部分（4列、3列格式）

## 五、优势总结

### 5.1 灵活性
- ✅ 无硬编码，完全自适应
- ✅ 支持任意列数和列顺序
- ✅ 支持跨页列数变化

### 5.2 准确性
- ✅ 三层识别策略，提高准确率
- ✅ 智能缓存验证，避免误用缓存
- ✅ LLM辅助处理边缘情况

### 5.3 可扩展性
- ✅ 关键字库可配置
- ✅ 支持LLM自动建议新关键字
- ✅ 易于添加新的列类型

### 5.4 性能
- ✅ 智能缓存机制，避免重复分析
- ✅ LLM可选，控制成本
- ✅ 增量学习，越用越准

## 六、测试建议

### 6.1 单元测试

```python
def test_column_analyzer():
    analyzer = ColumnAnalyzer()

    # 测试1：标准4列格式
    row = ['项目', '附注', '期末', '期初']
    column_map = analyzer.analyze_row_structure(row)
    assert ColumnType.ITEM_NAME in column_map
    assert ColumnType.CURRENT_PERIOD in column_map

    # 测试2：3列格式
    row = ['项目', '本期末', '上期末']
    column_map = analyzer.analyze_row_structure(row)
    assert len(column_map) == 3

    # 测试3：缓存机制
    row1 = ['货币资金', '七、1', '1000000', '900000']
    map1 = analyzer.analyze_row_structure(row1, use_cache=True)

    row2 = ['应收账款', '七、5', '500000', '450000']
    map2 = analyzer.analyze_row_structure(row2, use_cache=True)

    assert map1 == map2  # 应该使用缓存
```

### 6.2 集成测试

使用真实的PDF报表测试：
- 金山办公2024年报（126-128页）
- 福耀玻璃2024年报
- 海尔智家2024年报

验证：
- 跨页列数变化是否正确处理
- 不同格式的表头是否正确识别
- 数据提取的准确性

## 七、后续优化方向

1. **机器学习增强**：训练模型识别列类型
2. **上下文感知**：利用前后行的信息辅助判断
3. **置信度评分**：为每个识别结果提供置信度
4. **自动纠错**：检测并修正明显的识别错误
5. **可视化调试**：提供列结构识别的可视化界面
