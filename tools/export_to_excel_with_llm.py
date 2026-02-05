"""
导出真实PDF解析结果到Excel文件（使用LLM混合识别）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer
import pandas as pd
from datetime import datetime
from unittest.mock import patch


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
        # 模拟用户输入"2"（自动选择LLM结果）
        with patch('builtins.input', return_value='2'):
            with PDFReader(test_case['file']) as pdf_reader:
                table_extractor = TableExtractor()
                pages = pdf_reader.get_pages(test_case['pages'])
                all_tables = table_extractor.extract_tables_from_pages(pages)

                # 合并所有表格数据
                merged_data = []
                for table_dict in all_tables:
                    merged_data.extend(table_dict['data'])

                # 使用混合列分析器解析
                parser = BalanceSheetParser()
                parser.column_analyzer = HybridColumnAnalyzer()

                result = parser.parse_balance_sheet(merged_data)

                print(f"  ✓ 解析完成")
                return result

    except Exception as e:
        print(f"  ✗ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_summary_sheet(results):
    """创建汇总统计表"""
    summary_data = []

    for company_name, result in results.items():
        if result is None:
            continue

        # 提取关键数据
        assets = result['assets']
        liabilities = result['liabilities']
        equity = result['equity']

        # 获取资产总计
        assets_total_current = assets.get('assets_total', {}).get('current_period', 'N/A')
        assets_total_previous = assets.get('assets_total', {}).get('previous_period', 'N/A')

        # 获取负债合计
        liabilities_total_current = liabilities.get('liabilities_total', {}).get('current_period', 'N/A')
        liabilities_total_previous = liabilities.get('liabilities_total', {}).get('previous_period', 'N/A')

        # 获取所有者权益合计
        equity_total_current = equity.get('所有者权益合计', {}).get('current_period', 'N/A')
        equity_total_previous = equity.get('所有者权益合计', {}).get('previous_period', 'N/A')

        summary_data.append({
            '公司名称': company_name,
            '资产总计(本期)': assets_total_current,
            '资产总计(上期)': assets_total_previous,
            '负债合计(本期)': liabilities_total_current,
            '负债合计(上期)': liabilities_total_previous,
            '所有者权益合计(本期)': equity_total_current,
            '所有者权益合计(上期)': equity_total_previous,
        })

    return pd.DataFrame(summary_data)


def create_company_sheet(company_name, result):
    """创建单个公司的详细数据表"""
    if result is None:
        return pd.DataFrame()

    rows = []

    # 资产部分
    rows.append({
        '类别': '资产',
        '子类别': '',
        '项目': '',
        '本期金额': '',
        '上期金额': ''
    })

    # 流动资产
    assets = result['assets']
    current_assets = assets.get('current_assets', {})
    if current_assets:
        rows.append({
            '类别': '',
            '子类别': '流动资产',
            '项目': '',
            '本期金额': '',
            '上期金额': ''
        })
        for item_name, item_data in current_assets.items():
            rows.append({
                '类别': '',
                '子类别': '',
                '项目': item_name,
                '本期金额': item_data.get('current_period', ''),
                '上期金额': item_data.get('previous_period', '')
            })

    # 非流动资产
    non_current_assets = assets.get('non_current_assets', {})
    if non_current_assets:
        rows.append({
            '类别': '',
            '子类别': '非流动资产',
            '项目': '',
            '本期金额': '',
            '上期金额': ''
        })
        for item_name, item_data in non_current_assets.items():
            rows.append({
                '类别': '',
                '子类别': '',
                '项目': item_name,
                '本期金额': item_data.get('current_period', ''),
                '上期金额': item_data.get('previous_period', '')
            })

    # 资产总计
    if 'assets_total' in assets:
        item_data = assets['assets_total']
        rows.append({
            '类别': '',
            '子类别': '',
            '项目': '资产总计',
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', '')
        })

    # 负债部分
    rows.append({
        '类别': '负债',
        '子类别': '',
        '项目': '',
        '本期金额': '',
        '上期金额': ''
    })

    # 流动负债
    liabilities = result['liabilities']
    current_liabilities = liabilities.get('current_liabilities', {})
    if current_liabilities:
        rows.append({
            '类别': '',
            '子类别': '流动负债',
            '项目': '',
            '本期金额': '',
            '上期金额': ''
        })
        for item_name, item_data in current_liabilities.items():
            rows.append({
                '类别': '',
                '子类别': '',
                '项目': item_name,
                '本期金额': item_data.get('current_period', ''),
                '上期金额': item_data.get('previous_period', '')
            })

    # 非流动负债
    non_current_liabilities = liabilities.get('non_current_liabilities', {})
    if non_current_liabilities:
        rows.append({
            '类别': '',
            '子类别': '非流动负债',
            '项目': '',
            '本期金额': '',
            '上期金额': ''
        })
        for item_name, item_data in non_current_liabilities.items():
            rows.append({
                '类别': '',
                '子类别': '',
                '项目': item_name,
                '本期金额': item_data.get('current_period', ''),
                '上期金额': item_data.get('previous_period', '')
            })

    # 负债合计
    if 'liabilities_total' in liabilities:
        item_data = liabilities['liabilities_total']
        rows.append({
            '类别': '',
            '子类别': '',
            '项目': '负债合计',
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', '')
        })

    # 所有者权益部分
    rows.append({
        '类别': '所有者权益',
        '子类别': '',
        '项目': '',
        '本期金额': '',
        '上期金额': ''
    })

    equity = result['equity']
    for item_name, item_data in equity.items():
        rows.append({
            '类别': '',
            '子类别': '',
            '项目': item_name,
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', '')
        })

    return pd.DataFrame(rows)


def main():
    """主函数"""
    print("=" * 80)
    print("导出资产负债表数据到Excel（使用LLM混合识别）")
    print("=" * 80)

    # 解析所有公司数据
    results = {}
    for test_case in TEST_CASES:
        result = parse_company_data(test_case)
        results[test_case['name']] = result

    # 生成Excel文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/balance_sheet_results_llm_{timestamp}.xlsx"

    print(f"\n生成Excel文件: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 汇总统计表
        summary_df = create_summary_sheet(results)
        summary_df.to_excel(writer, sheet_name='汇总统计', index=False)

        # 各公司详细数据
        for company_name, result in results.items():
            if result is not None:
                company_df = create_company_sheet(company_name, result)
                # Excel sheet名称不能超过31个字符
                sheet_name = company_name[:31]
                company_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n✓ Excel文件已生成: {output_file}")
    print(f"  文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

    # 显示汇总信息
    print("\n" + "=" * 80)
    print("汇总信息:")
    print("=" * 80)
    print(summary_df.to_string(index=False))

    print("\n" + "=" * 80)
    print("✓ 导出完成")
    print("=" * 80)


if __name__ == '__main__':
    main()
