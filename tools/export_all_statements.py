"""
综合导出工具：为每个公司生成包含三张报表的Excel文件
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
from src.parsers.income_statement import IncomeStatementParser
from src.parsers.cash_flow import CashFlowParser
from src.parsers.statement_labels import get_label
import pandas as pd
from datetime import datetime


# 测试配置
TEST_CASES = [
    {
        'name': '福耀玻璃',
        'file': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
        'balance_sheet': (89, 91),
        'income_statement': (93, 95),
        'cash_flow': (96, 97)
    },
    {
        'name': '海尔智家',
        'file': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
        'balance_sheet': (117, 119),
        'income_statement': (121, 123),
        'cash_flow': (124, 126)
    },
    {
        'name': '海天味业',
        'file': 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf',
        'balance_sheet': (76, 78),
        'income_statement': (81, 83),
        'cash_flow': (85, 87)
    },
    {
        'name': '金山办公',
        'file': 'tests/sample_pdfs/金山办公-2024-年报.pdf',
        'balance_sheet': (126, 128),
        'income_statement': (130, 132),
        'cash_flow': (134, 135)
    },
    {
        'name': '深信服',
        'file': 'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        'balance_sheet': (120, 122),
        'income_statement': (124, 126),
        'cash_flow': (127, 128)
    },
]


def parse_statement(pdf_file, pages, parser_class, statement_name):
    """解析单个报表"""
    try:
        with PDFReader(pdf_file) as pdf_reader:
            table_extractor = TableExtractor()
            page_objects = pdf_reader.get_pages(pages)
            all_tables = table_extractor.extract_tables_from_pages(page_objects)

            if not all_tables:
                print(f"    ✗ {statement_name}: 未找到表格")
                return None

            # 合并表格数据
            merged_data = []
            for table_dict in all_tables:
                merged_data.extend(table_dict['data'])

            # 解析
            parser = parser_class()
            if statement_name == '资产负债表':
                result = parser.parse_balance_sheet(merged_data)
            elif statement_name == '利润表':
                result = parser.parse_income_statement(merged_data)
            elif statement_name == '现金流量表':
                result = parser.parse_cash_flow(merged_data)
            else:
                return None

            matched = result['parsing_info']['matched_items']
            print(f"    ✓ {statement_name}: 匹配 {matched} 项")
            return result

    except Exception as e:
        print(f"    ✗ {statement_name}: 错误 - {e}")
        return None


def balance_sheet_to_dataframe(company_name, result):
    """将资产负债表转换为DataFrame"""
    if not result:
        return pd.DataFrame()

    rows = []

    # 流动资产
    for item_name, item_data in result['assets']['current_assets'].items():
        rows.append({
            '公司': company_name,
            '类别': '流动资产',
            '项目': get_label(item_name, 'balance_sheet'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 非流动资产
    for item_name, item_data in result['assets']['non_current_assets'].items():
        rows.append({
            '公司': company_name,
            '类别': '非流动资产',
            '项目': get_label(item_name, 'balance_sheet'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 流动资产合计
    if 'current_assets_total' in result['assets']:
        rows.append({
            '公司': company_name,
            '类别': '资产合计',
            '项目': '流动资产合计',
            '本期金额': result['assets']['current_assets_total'].get('current_period', ''),
            '上期金额': result['assets']['current_assets_total'].get('previous_period', ''),
            '附注': ''
        })

    # 非流动资产合计
    if 'non_current_assets_total' in result['assets']:
        rows.append({
            '公司': company_name,
            '类别': '资产合计',
            '项目': '非流动资产合计',
            '本期金额': result['assets']['non_current_assets_total'].get('current_period', ''),
            '上期金额': result['assets']['non_current_assets_total'].get('previous_period', ''),
            '附注': ''
        })

    # 资产总计
    if 'assets_total' in result['assets']:
        rows.append({
            '公司': company_name,
            '类别': '资产合计',
            '项目': '资产总计',
            '本期金额': result['assets']['assets_total'].get('current_period', ''),
            '上期金额': result['assets']['assets_total'].get('previous_period', ''),
            '附注': ''
        })

    # 流动负债
    for item_name, item_data in result['liabilities']['current_liabilities'].items():
        rows.append({
            '公司': company_name,
            '类别': '流动负债',
            '项目': get_label(item_name, 'balance_sheet'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 非流动负债
    for item_name, item_data in result['liabilities']['non_current_liabilities'].items():
        rows.append({
            '公司': company_name,
            '类别': '非流动负债',
            '项目': get_label(item_name, 'balance_sheet'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 流动负债合计
    if 'current_liabilities_total' in result['liabilities']:
        rows.append({
            '公司': company_name,
            '类别': '负债合计',
            '项目': '流动负债合计',
            '本期金额': result['liabilities']['current_liabilities_total'].get('current_period', ''),
            '上期金额': result['liabilities']['current_liabilities_total'].get('previous_period', ''),
            '附注': ''
        })

    # 非流动负债合计
    if 'non_current_liabilities_total' in result['liabilities']:
        rows.append({
            '公司': company_name,
            '类别': '负债合计',
            '项目': '非流动负债合计',
            '本期金额': result['liabilities']['non_current_liabilities_total'].get('current_period', ''),
            '上期金额': result['liabilities']['non_current_liabilities_total'].get('previous_period', ''),
            '附注': ''
        })

    # 负债合计
    if 'liabilities_total' in result['liabilities']:
        rows.append({
            '公司': company_name,
            '类别': '负债合计',
            '项目': '负债合计',
            '本期金额': result['liabilities']['liabilities_total'].get('current_period', ''),
            '上期金额': result['liabilities']['liabilities_total'].get('previous_period', ''),
            '附注': ''
        })

    # 所有者权益
    for item_name, item_data in result['equity']['items'].items():
        rows.append({
            '公司': company_name,
            '类别': '所有者权益',
            '项目': get_label(item_name, 'balance_sheet'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 所有者权益合计
    if 'parent_equity_total' in result['equity']:
        rows.append({
            '公司': company_name,
            '类别': '所有者权益合计',
            '项目': '归属于母公司所有者权益合计',
            '本期金额': result['equity']['parent_equity_total'].get('current_period', ''),
            '上期金额': result['equity']['parent_equity_total'].get('previous_period', ''),
            '附注': ''
        })

    if 'equity_total' in result['equity']:
        rows.append({
            '公司': company_name,
            '类别': '所有者权益合计',
            '项目': '所有者权益合计',
            '本期金额': result['equity']['equity_total'].get('current_period', ''),
            '上期金额': result['equity']['equity_total'].get('previous_period', ''),
            '附注': ''
        })

    # 负债和所有者权益总计
    if 'total_liabilities_and_equity' in result:
        rows.append({
            '公司': company_name,
            '类别': '负债和所有者权益总计',
            '项目': '负债和所有者权益总计',
            '本期金额': result['total_liabilities_and_equity'].get('current_period', ''),
            '上期金额': result['total_liabilities_and_equity'].get('previous_period', ''),
            '附注': ''
        })

    return pd.DataFrame(rows)


def income_statement_to_dataframe(company_name, result):
    """将利润表转换为DataFrame"""
    if not result:
        return pd.DataFrame()

    rows = []

    # 营业收入
    for item_name, item_data in result['revenue'].items():
        rows.append({
            '公司': company_name,
            '类别': '营业收入',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 营业成本
    for item_name, item_data in result['costs'].items():
        rows.append({
            '公司': company_name,
            '类别': '营业成本',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 其他损益
    for item_name, item_data in result['other_items'].items():
        rows.append({
            '公司': company_name,
            '类别': '其他损益',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 利润
    for item_name, item_data in result['profit'].items():
        rows.append({
            '公司': company_name,
            '类别': '利润',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 综合收益
    for item_name, item_data in result['comprehensive_income'].items():
        rows.append({
            '公司': company_name,
            '类别': '综合收益',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 每股收益
    for item_name, item_data in result['eps'].items():
        rows.append({
            '公司': company_name,
            '类别': '每股收益',
            '项目': get_label(item_name, 'income_statement'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    return pd.DataFrame(rows)


def cash_flow_to_dataframe(company_name, result):
    """将现金流量表转换为DataFrame"""
    if not result:
        return pd.DataFrame()

    rows = []

    # 经营活动
    for item_name, item_data in result['operating_activities'].items():
        rows.append({
            '公司': company_name,
            '类别': '经营活动',
            '项目': get_label(item_name, 'cash_flow'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 投资活动
    for item_name, item_data in result['investing_activities'].items():
        rows.append({
            '公司': company_name,
            '类别': '投资活动',
            '项目': get_label(item_name, 'cash_flow'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 筹资活动
    for item_name, item_data in result['financing_activities'].items():
        rows.append({
            '公司': company_name,
            '类别': '筹资活动',
            '项目': get_label(item_name, 'cash_flow'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    # 其他项目
    for item_name, item_data in result['other_items'].items():
        rows.append({
            '公司': company_name,
            '类别': '其他项目',
            '项目': get_label(item_name, 'cash_flow'),
            '本期金额': item_data.get('current_period', ''),
            '上期金额': item_data.get('previous_period', ''),
            '附注': item_data.get('note', '')
        })

    return pd.DataFrame(rows)


def export_company_to_excel(test_case):
    """为单个公司导出Excel文件"""
    company_name = test_case['name']
    print(f"\n{'='*80}")
    print(f"处理公司: {company_name}")
    print(f"{'='*80}")

    # 解析三张报表
    balance_sheet_result = parse_statement(
        test_case['file'],
        test_case['balance_sheet'],
        BalanceSheetParser,
        '资产负债表'
    )

    income_statement_result = parse_statement(
        test_case['file'],
        test_case['income_statement'],
        IncomeStatementParser,
        '利润表'
    )

    cash_flow_result = parse_statement(
        test_case['file'],
        test_case['cash_flow'],
        CashFlowParser,
        '现金流量表'
    )

    # 转换为DataFrame
    df_balance = balance_sheet_to_dataframe(company_name, balance_sheet_result)
    df_income = income_statement_to_dataframe(company_name, income_statement_result)
    df_cash = cash_flow_to_dataframe(company_name, cash_flow_result)

    # 导出到Excel
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'{company_name}_三表合一_{timestamp}.xlsx')

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        if not df_balance.empty:
            df_balance.to_excel(writer, sheet_name='资产负债表', index=False)
        if not df_income.empty:
            df_income.to_excel(writer, sheet_name='利润表', index=False)
        if not df_cash.empty:
            df_cash.to_excel(writer, sheet_name='现金流量表', index=False)

    print(f"\n✓ 导出成功: {output_file}")
    return output_file


def main():
    """主函数"""
    print("\n" + "="*80)
    print("综合导出工具 - 三张报表")
    print("="*80)

    output_files = []
    for test_case in TEST_CASES:
        try:
            output_file = export_company_to_excel(test_case)
            output_files.append(output_file)
        except Exception as e:
            print(f"\n✗ {test_case['name']} 导出失败: {e}")

    print("\n" + "="*80)
    print("导出完成")
    print("="*80)
    print(f"\n共导出 {len(output_files)} 个文件:")
    for f in output_files:
        print(f"  - {f}")


if __name__ == '__main__':
    main()
