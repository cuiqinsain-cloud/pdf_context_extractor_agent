# LLM API 配置指南

## 一、配置文件说明

配置文件位置：`config/llm_config.json`

### 1.1 基本配置结构

```json
{
  "llm_api": {
    "provider": "anthropic",              // LLM提供商
    "base_url": "https://api.anthropic.com",  // API基础URL
    "model": "claude-3-5-sonnet-20241022",    // 模型名称
    "api_key_env": "LLM_API_KEY",        // API密钥环境变量名
    "max_tokens": 1024,
    "temperature": 0.0,
    "timeout": 30,
    "max_retries": 3
  },
  "llm_settings": { ... },
  "performance": { ... },
  "logging": { ... }
}
```

## 二、环境变量配置

### 2.1 设置 API Key

**方式1：在终端中设置（临时）**
```bash
export LLM_API_KEY="your_api_key_here"
```

**方式2：在 .env 文件中设置（推荐）**
```bash
# 创建 .env 文件
cat > .env << EOF
LLM_API_KEY=your_api_key_here
EOF
```

**方式3：在 shell 配置文件中设置（永久）**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export LLM_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### 2.2 验证环境变量

```bash
echo $LLM_API_KEY
```

## 三、不同 Provider 配置示例

### 3.1 Anthropic Claude（官方）

```json
{
  "llm_api": {
    "provider": "anthropic",
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-5-sonnet-20241022",
    "api_key_env": "LLM_API_KEY"
  }
}
```

**环境变量：**
```bash
export LLM_API_KEY="sk-ant-api03-..."
```

**可用模型：**
- `claude-3-5-sonnet-20241022` - 最新 Sonnet（推荐）
- `claude-3-opus-20240229` - Opus（最强）
- `claude-3-haiku-20240307` - Haiku（最快最便宜）

### 3.2 OpenRouter（多模型聚合平台）

```json
{
  "llm_api": {
    "provider": "openrouter",
    "base_url": "https://openrouter.ai/api/v1",
    "model": "anthropic/claude-3.5-sonnet",
    "api_key_env": "LLM_API_KEY"
  }
}
```

**环境变量：**
```bash
export LLM_API_KEY="sk-or-v1-..."
```

**可用模型：**
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`
- 更多模型见：https://openrouter.ai/models

### 3.3 Azure OpenAI

```json
{
  "llm_api": {
    "provider": "azure",
    "base_url": "https://your-resource.openai.azure.com",
    "model": "gpt-4",
    "api_key_env": "LLM_API_KEY",
    "default_headers": {
      "api-version": "2024-02-15-preview"
    }
  }
}
```

**环境变量：**
```bash
export LLM_API_KEY="your_azure_api_key"
```

### 3.4 自建代理/中转服务

```json
{
  "llm_api": {
    "provider": "custom",
    "base_url": "https://your-proxy.com/v1",
    "model": "claude-3-5-sonnet-20241022",
    "api_key_env": "LLM_API_KEY"
  }
}
```

**环境变量：**
```bash
export LLM_API_KEY="your_proxy_api_key"
```

### 3.5 本地模型（Ollama）

```json
{
  "llm_api": {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3",
    "api_key_env": "LLM_API_KEY",
    "timeout": 120
  }
}
```

**环境变量：**
```bash
export LLM_API_KEY="not_required"  # Ollama 通常不需要 API key
```

## 四、配置参数详解

### 4.1 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `provider` | LLM提供商标识 | `anthropic`, `openrouter`, `azure`, `custom` |
| `base_url` | API基础URL | `https://api.anthropic.com` |
| `model` | 模型名称 | `claude-3-5-sonnet-20241022` |
| `api_key_env` | API密钥环境变量名 | `LLM_API_KEY` |

### 4.2 可选参数

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| `max_tokens` | 最大生成token数 | 1024 | 1-4096 |
| `temperature` | 温度（创造性） | 0.0 | 0.0-1.0 |
| `timeout` | 请求超时时间（秒） | 30 | 1-300 |
| `max_retries` | 最大重试次数 | 3 | 0-10 |

### 4.3 高级参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `default_headers` | 自定义请求头 | `{"api-version": "2024-02-15"}` |
| `proxy` | 代理设置 | `http://proxy.com:8080` |

## 五、配置文件创建步骤

### 步骤1：复制模板文件

```bash
cp config/llm_config.template.json config/llm_config.json
```

### 步骤2：编辑配置文件

```bash
# 使用你喜欢的编辑器
vim config/llm_config.json
# 或
nano config/llm_config.json
```

### 步骤3：填写必填参数

根据你的 LLM 提供商，填写：
- `provider`
- `base_url`
- `model`
- `api_key_env`（通常保持 `LLM_API_KEY`）

### 步骤4：设置环境变量

```bash
export LLM_API_KEY="your_actual_api_key"
```

### 步骤5：验证配置

```bash
python3 tests/test_llm_config.py
```

## 六、安全最佳实践

### 6.1 保护 API Key

❌ **不要这样做：**
```json
{
  "api_key": "sk-ant-api03-xxx"  // 直接写在配置文件中
}
```

✅ **应该这样做：**
```json
{
  "api_key_env": "LLM_API_KEY"  // 从环境变量读取
}
```

### 6.2 .gitignore 配置

确保以下文件不被提交到 Git：
```
# .gitignore
config/llm_config.json
.env
*.log
```

### 6.3 权限设置

```bash
# 限制配置文件权限
chmod 600 config/llm_config.json
chmod 600 .env
```

## 七、故障排查

### 7.1 API Key 未找到

**错误信息：**
```
Error: API key not found in environment variable 'LLM_API_KEY'
```

**解决方法：**
```bash
# 检查环境变量是否设置
echo $LLM_API_KEY

# 如果为空，设置环境变量
export LLM_API_KEY="your_api_key"
```

### 7.2 连接超时

**错误信息：**
```
Error: Connection timeout after 30 seconds
```

**解决方法：**
1. 检查网络连接
2. 增加 `timeout` 值
3. 检查 `base_url` 是否正确
4. 如果在国内，可能需要配置代理

### 7.3 认证失败

**错误信息：**
```
Error: 401 Unauthorized
```

**解决方法：**
1. 检查 API key 是否正确
2. 检查 API key 是否过期
3. 检查 provider 和 base_url 是否匹配

### 7.4 模型不存在

**错误信息：**
```
Error: Model 'xxx' not found
```

**解决方法：**
1. 检查模型名称拼写
2. 确认该 provider 支持该模型
3. 查看 provider 的模型列表文档

## 八、配置示例集合

### 8.1 开发环境（使用 Haiku，成本低）

```json
{
  "llm_api": {
    "provider": "anthropic",
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key_env": "LLM_API_KEY",
    "max_tokens": 512,
    "temperature": 0.0
  },
  "llm_settings": {
    "enable_llm": true,
    "always_use_llm": true,  // 开发时总是调用，便于测试
    "enable_user_choice": true
  }
}
```

### 8.2 生产环境（使用 Sonnet，平衡性能和成本）

```json
{
  "llm_api": {
    "provider": "anthropic",
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-5-sonnet-20241022",
    "api_key_env": "LLM_API_KEY",
    "max_tokens": 1024,
    "temperature": 0.0
  },
  "llm_settings": {
    "enable_llm": true,
    "always_use_llm": false,  // 只在需要时调用
    "auto_accept_if_match": true,
    "fallback_to_rules": true
  },
  "performance": {
    "cache_llm_results": true,
    "cache_ttl": 3600
  }
}
```

### 8.3 离线环境（使用本地模型）

```json
{
  "llm_api": {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3",
    "api_key_env": "LLM_API_KEY",
    "max_tokens": 2048,
    "temperature": 0.0,
    "timeout": 120
  },
  "llm_settings": {
    "enable_llm": true,
    "fallback_to_rules": true
  }
}
```

## 九、环境变量管理工具

### 9.1 使用 python-dotenv

**安装：**
```bash
pip install python-dotenv
```

**使用：**
```python
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 读取环境变量
api_key = os.getenv('LLM_API_KEY')
```

### 9.2 使用 direnv（推荐）

**安装：**
```bash
# macOS
brew install direnv

# Ubuntu/Debian
sudo apt install direnv
```

**配置：**
```bash
# 在项目根目录创建 .envrc
echo 'export LLM_API_KEY="your_api_key"' > .envrc

# 允许 direnv 加载
direnv allow
```

**优点：**
- 自动加载/卸载环境变量
- 进入项目目录自动生效
- 离开项目目录自动失效

## 十、快速开始检查清单

- [ ] 复制配置模板：`cp config/llm_config.template.json config/llm_config.json`
- [ ] 选择 LLM provider（Anthropic/OpenRouter/自定义）
- [ ] 填写 `provider`、`base_url`、`model`
- [ ] 设置环境变量：`export LLM_API_KEY="your_key"`
- [ ] 验证环境变量：`echo $LLM_API_KEY`
- [ ] 测试配置：`python3 tests/test_llm_config.py`
- [ ] 添加 `.env` 到 `.gitignore`
- [ ] 运行实际测试：`python3 tests/test_real_pdf.py`

## 十一、获取 API Key

### Anthropic Claude
1. 访问：https://console.anthropic.com/
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API key
5. 复制 key（格式：`sk-ant-api03-...`）

### OpenRouter
1. 访问：https://openrouter.ai/
2. 注册/登录账号
3. 进入 Keys 页面
4. 创建新的 API key
5. 复制 key（格式：`sk-or-v1-...`）

---

**最后更新：** 2026-02-05
**版本：** v1.0
