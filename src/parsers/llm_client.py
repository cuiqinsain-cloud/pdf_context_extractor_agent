"""
通用 LLM 客户端
支持多种 LLM provider（Anthropic、OpenRouter、Chaitin 等）
"""
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """LLM 提供商类型"""
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    CHAITIN = "chaitin"
    CUSTOM = "custom"
    OLLAMA = "ollama"


class LLMClient:
    """通用 LLM 客户端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端

        Args:
            config: LLM API 配置
        """
        self.provider = config.get('provider', 'custom')
        self.base_url = config.get('base_url')
        self.model = config.get('model')
        self.api_key = config.get('api_key')
        self.max_tokens = config.get('max_tokens', 1024)
        self.temperature = config.get('temperature', 0.0)
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.default_headers = config.get('default_headers', {})
        self.proxy = config.get('proxy')

        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

        logger.info(f"LLM 客户端初始化: provider={self.provider}, model={self.model}")

    def call_llm(self, user_prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        通用 LLM 调用方法

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词（可选，如果不提供则使用默认的）

        Returns:
            Dict[str, Any]: LLM 响应结果
                {
                    'success': bool,
                    'content': str,  # LLM 返回的文本内容
                    'error': str  # 如果失败
                }
        """
        if not self.api_key:
            logger.error("API key 未设置，无法调用 LLM")
            return {
                'success': False,
                'error': 'API key not set',
                'content': ''
            }

        # 使用提供的系统提示词，或使用默认的
        sys_prompt = system_prompt if system_prompt else self.system_prompt

        # 根据 provider 类型调用不同的 API
        try:
            if self.provider == ProviderType.ANTHROPIC.value:
                result = self._call_anthropic_api_generic(user_prompt, sys_prompt)
            elif self.provider == ProviderType.CHAITIN.value:
                result = self._call_openai_compatible_api_generic(user_prompt, sys_prompt)
            elif self.provider == ProviderType.OPENROUTER.value:
                result = self._call_openai_compatible_api_generic(user_prompt, sys_prompt)
            elif self.provider == ProviderType.OLLAMA.value:
                result = self._call_ollama_api_generic(user_prompt, sys_prompt)
            else:
                # 默认使用 OpenAI 兼容格式
                result = self._call_openai_compatible_api_generic(user_prompt, sys_prompt)

            return result

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'content': ''
            }

    def analyze_header(self, header_row: List[str]) -> Dict[str, Any]:
        """
        使用 LLM 分析表头

        Args:
            header_row: 表头行数据

        Returns:
            Dict[str, Any]: 分析结果
                {
                    'success': bool,
                    'column_map': Dict[str, int],
                    'confidence': float,
                    'reasoning': str,
                    'raw_response': str
                }
        """
        if not self.api_key:
            logger.error("API key 未设置，无法调用 LLM")
            return {
                'success': False,
                'error': 'API key not set',
                'column_map': {},
                'confidence': 0.0
            }

        # 构建用户提示词
        user_prompt = self._build_user_prompt(header_row)

        # 根据 provider 类型调用不同的 API
        try:
            if self.provider == ProviderType.ANTHROPIC.value:
                result = self._call_anthropic_api(user_prompt)
            elif self.provider == ProviderType.CHAITIN.value:
                result = self._call_openai_compatible_api(user_prompt)
            elif self.provider == ProviderType.OPENROUTER.value:
                result = self._call_openai_compatible_api(user_prompt)
            elif self.provider == ProviderType.OLLAMA.value:
                result = self._call_ollama_api(user_prompt)
            else:
                # 默认使用 OpenAI 兼容格式
                result = self._call_openai_compatible_api(user_prompt)

            return result

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'column_map': {},
                'confidence': 0.0
            }

    def _call_anthropic_api_generic(self, user_prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        调用 Anthropic Claude API（通用版本）

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            Dict[str, Any]: 响应结果
        """
        url = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            **self.default_headers
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 Anthropic 响应格式
            content = response['data']['content'][0]['text']
            return {
                'success': True,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'content': ''
            }

    def _call_openai_compatible_api_generic(self, user_prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        调用 OpenAI 兼容 API（通用版本）

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            Dict[str, Any]: 响应结果
        """
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 OpenAI 兼容响应格式
            content = response['data']['choices'][0]['message']['content']
            return {
                'success': True,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'content': ''
            }

    def _call_ollama_api_generic(self, user_prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        调用 Ollama API（通用版本）

        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词

        Returns:
            Dict[str, Any]: 响应结果
        """
        url = f"{self.base_url}/api/generate"

        headers = {
            "Content-Type": "application/json"
        }

        # Ollama 使用不同的格式
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 Ollama 响应格式
            content = response['data']['response']
            return {
                'success': True,
                'content': content
            }
        else:
            return {
                'success': False,
                'error': response.get('error', 'Unknown error'),
                'content': ''
            }

    def _call_anthropic_api(self, user_prompt: str) -> Dict[str, Any]:
        """
        调用 Anthropic Claude API

        Args:
            user_prompt: 用户提示词

        Returns:
            Dict[str, Any]: 分析结果
        """
        url = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            **self.default_headers
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": self.system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 Anthropic 响应格式
            content = response['data']['content'][0]['text']
            return self._parse_llm_response(content)
        else:
            return response

    def _call_openai_compatible_api(self, user_prompt: str) -> Dict[str, Any]:
        """
        调用 OpenAI 兼容 API（适用于 Chaitin、OpenRouter 等）

        Args:
            user_prompt: 用户提示词

        Returns:
            Dict[str, Any]: 分析结果
        """
        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.default_headers
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 OpenAI 兼容响应格式
            content = response['data']['choices'][0]['message']['content']
            return self._parse_llm_response(content)
        else:
            return response

    def _call_ollama_api(self, user_prompt: str) -> Dict[str, Any]:
        """
        调用 Ollama API

        Args:
            user_prompt: 用户提示词

        Returns:
            Dict[str, Any]: 分析结果
        """
        url = f"{self.base_url}/api/generate"

        headers = {
            "Content-Type": "application/json"
        }

        # Ollama 使用不同的格式
        full_prompt = f"{self.system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        response = self._make_request(url, headers, payload)

        if response['success']:
            # 解析 Ollama 响应格式
            content = response['data']['response']
            return self._parse_llm_response(content)
        else:
            return response

    def _make_request(self, url: str, headers: Dict[str, str],
                     payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            url: 请求 URL
            headers: 请求头
            payload: 请求体

        Returns:
            Dict[str, Any]: 响应结果
        """
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"发送 LLM 请求 (尝试 {attempt + 1}/{self.max_retries})")
                logger.debug(f"URL: {url}")
                logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False)[:200]}...")

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                    proxies=proxies
                )

                response.raise_for_status()

                data = response.json()
                logger.debug(f"LLM 响应成功")

                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status_code
                }

            except requests.exceptions.Timeout:
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': f'Request timeout after {self.timeout}s',
                        'column_map': {},
                        'confidence': 0.0
                    }

            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP 错误: {e}")
                return {
                    'success': False,
                    'error': f'HTTP error: {e}',
                    'column_map': {},
                    'confidence': 0.0
                }

            except Exception as e:
                logger.error(f"请求失败: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'error': str(e),
                        'column_map': {},
                        'confidence': 0.0
                    }

        return {
            'success': False,
            'error': 'Max retries exceeded',
            'column_map': {},
            'confidence': 0.0
        }

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        解析 LLM 响应内容

        Args:
            content: LLM 返回的文本内容

        Returns:
            Dict[str, Any]: 解析后的结果
        """
        try:
            # 记录原始响应（用于调试）
            logger.debug(f"LLM 原始响应长度: {len(content)} 字符")
            logger.debug(f"LLM 原始响应: {content[:500]}...")  # 只显示前500字符

            # 尝试提取 JSON（可能被包裹在 markdown 代码块中）
            content = content.strip()

            # 移除可能的 markdown 代码块标记
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]

            if content.endswith('```'):
                content = content[:-3]

            content = content.strip()

            # 尝试修复不完整的 JSON
            # 如果 JSON 被截断，尝试补全
            if not content.endswith('}'):
                logger.warning("检测到不完整的 JSON，尝试修复")
                # 尝试找到最后一个完整的字段
                if '"reasoning"' in content:
                    # 如果有 reasoning 字段但不完整，尝试补全
                    content = content.rstrip(',\n ')
                    if not content.endswith('}'):
                        content += '\n}'
                elif '"confidence"' in content:
                    # 如果只有 confidence 但不完整，添加默认 reasoning
                    content = content.rstrip(',\n ')
                    if not content.endswith('}'):
                        content += ',\n  "reasoning": "Response truncated"\n}'
                else:
                    # 其他情况，直接补全
                    content += '\n}'

            # 解析 JSON
            result = json.loads(content)

            return {
                'success': True,
                'column_map': result.get('column_map', {}),
                'confidence': result.get('confidence', 0.0),
                'reasoning': result.get('reasoning', ''),
                'raw_response': content
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"原始内容: {content}")
            return {
                'success': False,
                'error': f'JSON parse error: {e}',
                'column_map': {},
                'confidence': 0.0,
                'raw_response': content
            }

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        Returns:
            str: 系统提示词
        """
        return """你是一个专业的财务报表分析专家，擅长识别中国A股上市公司年报中的资产负债表结构。

你的任务是分析表头行，识别每一列的类型：
- item_name: 项目名称/科目名称（通常是第一列）
- current_period: 期末/本期末/本年末数据（通常包含当前年份或"期末"等关键字）
- previous_period: 期初/上期末/上年末数据（通常包含上一年份或"期初"等关键字）
- note: 附注/注释编号（通常包含"附注"、"注"等关键字）

重要提示：
1. 日期格式可能包含空格，如"2024 年12月 31日"或"2024年12月31日"
2. 期末列通常在期初列之前（从左到右）
3. 项目名称列通常是第一列（索引0）
4. 列索引从0开始计数

请仔细分析每一列的文本内容，给出你的判断和理由。"""

    def _build_user_prompt(self, header_row: List[str]) -> str:
        """
        构建用户提示词

        Args:
            header_row: 表头行数据

        Returns:
            str: 用户提示词
        """
        return f"""请分析以下表头行，识别每一列的类型：

表头数据（共{len(header_row)}列）：
{json.dumps(header_row, ensure_ascii=False, indent=2)}

请以JSON格式返回结果（不要包含任何其他文字说明）：
{{
  "column_map": {{
    "item_name": 列索引,
    "current_period": 列索引,
    "previous_period": 列索引,
    "note": 列索引
  }},
  "confidence": 0.95,
  "reasoning": "详细的分析理由，说明为什么这样判断"
}}

注意：
1. 列索引从0开始
2. 如果某个列类型不存在，不要包含在column_map中
3. confidence 是0.0-1.0之间的置信度
4. reasoning 要详细说明你的判断依据"""
