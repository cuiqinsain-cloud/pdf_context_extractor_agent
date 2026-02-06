"""
真实PDF测试：现金流量表解析器测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.cash_flow import CashFlowParser
import json


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
    print(f"PDF文件: {test_case['file']}")
    print(f"页码范围: {test_case['pages'][0]}-{test_case['pages'][1]}")
    print("=" * 80)

    try:
        # 1. 读取PDF
        print("\n[1/3] 读取PDF...")
        with PDFReader(test_case['file']) as pdf_reader:
            # 2. 提取表格
            print("[2/3] 提取表格...")
            table_extractor = TableExtractor()

            pages = pdf_reader.get_pages(test_case['pages'])
            print(f"  - 获取页面: {test_case['pages'][0]}-{test_case['pages'][1]}")

            all_tables = table_extractor.extract_tables_from_pages(pages)

            if not all_tables:
                print("  ✗ 未找到任何表格")
                return False

            print(f"  ✓ 共提取 {len(all_tables)} 个表格")

        # 3. 解析现金流量表
        print("[3/3] 解析现金流量表...")
        parser = CashFlowParser()

        # 合并所有表格数据
        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        print(f"  - 合并后共 {len(merged_table_data)} 行数据")

        # 解析
        result = parser.parse_cash_flow(merged_table_data)

        # 4. 输出结果
        print("\n" + "-" * 80)
        print("解析结果:")
        print("-" * 80)

        # 统计信息
        parsing_info = result['parsing_info']
        print(f"总行数: {parsing_info['total_rows']}")
        print(f"匹配项目数: {parsing_info['matched_items']}")
        print(f"未匹配项目数: {len(parsing_info['unmatched_items'])}")
        if parsing_info['total_rows'] > 0:
            print(f"匹配率: {parsing_info['matched_items'] / parsing_info['total_rows'] * 100:.1f}%")

        # 经营活动项目
        operating_count = len(result['operating_activities'])
        print(f"\n经营活动项目: {operating_count} 项")
        for key, item in result['operating_activities'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 投资活动项目
        investing_count = len(result['investing_activities'])
        print(f"\n投资活动项目: {investing_count} 项")
        for key, item in result['investing_activities'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 筹资活动项目
        financing_count = len(result['financing_activities'])
        print(f"\n筹资活动项目: {financing_count} 项")
        for key, item in result['financing_activities'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 其他项目
        other_count = len(result['other_items'])
        if other_count > 0:
            print(f"\n其他项目: {other_count} 项")
            for key, item in result['other_items'].items():
                print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 验证数据
        print("\n" + "-" * 80)
        print("数据验证:")
        print("-" * 80)
        validation = parser.validate_cash_flow(result)

        # 显示三层级验证结果
        balance_check = validation.get('balance_check', {})

        # 层级2：净额验证
        level2_checks = balance_check.get('level2_net_flow_checks', [])
        if level2_checks:
            print("\n【层级2：各活动净额验证】")
            for check in level2_checks:
                status = "✓" if check.get('passed') else "✗"
                print(f"  {status} {check.get('name')}: 计算={check['calculated']:,.2f}, 报表={check['reported']:,.2f}, 差额={check['difference']:,.2f}")

        # 层级3：总额验证
        level3_checks = balance_check.get('level3_total_checks', [])
        if level3_checks:
            print("\n【层级3：现金净增加额验证】")
            for check in level3_checks:
                status = "✓" if check.get('passed') else "✗"
                print(f"  {status} {check.get('name')}: 计算={check['calculated']:,.2f}, 报表={check['reported']:,.2f}, 差额={check['difference']:,.2f}")

        print(f"\n完整性评分: {validation['completeness_score']:.1%}")
        print(f"总体验证结果: {'✓ 通过' if validation['is_valid'] else '✗ 失败'}")

        if validation['errors']:
            print(f"\n错误 ({len(validation['errors'])}):")
            for error in validation['errors']:
                print(f"  - {error}")

        if validation['warnings']:
            print(f"\n警告 ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"  - {warning}")

        # 未匹配项目（只显示前5个）
        if parsing_info['unmatched_items']:
            print(f"\n未匹配项目 (前5个):")
            for item in parsing_info['unmatched_items'][:5]:
                print(f"  - 第{item['row_index']}行: {item['item_name']}")

        print("\n" + "=" * 80)
        print(f"✓ {test_case['name']} 测试完成")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("真实PDF测试 - 现金流量表解析器")
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
