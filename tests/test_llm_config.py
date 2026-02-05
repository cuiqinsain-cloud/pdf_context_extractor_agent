#!/usr/bin/env python3
"""
测试 LLM 配置
验证配置文件和环境变量是否正确设置
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.config_loader import ConfigLoader

def test_config():
    """测试配置加载"""

    print("=" * 80)
    print("测试 LLM 配置")
    print("=" * 80)

    try:
        # 加载配置
        print("\n[1/4] 加载配置文件...")
        loader = ConfigLoader()
        config = loader.load_config()
        print("  ✓ 配置文件加载成功")

        # 显示 LLM API 配置
        print("\n[2/4] LLM API 配置:")
        llm_api = config['llm_api']
        print(f"  - Provider: {llm_api['provider']}")
        print(f"  - Base URL: {llm_api['base_url']}")
        print(f"  - Model: {llm_api['model']}")
        print(f"  - API Key: {'已设置' if llm_api.get('api_key') else '未设置'}")
        print(f"  - Max Tokens: {llm_api.get('max_tokens', 1024)}")
        print(f"  - Temperature: {llm_api.get('temperature', 0.0)}")

        # 显示 LLM 设置
        print("\n[3/4] LLM 功能设置:")
        llm_settings = config.get('llm_settings', {})
        print(f"  - 启用LLM: {llm_settings.get('enable_llm', False)}")
        print(f"  - 启用对比: {llm_settings.get('enable_comparison', True)}")
        print(f"  - 启用用户选择: {llm_settings.get('enable_user_choice', True)}")
        print(f"  - 总是使用LLM: {llm_settings.get('always_use_llm', False)}")
        print(f"  - 回退到规则: {llm_settings.get('fallback_to_rules', True)}")

        # 检查 API Key
        print("\n[4/4] 检查 API Key...")
        if llm_api.get('api_key'):
            api_key = llm_api['api_key']
            masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
            print(f"  ✓ API Key 已设置: {masked_key}")
        else:
            print(f"  ✗ API Key 未设置")
            print(f"\n  请设置环境变量:")
            api_key_env = llm_api.get('api_key_env', 'LLM_API_KEY')
            print(f"    export {api_key_env}='your_api_key'")

        print("\n" + "=" * 80)
        print("✓ 配置测试完成")
        print("=" * 80)

        return True

    except FileNotFoundError as e:
        print(f"\n✗ 配置文件不存在: {e}")
        print("\n请按照以下步骤配置:")
        print("  1. 复制配置模板:")
        print("     cp config/llm_config.template.json config/llm_config.json")
        print("  2. 编辑配置文件，填写必要参数")
        print("  3. 设置环境变量:")
        print("     export LLM_API_KEY='your_api_key'")
        return False

    except Exception as e:
        print(f"\n✗ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_config()
    sys.exit(0 if success else 1)
