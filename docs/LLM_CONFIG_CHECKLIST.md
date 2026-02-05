# LLM 配置参数清单

## 📋 必填参数（请您补充）

### 1. LLM API 配置

| 参数 | 说明 | 您的配置 | 示例 |
|------|------|---------|------|
| **provider** | LLM提供商 | `_____________` | `anthropic` / `openrouter` / `custom` |
| **base_url** | API基础URL | `_____________` | `https://api.anthropic.com` |
| **model** | 模型名称 | `_____________` | `claude-3-5-sonnet-20241022` |
| **api_key_env** | API密钥环境变量名 | `LLM_API_KEY` | 通常保持默认 |

### 2. 环境变量

```bash
# 请在终端执行或添加到 .env 文件
export LLM_API_KEY="___________________________"
```

---

## ⚙️ 可选参数（可保持默认值）

### 3. API 调用参数

| 参数 | 默认值 | 说明 | 建议值 |
|------|--------|------|--------|
| **max_tokens** | 1024 | 最大生成token数 | 开发: 512, 生产: 1024 |
| **temperature** | 0.0 | 温度（0=确定性，1=创造性） | 保持 0.0（需要确定性） |
| **timeout** | 30 | 请求超时时间（秒） | 网络好: 30, 网络差: 60 |
| **max_retries** | 3 | 最大重试次数 | 保持 3 |

### 4. 功能开关

| 参数 | 默认值 | 说明 | 建议 |
|------|--------|------|------|
| **enable_llm** | true | 是否启用LLM识别 | 开发/生产: true |
| **enable_comparison** | true | 是否启用结果对比 | 保持 true |
| **enable_user_choice** | true | 是否启用用户选择 | 保持 true |
| **always_use_llm** | false | 是否总是调用LLM | 开发: true, 生产: false |
| **fallback_to_rules** | true | LLM失败时回退到规则 | 保持 true |

### 5. 对比策略

| 参数 | 默认值 | 说明 | 建议 |
|------|--------|------|------|
| **confidence_threshold** | 0.7 | 置信度阈值 | 保持 0.7 |
| **auto_accept_if_match** | true | 结果一致时自动接受 | 保持 true |
| **comparison_mode** | "strict" | 对比模式 | strict / lenient |
| **allow_partial_match** | false | 是否允许部分匹配 | 保持 false |

### 6. 用户交互

| 参数 | 默认值 | 说明 | 建议 |
|------|--------|------|------|
| **choice_timeout** | 60 | 用户选择超时时间（秒） | 保持 60 |
| **default_choice** | "rules" | 超时时的默认选择 | rules / llm / skip |
| **save_choices** | true | 是否保存用户选择历史 | 保持 true |

### 7. 性能优化

| 参数 | 默认值 | 说明 | 建议 |
|------|--------|------|------|
| **cache_llm_results** | true | 是否缓存LLM结果 | 保持 true（节省成本） |
| **cache_ttl** | 3600 | 缓存有效期（秒） | 保持 3600（1小时） |

### 8. 日志配置

| 参数 | 默认值 | 说明 | 建议 |
|------|--------|------|------|
| **log_llm_requests** | true | 是否记录LLM请求 | 开发: true, 生产: false |
| **log_llm_responses** | true | 是否记录LLM响应 | 开发: true, 生产: false |
| **log_comparisons** | true | 是否记录对比结果 | 保持 true |
| **log_user_choices** | true | 是否记录用户选择 | 保持 true |

---

## 🎯 推荐配置方案

### 方案A：Anthropic Claude（官方）

```
provider: anthropic
base_url: https://api.anthropic.com
model: claude-3-5-sonnet-20241022
环境变量: export LLM_API_KEY="sk-ant-api03-..."
```

**优点：** 官方服务，稳定可靠，性能最佳
**成本：** 输入 $3/1M tokens，输出 $15/1M tokens

### 方案B：OpenRouter（多模型平台）

```
provider: openrouter
base_url: https://openrouter.ai/api/v1
model: anthropic/claude-3.5-sonnet
环境变量: export LLM_API_KEY="sk-or-v1-..."
```

**优点：** 支持多种模型，统一接口，可能有优惠
**成本：** 根据选择的模型而定

### 方案C：自定义代理/中转

```
provider: custom
base_url: 您的代理地址
model: claude-3-5-sonnet-20241022
环境变量: export LLM_API_KEY="您的代理密钥"
```

**优点：** 灵活可控，可能解决网络问题
**成本：** 根据代理服务商而定

---

## 📝 配置步骤

### 步骤1：选择方案
- [ ] 我选择方案：_________ (A/B/C)

### 步骤2：填写必填参数
- [ ] provider: _____________
- [ ] base_url: _____________
- [ ] model: _____________

### 步骤3：获取 API Key
- [ ] 已注册账号
- [ ] 已获取 API Key
- [ ] API Key 格式：_____________

### 步骤4：设置环境变量
- [ ] 已执行：`export LLM_API_KEY="..."`
- [ ] 已验证：`echo $LLM_API_KEY`

### 步骤5：创建配置文件
- [ ] 已复制模板：`cp config/llm_config.template.json config/llm_config.json`
- [ ] 已编辑配置文件
- [ ] 已填写必填参数

### 步骤6：测试配置
- [ ] 已运行测试：`python3 tests/test_llm_config.py`
- [ ] 测试通过

---

## 🔍 配置验证

完成配置后，请运行以下命令验证：

```bash
# 1. 检查环境变量
echo $LLM_API_KEY

# 2. 检查配置文件
cat config/llm_config.json

# 3. 测试 LLM 连接
python3 tests/test_llm_config.py

# 4. 运行完整测试
python3 tests/test_real_pdf.py
```

---

## ❓ 常见问题

### Q1: 我应该选择哪个模型？

**推荐：** `claude-3-5-sonnet-20241022`
- 性能和成本的最佳平衡
- 适合生产环境
- 准确率高

**备选：**
- `claude-3-haiku-20240307` - 开发测试用（便宜）
- `claude-3-opus-20240229` - 最高准确率（贵）

### Q2: API Key 应该放在哪里？

**推荐：** 环境变量（最安全）
```bash
export LLM_API_KEY="your_key"
```

**不推荐：** 直接写在配置文件中（不安全）

### Q3: 如何降低成本？

1. 启用缓存：`cache_llm_results: true`
2. 只在需要时调用：`always_use_llm: false`
3. 使用更便宜的模型：`claude-3-haiku-20240307`
4. 减少 max_tokens：`max_tokens: 512`

### Q4: 如何提高准确率？

1. 使用更强的模型：`claude-3-opus-20240229`
2. 增加 max_tokens：`max_tokens: 2048`
3. 启用用户选择：`enable_user_choice: true`
4. 保存用户选择用于学习：`save_choices: true`

---

## 📞 需要帮助？

如果您在配置过程中遇到问题，请：

1. 查看详细配置指南：`docs/LLM_CONFIG_GUIDE.md`
2. 查看设计文档：`docs/design/llm_integration_design.md`
3. 运行诊断脚本：`python3 tests/diagnose_llm_config.py`

---

**最后更新：** 2026-02-05
