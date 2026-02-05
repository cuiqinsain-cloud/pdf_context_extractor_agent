# 环境配置指南

本文档详细说明如何配置项目开发环境。

---

## 一、基础环境

### 1.1 系统要求

- **操作系统**: macOS / Linux / Windows
- **Python版本**: 3.8+
- **磁盘空间**: 至少500MB

### 1.2 必需软件

- Python 3.8或更高版本
- pip（Python包管理器）
- git（版本控制）

---

## 二、虚拟环境配置（重要！）

### 2.1 为什么使用虚拟环境？

虚拟环境可以：
- ✅ 隔离项目依赖，避免与系统Python包冲突
- ✅ 确保依赖版本一致
- ✅ 便于项目迁移和部署

**⚠️ 重要**: 本项目所有命令都必须在虚拟环境中执行！

### 2.2 创建虚拟环境

```bash
# 进入项目目录
cd pdf_context_extractor_agent

# 创建虚拟环境
python3 -m venv venv

# 验证虚拟环境已创建
ls venv/
# 应该看到: bin/ include/ lib/ pyvenv.cfg
```

### 2.3 激活虚拟环境

**macOS / Linux**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

**验证激活成功**:
```bash
which python
# 应该显示: /path/to/pdf_context_extractor_agent/venv/bin/python

python --version
# 应该显示: Python 3.8+
```

### 2.4 退出虚拟环境

```bash
deactivate
```

### 2.5 常见问题

**Q: 忘记激活虚拟环境怎么办？**
A: 如果运行命令时出现"ModuleNotFoundError"，很可能是忘记激活虚拟环境。重新执行 `source venv/bin/activate`。

**Q: 如何确认当前在虚拟环境中？**
A: 命令行提示符前会显示 `(venv)`，例如：
```
(venv) user@host:~/pdf_context_extractor_agent$
```

---

## 三、安装依赖

### 3.1 基础依赖

```bash
# 确保已激活虚拟环境
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt
```

### 3.2 依赖列表

```
# PDF处理
pdfplumber>=0.10.0
PyPDF2>=3.0.0

# 数据处理
pandas>=2.0.0
openpyxl>=3.1.0

# 工具库
python-dateutil>=2.8.0

# LLM集成
requests>=2.31.0
```

### 3.3 验证安装

```bash
# 测试导入
python -c "import pdfplumber, pandas, openpyxl, requests"

# 如果没有错误，说明安装成功
```

---

## 四、LLM功能配置（可选）

### 4.1 配置文件

```bash
# 复制配置模板
cp config/llm_config.template.json config/llm_config.json

# 编辑配置文件
vim config/llm_config.json  # 或使用其他编辑器
```

### 4.2 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| **provider** | LLM提供商 | `anthropic` / `openrouter` / `custom` |
| **base_url** | API基础URL | `https://api.anthropic.com` |
| **model** | 模型名称 | `claude-3-5-sonnet-20241022` |
| **api_key_env** | API密钥环境变量名 | `LLM_API_KEY` |

**配置示例**:
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

### 4.3 设置API Key

**方式1: 临时设置（推荐用于测试）**
```bash
export LLM_API_KEY="your_api_key_here"
```

**方式2: 永久设置（推荐用于开发）**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export LLM_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**方式3: 使用 .env 文件**
```bash
# 创建 .env 文件
cat > .env << EOF
LLM_API_KEY=your_api_key_here
EOF

# 注意：.env 文件已在 .gitignore 中，不会被提交
```

### 4.4 常用Provider配置

**Anthropic Claude（官方，推荐）**:
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
- 环境变量: `export LLM_API_KEY="sk-ant-api03-..."`
- 获取API Key: https://console.anthropic.com/

**OpenRouter（多模型平台）**:
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
- 环境变量: `export LLM_API_KEY="sk-or-v1-..."`
- 获取API Key: https://openrouter.ai/

**自定义代理/中转**:
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

### 4.5 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| **max_tokens** | 1024 | 最大生成token数 |
| **temperature** | 0.0 | 温度（0=确定性，1=创造性） |
| **timeout** | 30 | 请求超时时间（秒） |
| **max_retries** | 3 | 最大重试次数 |
| **enable_llm** | true | 是否启用LLM识别 |
| **always_use_llm** | false | 是否总是调用LLM |
| **cache_llm_results** | true | 是否缓存LLM结果 |

### 4.6 验证配置

```bash
# 激活虚拟环境
source venv/bin/activate

# 检查环境变量
echo $LLM_API_KEY

# 运行配置测试
python tests/test_llm_config.py

# 应该看到:
# ✓ 配置文件加载成功
# ✓ API Key 已设置
```

---

## 五、开发工具配置（可选）

### 5.1 IDE配置

**VS Code**:
1. 安装Python扩展
2. 选择虚拟环境作为Python解释器
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - 选择 `./venv/bin/python`

**PyCharm**:
1. File → Settings → Project → Python Interpreter
2. 添加虚拟环境：`./venv/bin/python`

### 5.2 代码格式化

```bash
# 安装开发工具（可选）
pip install black flake8 pylint

# 格式化代码
black src/

# 检查代码风格
flake8 src/
```

---

## 六、测试环境验证

### 6.1 运行测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有测试
python tests/test_column_analyzer.py
python tests/test_integration.py
python tests/test_real_pdf.py

# 如果配置了LLM
python tests/test_llm_integration.py
```

### 6.2 预期结果

```
✓ 单元测试: 7/7 通过
✓ 集成测试: 3/3 通过
✓ 真实PDF测试: 4/4 通过
```

---

## 七、常见问题排查

### 7.1 虚拟环境问题

**问题**: `command not found: python3`
**解决**:
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install python3

# 验证
python3 --version
```

**问题**: 虚拟环境创建失败
**解决**:
```bash
# 确保有venv模块
python3 -m pip install --user virtualenv

# 使用virtualenv创建
python3 -m virtualenv venv
```

### 7.2 依赖安装问题

**问题**: `pip install` 失败
**解决**:
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**问题**: 权限错误
**解决**:
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 不要使用sudo
pip install -r requirements.txt
```

### 7.3 LLM配置问题

**问题**: API Key未找到
**解决**:
```bash
# 检查环境变量
echo $LLM_API_KEY

# 如果为空，重新设置
export LLM_API_KEY="your_key"
```

**问题**: 配置文件不存在
**解决**:
```bash
# 复制模板
cp config/llm_config.template.json config/llm_config.json
```

**问题**: API请求超时
**解决**:
1. 检查网络连接
2. 验证API Key是否有效
3. 增加timeout配置（在llm_config.json中设置 `"timeout": 60`）

**问题**: 认证失败 (401 Unauthorized)
**解决**:
1. 检查API Key是否正确
2. 检查provider和base_url是否匹配
3. 确认API Key未过期

**问题**: 模型不存在
**解决**:
1. 检查模型名称拼写
2. 确认provider支持该模型
3. 参考上面的Provider配置示例

---

## 八、环境清理

### 8.1 清理虚拟环境

```bash
# 退出虚拟环境
deactivate

# 删除虚拟环境
rm -rf venv/

# 重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 8.2 清理缓存

```bash
# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理输出文件
rm -rf output/*.xlsx

# 清理日志
rm -rf logs/*.log
```

---

## 九、快速配置检查清单

使用前请确认：

- [ ] Python 3.8+ 已安装
- [ ] 虚拟环境已创建 (`venv/` 目录存在)
- [ ] 虚拟环境已激活 (命令行显示 `(venv)`)
- [ ] 依赖已安装 (`pip list` 显示所有包)
- [ ] 测试PDF文件存在 (`tests/sample_pdfs/` 目录)
- [ ] (可选) LLM配置文件已创建 (`config/llm_config.json`)
- [ ] (可选) API Key已设置 (`echo $LLM_API_KEY` 有输出)

---

## 十、下一步

环境配置完成后，您可以：

1. 阅读 [功能说明](FEATURES.md) 了解详细功能
2. 查看 [快速开始指南](guides/quick_start.md) 开始使用
3. 查看 [开发进展](DEVELOPMENT.md) 了解项目状态

---

**最后更新**: 2026-02-05
