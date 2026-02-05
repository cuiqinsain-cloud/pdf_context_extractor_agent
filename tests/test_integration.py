"""
集成测试：验证 ColumnAnalyzer 与 BalanceSheetParser 的集成
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.balance_sheet import BalanceSheetParser


def test_basic_integration():
    """测试基本集成功能"""
    print("=" * 60)
    print("测试1: 基本集成功能")
    print("=" * 60)

    # 测试数据：标准4列格式
    table_data = [
        ['项目', '附注', '2024年12月31日', '2023年12月31日'],
        ['流动资产：', '', '', ''],
        ['货币资金', '七、1', '1000000.00', '900000.00'],
        ['应收账款', '七、2', '500000.00', '450000.00'],
        ['流动资产合计', '', '1500000.00', '1350000.00'],
    ]

    parser = BalanceSheetParser()
    result = parser.parse_balance_sheet(table_data)

    print(f"✓ 匹配项目数: {result['parsing_info']['matched_items']}")
    print(f"✓ 未匹配项目数: {len(result['parsing_info']['unmatched_items'])}")

    # 验证数据提取
    if '货币资金' in result['assets']['current_assets']:
        item = result['assets']['current_assets']['货币资金']
        print(f"✓ 货币资金 - 本期: {item.get('current_period')}, 上期: {item.get('previous_period')}")
        assert item.get('current_period') == '1000000.00'
        assert item.get('previous_period') == '900000.00'
    else:
        print("✗ 未找到货币资金")
        return False

    print("✓ 测试1通过\n")
    return True


def test_cross_page_format_change():
    """测试跨页列数变化"""
    print("=" * 60)
    print("测试2: 跨页列数变化")
    print("=" * 60)

    # 模拟跨页情况：第一页4列，第二页3列
    table_data = [
        ['项目', '附注', '期末余额', '期初余额'],
        ['货币资金', '七、1', '1000000.00', '900000.00'],
        # 跨页后变成3列
        ['应收账款', '500000.00', '450000.00'],
        ['存货', '300000.00', '280000.00'],
    ]

    parser = BalanceSheetParser()
    result = parser.parse_balance_sheet(table_data)

    print(f"✓ 匹配项目数: {result['parsing_info']['matched_items']}")

    # 验证第一页数据（4列）
    if '货币资金' in result['assets']['current_assets']:
        item = result['assets']['current_assets']['货币资金']
        print(f"✓ 货币资金(4列) - 本期: {item.get('current_period')}, 上期: {item.get('previous_period')}")
    else:
        print("✗ 未找到货币资金")
        return False

    # 验证第二页数据（3列）
    if '应收账款' in result['assets']['current_assets']:
        item = result['assets']['current_assets']['应收账款']
        print(f"✓ 应收账款(3列) - 本期: {item.get('current_period')}, 上期: {item.get('previous_period')}")
    else:
        print("✗ 未找到应收账款")
        return False

    print("✓ 测试2通过\n")
    return True


def test_various_header_formats():
    """测试各种表头格式"""
    print("=" * 60)
    print("测试3: 各种表头格式")
    print("=" * 60)

    test_cases = [
        {
            'name': '格式1: 期末/期初',
            'data': [
                ['项目', '期末余额', '期初余额'],
                ['货币资金', '1000000.00', '900000.00'],
            ]
        },
        {
            'name': '格式2: 本期末/上期末',
            'data': [
                ['项目', '本期末', '上期末'],
                ['货币资金', '1000000.00', '900000.00'],
            ]
        },
        {
            'name': '格式3: 年末余额/年初余额',
            'data': [
                ['项目', '年末余额', '年初余额'],
                ['货币资金', '1000000.00', '900000.00'],
            ]
        },
    ]

    parser = BalanceSheetParser()

    for test_case in test_cases:
        print(f"\n  {test_case['name']}")
        result = parser.parse_balance_sheet(test_case['data'])

        if '货币资金' in result['assets']['current_assets']:
            item = result['assets']['current_assets']['货币资金']
            print(f"  ✓ 本期: {item.get('current_period')}, 上期: {item.get('previous_period')}")
        else:
            print(f"  ✗ 未找到货币资金")
            return False

    print("\n✓ 测试3通过\n")
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ColumnAnalyzer 集成测试")
    print("=" * 60 + "\n")

    tests = [
        test_basic_integration,
        test_cross_page_format_change,
        test_various_header_formats,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ 测试失败: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
