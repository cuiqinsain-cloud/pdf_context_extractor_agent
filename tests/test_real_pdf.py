"""
真实PDF测试：使用实际的年报PDF测试 ColumnAnalyzer 集成效果
"""
import sys
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
import json


# 测试配置
TEST_CASES = [
    {
        'name': '福耀玻璃',
        'file': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
        'pages': (89, 91)
    },
    {
        'name': '海尔智家',
        'file': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
        'pages': (117, 119)
    },
    {
        'name': '海天味业',
        'file': 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf',
        'pages': (76, 78)
    },
    {
        'name': '金山办公',
        'file': 'tests/sample_pdfs/金山办公-2024-年报.pdf',
        'pages': (126, 128)
    },
]


def test_single_company(test_case):
    """测试单个公司的资产负债表提取"""
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

            # 获取指定页码范围的页面对象
            pages = pdf_reader.get_pages(test_case['pages'])
            print(f"  - 获取页面: {test_case['pages'][0]}-{test_case['pages'][1]}")

            # 提取表格
            all_tables = table_extractor.extract_tables_from_pages(pages)

            if not all_tables:
                print("  ✗ 未找到任何表格")
                return False

            print(f"  ✓ 共提取 {len(all_tables)} 个表格")

        # 3. 解析资产负债表
        print("[3/3] 解析资产负债表...")
        parser = BalanceSheetParser()

        # 合并所有表格数据
        merged_table_data = []
        for table_dict in all_tables:
            # table_dict 包含 'page', 'table_index', 'data', 'raw_text'
            # 我们需要的是 'data' 字段
            merged_table_data.extend(table_dict['data'])

        print(f"  - 合并后共 {len(merged_table_data)} 行数据")

        # 解析
        result = parser.parse_balance_sheet(merged_table_data)

        # 4. 输出结果
        print("\n" + "-" * 80)
        print("解析结果:")
        print("-" * 80)

        # 统计信息
        parsing_info = result['parsing_info']
        print(f"总行数: {parsing_info['total_rows']}")
        print(f"匹配项目数: {parsing_info['matched_items']}")
        print(f"未匹配项目数: {len(parsing_info['unmatched_items'])}")
        print(f"匹配率: {parsing_info['matched_items'] / parsing_info['total_rows'] * 100:.1f}%")

        # 资产项目
        current_assets_count = len(result['assets']['current_assets'])
        non_current_assets_count = len(result['assets']['non_current_assets'])
        print(f"\n资产项目:")
        print(f"  - 流动资产: {current_assets_count} 项")
        print(f"  - 非流动资产: {non_current_assets_count} 项")

        # 负债项目
        current_liabilities_count = len(result['liabilities']['current_liabilities'])
        non_current_liabilities_count = len(result['liabilities']['non_current_liabilities'])
        print(f"\n负债项目:")
        print(f"  - 流动负债: {current_liabilities_count} 项")
        print(f"  - 非流动负债: {non_current_liabilities_count} 项")

        # 权益项目
        equity_count = len(result['equity'])
        print(f"\n所有者权益项目: {equity_count} 项")

        # 关键项目示例
        print(f"\n关键项目示例:")
        if '货币资金' in result['assets']['current_assets']:
            item = result['assets']['current_assets']['货币资金']
            print(f"  货币资金: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        if '应收账款' in result['assets']['current_assets']:
            item = result['assets']['current_assets']['应收账款']
            print(f"  应收账款: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        if '固定资产' in result['assets']['non_current_assets']:
            item = result['assets']['non_current_assets']['固定资产']
            print(f"  固定资产: 本期={item.get('current_period')}, 上期={item.get('previous_period')}")

        # 验证平衡性
        print("\n" + "-" * 80)
        print("数据验证:")
        print("-" * 80)
        validation = parser.validate_balance_sheet(result)

        if validation['balance_check']:
            status = validation['balance_check']['status']
            if status == 'passed':
                print(f"✓ 平衡性检查: 通过")
            else:
                print(f"✗ 平衡性检查: 失败")
                print(f"  差额: {validation['balance_check']['difference']:,.2f}")

        print(f"完整性评分: {validation['completeness_score']:.1%}")

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
    print("真实PDF测试 - ColumnAnalyzer 集成验证")
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
