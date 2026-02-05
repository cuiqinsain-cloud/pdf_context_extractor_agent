"""
配置加载器
从 JSON 文件和环境变量加载 LLM 配置
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "llm_config.json"

        self.config_path = Path(config_path)
        self.config = None

    def load_config(self) -> Dict[str, Any]:
        """
        加载配置

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
            ValueError: 配置验证失败
        """
        # 检查配置文件是否存在
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}\n"
                f"请复制模板文件: cp config/llm_config.template.json config/llm_config.json"
            )

        # 读取配置文件
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"配置文件格式错误: {self.config_path}",
                e.doc, e.pos
            )

        # 从环境变量读取 API key
        config = self._load_api_key_from_env(config)

        # 验证配置
        self._validate_config(config)

        self.config = config
        logger.info(f"配置加载成功: {self.config_path}")
        logger.info(f"Provider: {config['llm_api']['provider']}")
        logger.info(f"Model: {config['llm_api']['model']}")

        return config

    def _load_api_key_from_env(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        从环境变量读取 API key

        Args:
            config: 配置字典

        Returns:
            Dict[str, Any]: 更新后的配置字典
        """
        api_key_env = config.get('llm_api', {}).get('api_key_env', 'LLM_API_KEY')

        # 从环境变量读取
        api_key = os.getenv(api_key_env)

        if not api_key:
            logger.warning(
                f"环境变量 {api_key_env} 未设置\n"
                f"请执行: export {api_key_env}='your_api_key'"
            )
            # 不抛出异常，允许在某些情况下不需要 API key（如测试）
            config['llm_api']['api_key'] = None
        else:
            config['llm_api']['api_key'] = api_key
            logger.debug(f"API key 已从环境变量 {api_key_env} 读取")

        return config

    def _validate_config(self, config: Dict[str, Any]):
        """
        验证配置

        Args:
            config: 配置字典

        Raises:
            ValueError: 配置验证失败
        """
        # 验证必填字段
        required_fields = {
            'llm_api': ['provider', 'base_url', 'model', 'api_key_env'],
            'llm_settings': ['enable_llm'],
        }

        for section, fields in required_fields.items():
            if section not in config:
                raise ValueError(f"配置缺少必填部分: {section}")

            for field in fields:
                if field not in config[section]:
                    raise ValueError(f"配置缺少必填字段: {section}.{field}")

        # 验证 provider
        provider = config['llm_api']['provider']
        supported_providers = ['anthropic', 'openrouter', 'chaitin', 'custom', 'ollama']
        if provider not in supported_providers:
            logger.warning(
                f"未知的 provider: {provider}\n"
                f"支持的 provider: {', '.join(supported_providers)}\n"
                f"将作为自定义 provider 处理"
            )

        # 验证 base_url
        base_url = config['llm_api']['base_url']
        if not base_url.startswith(('http://', 'https://')):
            raise ValueError(f"base_url 必须以 http:// 或 https:// 开头: {base_url}")

        # 验证数值范围
        max_tokens = config['llm_api'].get('max_tokens', 1024)
        if not (1 <= max_tokens <= 8192):
            raise ValueError(f"max_tokens 必须在 1-8192 之间: {max_tokens}")

        temperature = config['llm_api'].get('temperature', 0.0)
        if not (0.0 <= temperature <= 1.0):
            raise ValueError(f"temperature 必须在 0.0-1.0 之间: {temperature}")

        timeout = config['llm_api'].get('timeout', 30)
        if not (1 <= timeout <= 300):
            raise ValueError(f"timeout 必须在 1-300 之间: {timeout}")

        logger.debug("配置验证通过")

    def get_llm_api_config(self) -> Dict[str, Any]:
        """
        获取 LLM API 配置

        Returns:
            Dict[str, Any]: LLM API 配置
        """
        if self.config is None:
            self.load_config()

        return self.config['llm_api']

    def get_llm_settings(self) -> Dict[str, Any]:
        """
        获取 LLM 设置

        Returns:
            Dict[str, Any]: LLM 设置
        """
        if self.config is None:
            self.load_config()

        return self.config.get('llm_settings', {})

    def get_performance_config(self) -> Dict[str, Any]:
        """
        获取性能配置

        Returns:
            Dict[str, Any]: 性能配置
        """
        if self.config is None:
            self.load_config()

        return self.config.get('performance', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置

        Returns:
            Dict[str, Any]: 日志配置
        """
        if self.config is None:
            self.load_config()

        return self.config.get('logging', {})


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Dict[str, Any]: 配置字典
    """
    loader = ConfigLoader(config_path)
    return loader.load_config()
