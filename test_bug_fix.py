#!/usr/bin/env python
"""
测试列映射bug修复效果
验证从5家公司的年报中提取合并资产负债表数据
"""
import os
import sys
from main import FinancialReportExtractor
import re

# 测试用例配置
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
    {
        'name': '深信服',
        'file': 'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        'pages': (120, 122)
    }
]

def is_note_format(value):
    """检查值是否为附注格式（如"七、1"）"""
    if not value:
        return False
    return bool(re.search(r'[一二三四五六七八九十]+、\d+', str(value)))

def is_valid_amount(value):
    """检查值是否为有效的金额格式"""
    if not value:
        return False
    # 移除空格和逗号
    cleaned = str(value).replace(',', '').replace(' ', '').strip()
    # 检查是否为纯数字（可能带小数点和负号）
    return bool(re.match(r'^-?\d+(\.\d+)?$', cleaned))

def analyze_extraction_result(result, company_name):
    """分析提取结果，检查是否存在列映射错误"""
    print(f"\n{'='*60}")
    print(f"公司: {company_name}")
    print(f"{'='*60}")

    if not result['success']:
        print(f"❌ 提取失败: {result.get('error_message', '未知错误')}")
        return False

    balance_sheet = result['balance_sheet_data']

    # 统计信息
    total_items = 0
    items_with_amounts = 0
    items_with_note_as_amount = 0  # 金额字段包含附注格式的项目数
    sample_items = []

    # 检查资产项目
    for category in ['current_assets', 'non_current_assets']:
        for item_name, item_data in balance_sheet['assets'][category].items():
            total_items += 1
            current = item_data.get('current_period', '')
            previous = item_data.get('previous_period', '')
            note = item_data.get('note', '')

            # 检查金额字段是否被误识别为附注
            if is_note_format(current) or is_note_format(previous):
                items_with_note_as_amount += 1
                sample_items.append({
                    'name': item_name,
                    'current': current,
                    'previous': previous,
                    'note': note
                })
            elif is_valid_amount(current) or is_valid_amount(previous):
                items_with_amounts += 1

            # 收集前3个样本用于展示
            if len(sample_items) < 3 and (current or previous):
                sample_items.append({
                    'name': item_name,
                    'current': current,
                    'previous': previous,
                    'note': note
                })

    # 检查负债项目
    for category in ['current_liabilities', 'non_current_liabilities']:
        for item_name, item_data in balance_sheet['liabilities'][category].items():
            total_items += 1
            current = item_data.get('current_period', '')
            previous = item_data.get('previous_period', '')
            note = item_data.get('note', '')

            if is_note_format(current) or is_note_format(previous):
                items_with_note_as_amount += 1
            elif is_valid_amount(current) or is_valid_amount(previous):
                items_with_amounts += 1

    # 输出结果
    print(f"\n📊 提取统计:")
    print(f"  - 总项目数: {total_items}")
    print(f"  - 有效金额项目: {items_with_amounts}")
    print(f"  - 金额字段包含附注格式: {items_with_note_as_amount}")

    # 显示样本数据
    print(f"\n📋 样本数据（前3项）:")
    for i, item in enumerate(sample_items[:3], 1):
        print(f"  {i}. {item['name']}")
        print(f"     本期末: {item['current']}")
        print(f"     上期末: {item['previous']}")
        print(f"     附注: {item['note']}")

    # 验证结果
    validation = result['validation_result']
    print(f"\n✅ 验证结果:")
    print(f"  - 整体验证: {'通过' if validation['is_valid'] else '失败'}")
    if validation.get('balance_check'):
        print(f"  - 平衡性检查: {validation['balance_check'].get('status', '未知')}")
    print(f"  - 完整性评分: {validation.get('completeness_score', 0):.1%}")

    # 判断是否存在bug
    if items_with_note_as_amount > 0:
        print(f"\n⚠️  警告: 发现 {items_with_note_as_amount} 个项目的金额字段包含附注格式！")
        print(f"   这可能表明列映射bug仍然存在。")
        return False
    else:
        print(f"\n✅ 通过: 未发现金额字段包含附注格式的情况")
        return True

def main():
    """运行所有测试用例"""
    print("="*60)
    print("开始测试列映射bug修复效果")
    print("="*60)

    results = []

    for test_case in TEST_CASES:
        try:
            print(f"\n正在测试: {test_case['name']} (页码 {test_case['pages'][0]}-{test_case['pages'][1]})")

            # 创建提取器
            extractor = FinancialReportExtractor(test_case['file'])

            # 执行提取
            result = extractor.extract_balance_sheet(test_case['pages'])

            # 分析结果
            passed = analyze_extraction_result(result, test_case['name'])
            results.append({
                'name': test_case['name'],
                'passed': passed,
                'success': result['success']
            })

        except Exception as e:
            print(f"\n❌ 测试失败: {test_case['name']}")
            print(f"   错误: {str(e)}")
            results.append({
                'name': test_case['name'],
                'passed': False,
                'success': False
            })

    # 输出总结
    print(f"\n\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")

    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)

    for result in results:
        status = "✅ 通过" if result['passed'] else "❌ 失败"
        print(f"{status} - {result['name']}")

    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！列映射bug已成功修复。")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败，需要进一步检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
