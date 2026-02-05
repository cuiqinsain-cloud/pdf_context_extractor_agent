"""
导出真实PDF解析结果到Excel文件
"""
import sys
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
import pandas as pd
from datetime import datetime


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


def parse_company_data(test_case):
    """解析单个公司的数据"""
    print(f"\n处理 {test_case['name']}...")

    try:
        with PDFReader(test_case['file']) as pdf_reader:
            table_extractor = TableExtractor()
            pages = pdf_reader.get_pages(test_case['pages'])
            all_tables = table_extractor.extract_tables_from_pages(pages)

            if not all_tables:
                print(f"  ✗ 未找到表格")
                return None

            print(f"  ✓ 提取 {len(all_tables)} 个表格")

        # 解析
        parser = BalanceSheetParser()
        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        result = parser.parse_balance_sheet(merged_table_data)
        print(f"  ✓ 匹配 {result['parsing_info']['matched_items']} 项")

        return result

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return None


def result_to_dataframe(company_name, result):
    """将解析结果转换为DataFrame"""
    rows = []

    # 流动资产
    for item_name, item_data in result['assets']['current_assets'].items():
        rows.append({
            '公司': company_name,
            '类别': '流动资产',
            '项目': item_name,
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 非流动资产
    for item_name, item_data in result['assets']['non_current_assets'].items():
        rows.append({
            '公司': company_name,
            '类别': '非流动资产',
            '项目': item_name,
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 资产总计
    if result['assets']['assets_total']:
        item_data = result['assets']['assets_total']
        rows.append({
            '公司': company_name,
            '类别': '资产总计',
            '项目': '资产总计',
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 流动负债
    for item_name, item_data in result['liabilities']['current_liabilities'].items():
        rows.append({
            '公司': company_name,
            '类别': '流动负债',
            '项目': item_name,
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 非流动负债
    for item_name, item_data in result['liabilities']['non_current_liabilities'].items():
        rows.append({
            '公司': company_name,
            '类别': '非流动负债',
            '项目': item_name,
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 负债总计
    if result['liabilities']['liabilities_total']:
        item_data = result['liabilities']['liabilities_total']
        rows.append({
            '公司': company_name,
            '类别': '负债总计',
            '项目': '负债总计',
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 所有者权益（普通项目）
    equity_items = result['equity'].get('items', {})
    for item_name, item_data in equity_items.items():
        rows.append({
            '公司': company_name,
            '类别': '所有者权益',
            '项目': item_name,
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 归属于母公司所有者权益合计
    if result['equity'].get('parent_equity_total'):
        item_data = result['equity']['parent_equity_total']
        rows.append({
            '公司': company_name,
            '类别': '所有者权益',
            '项目': '归属于母公司所有者权益合计',
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 所有者权益合计
    if result['equity'].get('equity_total'):
        item_data = result['equity']['equity_total']
        rows.append({
            '公司': company_name,
            '类别': '所有者权益',
            '项目': '所有者权益合计',
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 负债和所有者权益总计
    if result['liabilities_and_equity_total']:
        item_data = result['liabilities_and_equity_total']
        rows.append({
            '公司': company_name,
            '类别': '负债和所有者权益总计',
            '项目': '负债和所有者权益总计',
            '原始名称': item_data.get('original_name', ''),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    return pd.DataFrame(rows)


def create_summary_dataframe(all_results):
    """创建汇总统计表"""
    rows = []

    for company_name, result in all_results.items():
        if result is None:
            continue

        parsing_info = result['parsing_info']

        rows.append({
            '公司': company_name,
            '总行数': parsing_info['total_rows'],
            '匹配项目数': parsing_info['matched_items'],
            '未匹配项目数': len(parsing_info['unmatched_items']),
            '匹配率': f"{parsing_info['matched_items'] / parsing_info['total_rows'] * 100:.1f}%",
            '流动资产项数': len(result['assets']['current_assets']),
            '非流动资产项数': len(result['assets']['non_current_assets']),
            '流动负债项数': len(result['liabilities']['current_liabilities']),
            '非流动负债项数': len(result['liabilities']['non_current_liabilities']),
            '所有者权益项数': len(result['equity'].get('items', {}))
        })

    return pd.DataFrame(rows)


def create_unmatched_dataframe(all_results):
    """创建未匹配项目表"""
    rows = []

    for company_name, result in all_results.items():
        if result is None:
            continue

        for item in result['parsing_info']['unmatched_items']:
            rows.append({
                '公司': company_name,
                '行号': item['row_index'],
                '项目名称': item['item_name'],
                '本期金额': item['values'].get('current_period', ''),
                '上期金额': item['values'].get('previous_period', ''),
                '附注': item['values'].get('note', '')
            })

    return pd.DataFrame(rows)


def main():
    """主函数"""
    print("=" * 80)
    print("导出真实PDF解析结果到Excel")
    print("=" * 80)

    # 解析所有公司数据
    all_results = {}
    for test_case in TEST_CASES:
        result = parse_company_data(test_case)
        all_results[test_case['name']] = result

    # 创建Excel文件
    output_file = f"balance_sheet_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    print(f"\n生成Excel文件: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 1. 汇总统计表
        summary_df = create_summary_dataframe(all_results)
        summary_df.to_excel(writer, sheet_name='汇总统计', index=False)
        print("  ✓ 汇总统计")

        # 2. 每个公司一个sheet
        for company_name, result in all_results.items():
            if result is None:
                continue

            df = result_to_dataframe(company_name, result)
            # Excel sheet名称最多31个字符
            sheet_name = company_name[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  ✓ {company_name}")

        # 3. 未匹配项目表
        unmatched_df = create_unmatched_dataframe(all_results)
        if not unmatched_df.empty:
            unmatched_df.to_excel(writer, sheet_name='未匹配项目', index=False)
            print("  ✓ 未匹配项目")

    print(f"\n✓ Excel文件已生成: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
