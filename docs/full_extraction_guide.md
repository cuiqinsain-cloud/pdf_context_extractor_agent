# 完整文档注释提取指南

## 📖 概述

本指南介绍如何使用批量提取脚本处理完整的财务报表注释章节。

---

## 🚀 快速开始

### 1. 基本用法

```bash
python scripts/extract_full_notes.py <PDF路径> <起始页> <结束页>
```

### 2. 示例

**福耀玻璃年报（125-174页）**:
```bash
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174
```

**深信服年报（162-199页）**:
```bash
python scripts/extract_full_notes.py \
    data/深信服2024年年度报告.pdf \
    162 199
```

### 3. 自定义输出路径

```bash
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174 \
    -o output/fuyao_notes.json
```

### 4. 自定义批次大小

```bash
python scripts/extract_full_notes.py \
    data/福耀玻璃2024年年度报告.pdf \
    125 174 \
    -b 3  # 使用3页/批次
```

---

## 📊 预估时间

基于测试结果（5页/批次，2.3分钟/批次）：

| 文档 | 页数 | 批次数 | 预估时间 |
|------|------|--------|----------|
| 福耀玻璃 (125-174) | 50页 | 10批次 | ~23分钟 |
| 深信服 (162-199) | 38页 | 8批次 | ~18分钟 |

---

## 📝 输出格式

### JSON结构

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
        "tables": [
          [
            ["列1", "列2", "列3"],
            ["数据1", "数据2", "数据3"]
          ]
        ],
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

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `notes` | array | 提取的所有标题和内容 |
| `total_pages` | int | 处理的总页数 |
| `total_notes` | int | 提取的总标题数 |
| `errors` | array | 错误信息列表 |

**Note对象**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `number` | string | 标题序号（如"1"、"1.1"） |
| `level` | int | 层级（1=主标题，2=子标题） |
| `title` | string | 标题文本 |
| `full_title` | string | 完整标题（含序号） |
| `page_num` | int | 页码 |
| `content` | object | 内容对象 |
| `has_table` | boolean | 是否包含表格 |
| `is_complete` | boolean | 内容是否完整 |

**Content对象**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | string | 文本内容 |
| `tables` | array | 表格数据（二维数组） |
| `table_count` | int | 表格数量 |

---

## 🔧 命令行参数

```
usage: extract_full_notes.py [-h] [-o OUTPUT] [-b BATCH_SIZE]
                              pdf_path start_page end_page

提取完整文档的财务报表注释

positional arguments:
  pdf_path              PDF文件路径
  start_page            起始页码
  end_page              结束页码

optional arguments:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出JSON文件路径（默认：output/notes_full.json）
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        批次大小（默认：5）
```

---

## 📈 性能优化建议

### 1. 批次大小选择

| 批次大小 | 优点 | 缺点 | 适用场景 |
|----------|------|------|----------|
| 3页 | 稳定性最高 | 速度较慢 | 网络不稳定时 |
| **5页** | **平衡最优** | - | **推荐默认** |
| 10页 | 速度最快 | 可能超时 | 网络极好时 |

**推荐**: 使用默认的5页/批次，在性能和稳定性之间取得最佳平衡。

### 2. 网络优化

- 使用稳定的网络连接
- 避免在网络高峰期运行
- 如遇超时，减小批次大小

### 3. 成本优化

- 批量处理比逐页处理节省80% API成本
- 5页批次是成本效益最优方案

---

## 🐛 故障排除

### 问题1: 请求超时

**症状**:
```
ERROR: Request timeout after 120 seconds
```

**解决方案**:
1. 减小批次大小：`-b 3`
2. 检查网络连接
3. 重试失败的批次

### 问题2: 内存不足

**症状**:
```
MemoryError: Unable to allocate array
```

**解决方案**:
1. 减小批次大小
2. 关闭其他程序释放内存
3. 分段处理大文档

### 问题3: 提取质量问题

**症状**: 标题或内容缺失

**解决方案**:
1. 检查PDF质量（是否为扫描件）
2. 查看日志中的错误信息
3. 手动验证关键页面

---

## 📊 质量检查

### 1. 自动检查

脚本会自动输出以下统计信息：
- 提取的标题数量
- 包含内容的标题比例
- 包含表格的标题比例
- 总表格数

### 2. 手动验证

建议抽查以下内容：
- [ ] 第一个标题是否正确
- [ ] 最后一个标题是否正确
- [ ] 随机抽查5-10个标题
- [ ] 检查表格数据是否完整
- [ ] 验证层级结构是否正确

### 3. 验证脚本

```python
import json

# 读取结果
with open('output/notes_full.json', 'r') as f:
    data = json.load(f)

# 检查完整性
print(f"总标题数: {data['total_notes']}")
print(f"成功率: {data['success']}")
print(f"错误数: {len(data['errors'])}")

# 检查内容完整性
complete_notes = sum(1 for n in data['notes'] if n.get('is_complete'))
print(f"完整标题: {complete_notes}/{data['total_notes']}")

# 检查表格
notes_with_tables = sum(1 for n in data['notes'] if n.get('has_table'))
print(f"包含表格: {notes_with_tables}/{data['total_notes']}")
```

---

## 🎯 最佳实践

### 1. 处理流程

```bash
# 步骤1: 先处理小范围测试（如前10页）
python scripts/extract_full_notes.py data/report.pdf 125 134 -o output/test.json

# 步骤2: 检查测试结果
python -c "import json; print(json.load(open('output/test.json'))['total_notes'])"

# 步骤3: 确认无误后处理完整文档
python scripts/extract_full_notes.py data/report.pdf 125 174 -o output/full.json
```

### 2. 备份策略

```bash
# 定期备份结果
cp output/notes_full.json output/backup/notes_full_$(date +%Y%m%d_%H%M%S).json
```

### 3. 日志记录

```bash
# 保存日志到文件
python scripts/extract_full_notes.py data/report.pdf 125 174 2>&1 | tee logs/extraction.log
```

---

## 📚 相关文档

- [批量提取性能测试报告](batch_extraction_report.md)
- [NotesExtractor API文档](../src/parsers/notes_extractor.py)
- [BatchNotesExtractor API文档](../src/parsers/batch_notes_extractor.py)

---

## 💡 提示

1. **首次使用**: 建议先在小范围（10-20页）测试，确认效果后再处理完整文档
2. **长时间运行**: 对于50页以上的文档，建议使用 `nohup` 或 `screen` 在后台运行
3. **结果验证**: 处理完成后务必进行质量检查，确保数据完整性
4. **成本控制**: 批量处理已经很经济，但仍建议避免重复处理同一文档

---

## ✅ 检查清单

处理完整文档前的检查：

- [ ] PDF文件路径正确
- [ ] 页码范围正确（起始页 < 结束页）
- [ ] 输出目录存在且有写权限
- [ ] LLM配置正确（config/llm_config.yaml）
- [ ] 网络连接稳定
- [ ] 已在小范围测试成功

处理完成后的检查：

- [ ] success 字段为 true
- [ ] total_notes 数量合理
- [ ] errors 列表为空或可接受
- [ ] 抽查关键标题和内容
- [ ] 表格数据完整
- [ ] 已备份结果文件
