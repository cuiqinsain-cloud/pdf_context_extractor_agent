"""
真实PDF测试：利润表解析器测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.income_statement import IncomeStatementParser
import json


# 测试配置
TEST_CASES = [
    {
        'name': '福耀玻璃',
        'file': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
        'pages': (93, 95)
    },
    {
        'name': '海尔智家',
        'file': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
        'pages': (121, 123)
    },
    {
        'name': '海天味业',
        'file': 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf',
        'pages': (81, 83)
    },
    {
        'name': '金山办公',
        'file': 'tests/sample_pdfs/金山办公-2024-年报.pdf',
        'pages': (130, 132)
    },
]


def test_single_company(test_case):
    """测试单个公司的利润表提取"""
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

        # 3. 解析利润表
        print("[3/3] 解析利润表...")
        parser = IncomeStatementParser()

        # 合并所有表格数据
        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        print(f"  - 合并后共 {len(merged_table_data)} 行数据")

        # 解析
        result = parser.parse_income_statement(merged_table_data)

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

        # 营业收入项目
        revenue_count = len(result['revenue'])
        print(f"\n营业收入项目: {revenue_count} 项")
        for key, item in result['revenue'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 营业成本项目
        cost_count = len(result['costs'])
        print(f"\n营业成本项目: {cost_count} 项")
        for key, item in result['costs'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 利润项目
        profit_count = len(result['profit'])
        print(f"\n利润项目: {profit_count} 项")
        for key, item in result['profit'].items():
            print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 每股收益
        eps_count = len(result['eps'])
        if eps_count > 0:
            print(f"\n每股收益: {eps_count} 项")
            for key, item in result['eps'].items():
                print(f"  - {key}: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 验证数据
        print("\n" + "-" * 80)
        print("数据验证:")
        print("-" * 80)
        validation = parser.validate_income_statement(result)

        # 显示三层级验证结果
        balance_check = validation.get('balance_check', {})

        # 层级1：子项目合计
        level1_checks = balance_check.get('level1_subtotal_checks', [])
        if level1_checks:
            print("\n【层级1：子项目合计验证】")
            for check in level1_checks:
                status = "✓" if check.get('passed') else "✗"
                print(f"  {status} {check.get('name')}: ", end="")
                if check.get('calculated') is not None:
                    print(f"计算={check['calculated']:,.2f}, 报表={check['reported']:,.2f}, 差额={check['difference']:,.2f}")
                else:
                    print(check.get('message', ''))

        # 层级2：利润计算
        level2_checks = balance_check.get('level2_profit_checks', [])
        if level2_checks:
            print("\n【层级2：利润计算验证】")
            for check in level2_checks:
                status = "✓" if check.get('passed') else "✗"
                print(f"  {status} {check.get('name')}: 计算={check['calculated']:,.2f}, 报表={check['reported']:,.2f}, 差额={check['difference']:,.2f}")

        # 层级3：归属验证
        level3_checks = balance_check.get('level3_attribution_checks', [])
        if level3_checks:
            print("\n【层级3：归属验证】")
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
    print("真实PDF测试 - 利润表解析器")
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
