"""
测试三层级平衡性验证功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser


def test_balance_validation():
    """测试三层级平衡性验证"""
    print("\n" + "=" * 80)
    print("三层级平衡性验证测试")
    print("=" * 80)

    test_case = {
        'name': '海尔智家',
        'file': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
        'pages': (117, 119)
    }

    print(f"\n测试公司: {test_case['name']}")
    print(f"PDF文件: {test_case['file']}")
    print(f"页码范围: {test_case['pages']}")

    # 读取和解析
    with PDFReader(test_case['file']) as pdf_reader:
        table_extractor = TableExtractor()
        pages = pdf_reader.get_pages(test_case['pages'])
        all_tables = table_extractor.extract_tables_from_pages(pages)

        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        parser = BalanceSheetParser()
        result = parser.parse_balance_sheet(merged_table_data)

        # 执行验证
        validation = parser.validate_balance_sheet(result)

        # 显示详细结果
        print("\n" + "=" * 80)
        print("验证结果详情")
        print("=" * 80)

        balance_check = validation['balance_check']

        # 层级1
        print("\n【层级1：子项目合计验证】")
        for check in balance_check['level1_subtotal_checks']:
            status = "✓" if check['passed'] else "✗"
            print(f"\n{status} {check['name']}")
            if check.get('calculated') is not None:
                print(f"   计算值: {check['calculated']:,.2f}")
                print(f"   报表值: {check['reported']:,.2f}")
                print(f"   差额: {check['difference']:,.2f}")
                print(f"   项目数: {check['item_count']}")
                if check.get('deduction_items'):
                    print(f"   减项:")
                    for item in check['deduction_items']:
                        print(f"     - {item['name']}: {item['value']:,.2f}")

        # 层级2
        print("\n【层级2：大类合计验证】")
        for check in balance_check['level2_category_checks']:
            status = "✓" if check['passed'] else "✗"
            print(f"\n{status} {check['name']}")
            print(f"   公式: {check['formula']}")
            print(f"   计算值: {check['calculated']:,.2f}")
            print(f"   报表值: {check['reported']:,.2f}")
            print(f"   差额: {check['difference']:,.2f}")

        # 层级3
        print("\n【层级3：总平衡验证】")
        level3 = balance_check['level3_total_check']
        if level3:
            status = "✓" if level3['passed'] else "✗"
            print(f"\n{status} {level3['formula']}")
            print(f"   资产总计: {level3['assets_total']:,.2f}")
            print(f"   负债和所有者权益总计: {level3['liabilities_and_equity_total']:,.2f}")
            print(f"   差额: {level3['difference']:,.2f}")

        # 总结
        print("\n" + "=" * 80)
        print(f"总体验证结果: {'✓ 通过' if validation['is_valid'] else '✗ 失败'}")
        print(f"错误数: {len(validation['errors'])}")
        print(f"警告数: {len(validation['warnings'])}")
        print("=" * 80)

        if validation['errors']:
            print("\n错误:")
            for error in validation['errors']:
                print(f"  - {error}")

        if validation['warnings']:
            print("\n警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")


if __name__ == '__main__':
    test_balance_validation()
