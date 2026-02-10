"""
简单测试LLM连接
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.llm_client import LLMClient


def test_llm_connection():
    """测试LLM连接"""
    # 加载配置
    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'llm_config.json'
    )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 获取API key
    api_key_env = config['llm_api'].get('api_key_env', 'LLM_API_KEY')
    api_key = os.environ.get(api_key_env)

    if not api_key:
        print(f"✗ 环境变量 {api_key_env} 未设置")
        return

    # 构建LLM配置
    llm_config = config['llm_api'].copy()
    llm_config['api_key'] = api_key

    print(f"LLM配置:")
    print(f"  Provider: {llm_config['provider']}")
    print(f"  Model: {llm_config['model']}")
    print(f"  Base URL: {llm_config['base_url']}")
    print(f"  Timeout: {llm_config['timeout']}s")

    # 创建客户端
    client = LLMClient(llm_config)

    # 测试简单调用
    print(f"\n测试简单调用...")
    result = client.call_llm(
        user_prompt="请用一句话介绍你自己。",
        system_prompt="你是一个AI助手。"
    )

    if result['success']:
        print(f"✓ 调用成功")
        print(f"响应: {result['content'][:200]}")
    else:
        print(f"✗ 调用失败: {result.get('error')}")


if __name__ == '__main__':
    test_llm_connection()
