# 文档索引

本目录包含项目的所有文档，按类别组织。

## 📚 文档结构

```
docs/
├── README.md                    # 本文件 - 文档索引
├── design/                      # 设计文档
│   ├── parser_optimization.md  # 列结构分析器优化设计 ⭐
│   └── agents.md               # Agent权限定义
└── reports/                     # 测试和进展报告
    ├── test_report.md          # 单元测试报告
    ├── integration_notes.md    # 集成测试说明
    ├── real_pdf_test_report.md # 真实PDF测试报告
    └── progress_report.md      # 项目进展报告 ⭐
```

## 🎯 快速导航

### 新手入门

1. **从这里开始**: [../README.md](../README.md) - 项目主页
2. **了解核心技术**: [design/parser_optimization.md](design/parser_optimization.md)
3. **查看测试结果**: [reports/real_pdf_test_report.md](reports/real_pdf_test_report.md)

### 开发者

1. **设计文档**: [design/parser_optimization.md](design/parser_optimization.md) - 理解动态列结构识别
2. **集成说明**: [reports/integration_notes.md](reports/integration_notes.md) - 了解集成过程
3. **当前状态**: [reports/progress_report.md](reports/progress_report.md) - 查看待办事项

### 测试相关

1. **单元测试**: [reports/test_report.md](reports/test_report.md) - ColumnAnalyzer测试
2. **集成测试**: [reports/integration_notes.md](reports/integration_notes.md) - 集成验证
3. **真实PDF测试**: [reports/real_pdf_test_report.md](reports/real_pdf_test_report.md) - 实际效果

## 📖 文档详情

### 设计文档 (design/)

#### [parser_optimization.md](design/parser_optimization.md) ⭐
**列结构分析器优化设计**

核心技术文档，详细介绍：
- 动态列结构识别的设计思路
- 三层识别策略（关键字匹配 → 特征推断 → LLM辅助）
- 智能缓存机制
- 使用方法和示例

**适合**: 想要理解核心技术的开发者

#### [agents.md](design/agents.md)
**Agent权限定义**

系统架构文档，包含：
- Agent角色定义
- 权限管理
- 工作流程

**适合**: 了解系统架构的开发者

---

### 测试报告 (reports/)

#### [test_report.md](reports/test_report.md)
**单元测试报告**

ColumnAnalyzer的单元测试结果：
- 7个测试用例全部通过
- 发现并修复的2个bug
- 核心功能验证

**适合**: 了解测试覆盖情况

#### [integration_notes.md](reports/integration_notes.md)
**集成测试说明**

ColumnAnalyzer集成到BalanceSheetParser的过程：
- 集成步骤
- 修改的文件
- 功能改进
- 向后兼容性

**适合**: 了解集成过程和改进点

#### [real_pdf_test_report.md](reports/real_pdf_test_report.md)
**真实PDF测试报告**

4家上市公司年报的测试结果：
- 福耀玻璃、海尔智家、海天味业、金山办公
- 详细的测试数据和分析
- 发现的问题和建议

**适合**: 了解实际效果和问题

#### [progress_report.md](reports/progress_report.md) ⭐
**项目进展报告**

最全面的项目状态文档：
- 已完成的工作
- 发现的问题（优先级分类）
- 下一步工作计划
- 技术亮点
- 关键文件清单

**适合**: 全面了解项目当前状态

## 🔍 按主题查找

### 想了解...

**核心技术原理**
→ [design/parser_optimization.md](design/parser_optimization.md)

**测试结果和效果**
→ [reports/real_pdf_test_report.md](reports/real_pdf_test_report.md)

**当前进展和待办**
→ [reports/progress_report.md](reports/progress_report.md)

**如何集成和使用**
→ [reports/integration_notes.md](reports/integration_notes.md)

**系统架构**
→ [design/agents.md](design/agents.md)

## 📝 文档更新记录

| 日期 | 文档 | 更新内容 |
|------|------|---------|
| 2026-02-04 | progress_report.md | 创建项目进展报告 |
| 2026-02-04 | real_pdf_test_report.md | 真实PDF测试结果 |
| 2026-02-04 | integration_notes.md | 集成说明 |
| 2026-02-04 | test_report.md | 单元测试报告 |
| 2026-02-04 | parser_optimization.md | 设计文档 |

## 🤝 贡献文档

如果你想贡献文档：

1. 设计文档放在 `design/` 目录
2. 测试报告放在 `reports/` 目录
3. 更新本索引文件
4. 使用Markdown格式
5. 包含清晰的标题和目录

---

**最后更新**: 2026-02-04
