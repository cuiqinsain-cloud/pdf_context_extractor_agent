# LLM智能识别集成方案设计

## 一、方案概述

### 1.1 设计目标

实现 **规则匹配 + LLM智能识别** 的混合方案：
- 规则匹配作为基础（快速、免费、可控）
- LLM识别作为增强（智能、灵活、准确）
- 两者结果对比，不一致时提示用户选择
- 使用 Claude Agent SDK 实现

### 1.2 工作流程

```
┌─────────────────┐
│  提取表头行      │
└────────┬────────┘
         │
         ├──────────────────────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐            ┌─────────────────┐
│  规则匹配识别    │            │  LLM智能识别     │
│  (ColumnAnalyzer)│            │  (Claude SDK)    │
└────────┬────────┘            └────────┬────────┘
         │                              │
         │  结果A                       │  结果B
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌─────────────────┐
         │  结果对比分析    │
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         │                 │
    一致 │                 │ 不一致
         ▼                 ▼
  ┌──────────┐      ┌──────────────┐
  │ 直接使用  │      │ 提示用户选择  │
  └──────────┘      └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ 记录用户选择  │
                    │ 用于学习优化  │
                    └──────────────┘
```

## 二、技术架构

### 2.1 核心组件

#### 1. HybridColumnAnalyzer（混合列分析器）
- 继承现有的 ColumnAnalyzer
- 集成 LLM 识别能力
- 实现结果对比和冲突解决

#### 2. ClaudeSDKClient（Claude SDK客户端）
- 封装 Claude Agent SDK 调用
- 管理 API 配置和连接
- 处理错误和重试

#### 3. ResultComparator（结果对比器）
- 对比规则匹配和LLM识别结果
- 计算差异和置信度
- 生成对比报告

#### 4. UserChoiceHandler（用户选择处理器）
- 提示用户选择
- 记录用户决策
- 用于后续学习和优化

### 2.2 类图

```python
┌─────────────────────────────────┐
│     HybridColumnAnalyzer        │
├─────────────────────────────────┤
│ - rule_analyzer: ColumnAnalyzer │
│ - llm_client: ClaudeSDKClient   │
│ - comparator: ResultComparator  │
│ - choice_handler: UserChoice... │
├─────────────────────────────────┤
│ + analyze_with_hybrid()         │
│ + compare_results()             │
│ + resolve_conflict()            │
└─────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ColumnAnalyzer│  │ClaudeSDK...  │  │ResultComp... │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 三、Claude Agent SDK 集成

### 3.1 SDK 选择

使用 **Anthropic Python SDK** + **Agent 模式**：
```python
from anthropic import Anthropic
```

### 3.2 Prompt 设计

#### 系统提示词
```
你是一个专业的财务报表分析专家，擅长识别中国A股上市公司年报中的资产负债表结构。

你的任务是分析表头行，识别每一列的类型：
- item_name: 项目名称/科目名称
- current_period: 期末/本期末/本年末数据
- previous_period: 期初/上期末/上年末数据
- note: 附注/注释编号
- unknown: 无法确定的列

要求：
1. 仔细分析每一列的文本内容
2. 考虑中国财务报表的常见格式
3. 注意日期格式可能包含空格（如"2024 年12月 31日"）
4. 给出你的分析理由和置信度
```

#### 用户提示词模板
```
请分析以下表头行，识别每一列的类型：

表头数据：
{header_row}

请以JSON格式返回结果：
{
  "column_map": {
    "item_name": 列索引,
    "current_period": 列索引,
    "previous_period": 列索引,
    "note": 列索引
  },
  "confidence": 0.95,
  "reasoning": "详细的分析理由"
}
```

## 四、配置参数清单

### 4.1 Claude API 配置

需要用户提供的配置参数：

```python
# config/llm_config.json
{
  "claude_api": {
    # ============ 必填参数 ============
    "api_key": "YOUR_ANTHROPIC_API_KEY",  # Anthropic API密钥
    "model": "claude-3-5-sonnet-20241022",  # 模型名称

    # ============ 可选参数 ============
    "max_tokens": 1024,  # 最大token数
    "temperature": 0.0,  # 温度（0=确定性，1=创造性）
    "timeout": 30,  # 请求超时时间（秒）
    "max_retries": 3,  # 最大重试次数

    # ============ 高级参数 ============
    "base_url": null,  # 自定义API端点（可选）
    "default_headers": {},  # 自定义请求头（可选）
    "proxy": null  # 代理设置（可选）
  },

  "llm_settings": {
    # ============ 功能开关 ============
    "enable_llm": true,  # 是否启用LLM识别
    "enable_comparison": true,  # 是否启用结果对比
    "enable_user_choice": true,  # 是否启用用户选择

    # ============ 行为配置 ============
    "confidence_threshold": 0.7,  # 置信度阈值
    "auto_accept_if_match": true,  # 结果一致时自动接受
    "always_use_llm": false,  # 是否总是调用LLM（调试用）
    "fallback_to_rules": true,  # LLM失败时回退到规则

    # ============ 对比策略 ============
    "comparison_mode": "strict",  # strict/lenient
    "allow_partial_match": false,  # 是否允许部分匹配

    # ============ 用户交互 ============
    "choice_timeout": 60,  # 用户选择超时时间（秒）
    "default_choice": "rules",  # 超时时的默认选择：rules/llm/skip
    "save_choices": true,  # 是否保存用户选择历史
    "choices_log_path": "logs/user_choices.json"
  },

  "performance": {
    # ============ 性能优化 ============
    "cache_llm_results": true,  # 是否缓存LLM结果
    "cache_ttl": 3600,  # 缓存有效期（秒）
    "batch_mode": false,  # 是否批量处理（未来功能）
    "parallel_requests": 1  # 并行请求数
  },

  "logging": {
    # ============ 日志配置 ============
    "log_llm_requests": true,  # 是否记录LLM请求
    "log_llm_responses": true,  # 是否记录LLM响应
    "log_comparisons": true,  # 是否记录对比结果
    "log_user_choices": true,  # 是否记录用户选择
    "log_file": "logs/llm_integration.log"
  }
}
```

### 4.2 环境变量配置（可选）

```bash
# .env 文件
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选
ANTHROPIC_TIMEOUT=30
```

### 4.3 配置优先级

1. 环境变量（最高优先级）
2. 配置文件
3. 代码默认值（最低优先级）

## 五、实现细节

### 5.1 ClaudeSDKClient 实现

```python
from anthropic import Anthropic
import json
from typing import Dict, Any, Optional

class ClaudeSDKClient:
    """Claude SDK客户端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化客户端

        Args:
            config: 配置字典
        """
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-5-sonnet-20241022')
        self.max_tokens = config.get('max_tokens', 1024)
        self.temperature = config.get('temperature', 0.0)
        self.timeout = config.get('timeout', 30)

        # 初始化Anthropic客户端
        self.client = Anthropic(
            api_key=self.api_key,
            timeout=self.timeout,
            base_url=config.get('base_url'),
            default_headers=config.get('default_headers', {})
        )

        # 系统提示词
        self.system_prompt = self._build_system_prompt()

    def analyze_header(self, header_row: list) -> Dict[str, Any]:
        """
        使用Claude分析表头

        Args:
            header_row: 表头行数据

        Returns:
            分析结果
        """
        # 构建用户提示词
        user_prompt = self._build_user_prompt(header_row)

        # 调用Claude API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # 解析响应
            response_text = message.content[0].text
            result = json.loads(response_text)

            return {
                'success': True,
                'column_map': result.get('column_map', {}),
                'confidence': result.get('confidence', 0.0),
                'reasoning': result.get('reasoning', ''),
                'raw_response': response_text
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'column_map': {},
                'confidence': 0.0
            }

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是一个专业的财务报表分析专家..."""

    def _build_user_prompt(self, header_row: list) -> str:
        """构建用户提示词"""
        return f"""请分析以下表头行...

表头数据：{json.dumps(header_row, ensure_ascii=False)}
..."""
```

### 5.2 ResultComparator 实现

```python
class ResultComparator:
    """结果对比器"""

    def compare(self,
                rule_result: Dict[str, int],
                llm_result: Dict[str, int]) -> Dict[str, Any]:
        """
        对比两个结果

        Args:
            rule_result: 规则匹配结果
            llm_result: LLM识别结果

        Returns:
            对比结果
        """
        # 检查是否完全一致
        is_match = rule_result == llm_result

        # 计算差异
        differences = []
        all_keys = set(rule_result.keys()) | set(llm_result.keys())

        for key in all_keys:
            rule_val = rule_result.get(key)
            llm_val = llm_result.get(key)

            if rule_val != llm_val:
                differences.append({
                    'column_type': key,
                    'rule_index': rule_val,
                    'llm_index': llm_val
                })

        return {
            'is_match': is_match,
            'differences': differences,
            'rule_result': rule_result,
            'llm_result': llm_result
        }
```

### 5.3 UserChoiceHandler 实现

```python
class UserChoiceHandler:
    """用户选择处理器"""

    def prompt_user_choice(self,
                          comparison: Dict[str, Any],
                          header_row: list) -> str:
        """
        提示用户选择

        Args:
            comparison: 对比结果
            header_row: 表头行

        Returns:
            用户选择：'rules' 或 'llm' 或 'skip'
        """
        print("\n" + "="*80)
        print("检测到规则匹配和LLM识别结果不一致")
        print("="*80)

        print(f"\n表头行: {header_row}")

        print("\n规则匹配结果:")
        self._print_result(comparison['rule_result'], header_row)

        print("\nLLM识别结果:")
        self._print_result(comparison['llm_result'], header_row)

        print("\n差异:")
        for diff in comparison['differences']:
            print(f"  - {diff['column_type']}: "
                  f"规则={diff['rule_index']}, "
                  f"LLM={diff['llm_index']}")

        print("\n请选择:")
        print("  1. 使用规则匹配结果")
        print("  2. 使用LLM识别结果")
        print("  3. 跳过此表格")

        choice = input("\n请输入选择 (1/2/3): ").strip()

        choice_map = {
            '1': 'rules',
            '2': 'llm',
            '3': 'skip'
        }

        return choice_map.get(choice, 'rules')

    def _print_result(self, result: Dict[str, int], header_row: list):
        """打印结果"""
        for col_type, col_idx in result.items():
            cell_value = header_row[col_idx] if col_idx < len(header_row) else 'N/A'
            print(f"  - {col_type}: 列{col_idx} = '{cell_value}'")
```

## 六、使用示例

### 6.1 基本使用

```python
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer

# 加载配置
config = load_config('config/llm_config.json')

# 创建混合分析器
analyzer = HybridColumnAnalyzer(config)

# 分析表头
header_row = ['项目', '附注', '2024 年12月 31日', '2023 年12 月31日']
result = analyzer.analyze_with_hybrid(header_row)

print(f"最终结果: {result['final_result']}")
print(f"使用方法: {result['method']}")  # 'rules', 'llm', 或 'user_choice'
```

### 6.2 集成到 BalanceSheetParser

```python
class BalanceSheetParser:
    def __init__(self, enable_llm: bool = False):
        if enable_llm:
            config = load_config('config/llm_config.json')
            self.column_analyzer = HybridColumnAnalyzer(config)
        else:
            self.column_analyzer = ColumnAnalyzer()
```

## 七、测试计划

### 7.1 单元测试

- [ ] ClaudeSDKClient API调用测试
- [ ] ResultComparator 对比逻辑测试
- [ ] UserChoiceHandler 交互测试
- [ ] HybridColumnAnalyzer 集成测试

### 7.2 集成测试

- [ ] 使用海天味业PDF测试（带空格的日期格式）
- [ ] 对比规则和LLM的识别结果
- [ ] 验证用户选择流程

### 7.3 性能测试

- [ ] LLM调用延迟测试
- [ ] 缓存效果测试
- [ ] 批量处理性能测试

## 八、成本估算

### 8.1 API调用成本

Claude 3.5 Sonnet 定价（2024年）：
- 输入：$3 / 1M tokens
- 输出：$15 / 1M tokens

每次表头分析：
- 输入：约200 tokens（系统提示词 + 表头数据）
- 输出：约100 tokens（JSON结果）
- 单次成本：约 $0.002

处理100个PDF（假设每个3页）：
- 总调用次数：300次
- 总成本：约 $0.60

### 8.2 优化建议

1. **缓存机制**：相同表头不重复调用
2. **批量处理**：一次调用分析多个表头
3. **智能触发**：只在规则匹配置信度低时调用LLM

## 九、后续优化

### 9.1 学习机制

- 记录用户选择历史
- 分析用户偏好模式
- 自动优化规则库

### 9.2 主动学习

- 当用户多次选择LLM结果时，提取新的关键字
- 自动更新规则库
- 减少对LLM的依赖

### 9.3 可视化界面

- Web界面展示对比结果
- 可视化差异
- 批量处理和审核

## 十、风险和限制

### 10.1 风险

1. **API成本**：大量调用可能产生费用
2. **延迟**：LLM调用增加处理时间
3. **依赖性**：依赖外部API服务

### 10.2 缓解措施

1. 设置调用限额和预算
2. 实现缓存和批量处理
3. 提供降级方案（纯规则模式）

## 十一、总结

本方案实现了规则匹配和LLM智能识别的有机结合：
- ✅ 保留规则匹配的速度和可控性
- ✅ 增加LLM的智能和灵活性
- ✅ 提供用户选择机制
- ✅ 支持持续学习和优化

预期效果：
- 海天味业等特殊格式：识别准确率 100%
- 整体数据提取准确率：从 67.5% 提升到 95%+
- 用户干预次数：逐步减少（通过学习优化）
