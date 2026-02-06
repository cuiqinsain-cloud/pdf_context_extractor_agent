"""
详细的现金流量表测试 - 显示完整性和验证详情
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.cash_flow import CashFlowParser


# 测试配置
TEST_CASES = [
    {
        'name': '福耀玻璃',
        'file': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
        'pages': (96, 97)
    },
    {
        'name': '海尔智家',
        'file': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
        'pages': (124, 126)
    },
    {
        'name': '海天味业',
        'file': 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf',
        'pages': (85, 87)
    },
    {
        'name': '金山办公',
        'file': 'tests/sample_pdfs/金山办公-2024-年报.pdf',
        'pages': (134, 135)
    },
    {
        'name': '深信服',
        'file': 'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        'pages': (127, 128)
    },
]


def test_single_company(test_case):
    """测试单个公司的现金流量表提取"""
    print("\n" + "=" * 80)
    print(f"测试公司: {test_case['name']}")
    print("=" * 80)

    try:
        # 1. 读取PDF并提取表格
        with PDFReader(test_case['file']) as pdf_reader:
            table_extractor = TableExtractor()
            pages = pdf_reader.get_pages(test_case['pages'])
            all_tables = table_extractor.extract_tables_from_pages(pages)

            if not all_tables:
                print("  ✗ 未找到任何表格")
                return False

        # 2. 解析现金流量表
        parser = CashFlowParser()
        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        result = parser.parse_cash_flow(merged_table_data)

        # 3. 验证数据
        validation = parser.validate_cash_flow(result)

        # 4. 输出关键指标
        print(f"\n【关键项目提取情况】")

        # 检查三大活动净额
        operating_net = result['operating_activities'].get('operating_net_cash_flow', {})
        investing_net = result['investing_activities'].get('investing_net_cash_flow', {})
        financing_net = result['financing_activities'].get('financing_net_cash_flow', {})

        print(f"  经营活动净额: {'✓' if operating_net.get('current_period') else '✗'} {operating_net.get('current_period', 'N/A')}")
        print(f"  投资活动净额: {'✓' if investing_net.get('current_period') else '✗'} {investing_net.get('current_period', 'N/A')}")
        print(f"  筹资活动净额: {'✓' if financing_net.get('current_period') else '✗'} {financing_net.get('current_period', 'N/A')}")

        # 检查其他关键项目
        net_increase = result['other_items'].get('net_increase_cash', {})
        ending_balance = result['other_items'].get('ending_cash_balance', {})

        print(f"  现金净增加额: {'✓' if net_increase.get('current_period') else '✗'} {net_increase.get('current_period', 'N/A')}")
        print(f"  期末余额: {'✓' if ending_balance.get('current_period') else '✗'} {ending_balance.get('current_period', 'N/A')}")

        # 5. 显示验证结果
        print(f"\n【验证结果】")
        print(f"  完整性评分: {validation['completeness_score']:.0%}")

        # 层级2验证
        level2_checks = validation['balance_check'].get('level2_net_flow_checks', [])
        if level2_checks:
            print(f"  层级2验证: {sum(1 for c in level2_checks if c['passed'])}/{len(level2_checks)} 通过")
            for check in level2_checks:
                status = "✓" if check['passed'] else "✗"
                print(f"    {status} {check['name']}: 差额={check['difference']:,.2f}")

        # 层级3验证
        level3_checks = validation['balance_check'].get('level3_total_checks', [])
        if level3_checks:
            print(f"  层级3验证: {sum(1 for c in level3_checks if c['passed'])}/{len(level3_checks)} 通过")
            for check in level3_checks:
                status = "✓" if check['passed'] else "✗"
                print(f"    {status} {check['name']}: 差额={check['difference']:,.2f}")

        # 6. 显示警告和错误
        if validation['warnings']:
            print(f"\n【警告】")
            for warning in validation['warnings']:
                print(f"  ⚠️  {warning}")

        if validation['errors']:
            print(f"\n【错误】")
            for error in validation['errors']:
                print(f"  ✗ {error}")

        # 7. 总体评价
        print(f"\n【总体评价】")
        if validation['completeness_score'] >= 1.0:
            print(f"  ✅ 完美 - 所有关键项目均已提取")
        elif validation['completeness_score'] >= 0.8:
            print(f"  ✅ 优秀 - 大部分关键项目已提取")
        elif validation['completeness_score'] >= 0.6:
            print(f"  ⚠️  良好 - 部分关键项目缺失")
        else:
            print(f"  ❌ 需改进 - 大量关键项目缺失")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("现金流量表解析器 - 详细测试报告")
    print("=" * 80)

    results = []

    for test_case in TEST_CASES:
        success = test_single_company(test_case)
        results.append({
            'name': test_case['name'],
            'success': success
        })

    # 总结
    print("\n\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed

    for result in results:
        status = "✓ 通过" if result['success'] else "✗ 失败"
        print(f"{result['name']}: {status}")

    print(f"\n总计: {passed}/{len(results)} 通过")
    print("=" * 80)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
