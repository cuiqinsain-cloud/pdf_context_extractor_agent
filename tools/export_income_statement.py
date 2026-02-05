"""
利润表数据导出到Excel工具
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.income_statement import IncomeStatementParser
import pandas as pd
from datetime import datetime


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


def parse_company_income_statement(test_case):
    """解析单个公司的利润表"""
    print(f"正在处理: {test_case['name']}...")

    try:
        with PDFReader(test_case['file']) as pdf_reader:
            table_extractor = TableExtractor()
            pages = pdf_reader.get_pages(test_case['pages'])
            all_tables = table_extractor.extract_tables_from_pages(pages)

            if not all_tables:
                print(f"  ✗ {test_case['name']}: 未找到表格")
                return None

            # 合并表格数据
            merged_table_data = []
            for table_dict in all_tables:
                merged_table_data.extend(table_dict['data'])

            # 解析利润表
            parser = IncomeStatementParser()
            result = parser.parse_income_statement(merged_table_data)

            # 验证
            validation = parser.validate_income_statement(result)

            print(f"  ✓ {test_case['name']}: 匹配{result['parsing_info']['matched_items']}项, "
                  f"验证{'通过' if validation['is_valid'] else '失败'}")

            return {
                'company': test_case['name'],
                'data': result,
                'validation': validation
            }

    except Exception as e:
        print(f"  ✗ {test_case['name']}: 解析失败 - {e}")
        return None


def convert_to_dataframe(all_results):
    """将解析结果转换为DataFrame"""
    rows = []

    # 定义项目顺序和中文名称
    item_mapping = {
        # 营业收入
        'revenue.operating_total_revenue': '一、营业总收入',
        'revenue.operating_revenue': '  营业收入',
        # 营业成本
        'costs.operating_total_cost': '二、营业总成本',
        'costs.operating_cost': '  营业成本',
        'costs.taxes_and_surcharges': '  税金及附加',
        'costs.selling_expenses': '  销售费用',
        'costs.administrative_expenses': '  管理费用',
        'costs.rd_expenses': '  研发费用',
        'costs.financial_expenses': '  财务费用',
        # 其他损益
        'other_items.other_income': '加：其他收益',
        'other_items.investment_income': '  投资收益',
        'other_items.fair_value_change': '  公允价值变动收益',
        'other_items.credit_impairment': '  信用减值损失',
        'other_items.asset_impairment': '  资产减值损失',
        'other_items.asset_disposal': '  资产处置收益',
        # 利润
        'profit.operating_profit': '三、营业利润',
        'profit.non_operating_income': '加：营业外收入',
        'profit.non_operating_expenses': '减：营业外支出',
        'profit.total_profit': '四、利润总额',
        'profit.income_tax': '减：所得税费用',
        'profit.net_profit': '五、净利润',
        'profit.continuing_operations_profit': '  持续经营净利润',
        'profit.discontinued_operations_profit': '  终止经营净利润',
        'profit.parent_net_profit': '  归属于母公司所有者的净利润',
        'profit.minority_profit': '  少数股东损益',
        # 综合收益
        'comprehensive_income.other_comprehensive_income': '六、其他综合收益的税后净额',
        'comprehensive_income.total_comprehensive_income': '七、综合收益总额',
        # 每股收益
        'eps.basic_eps': '八、每股收益（基本）',
        'eps.diluted_eps': '  每股收益（稀释）',
    }

    for item_path, item_name_cn in item_mapping.items():
        row = {'项目': item_name_cn}

        for result in all_results:
            if result is None:
                continue

            company = result['company']
            data = result['data']

            # 解析路径
            parts = item_path.split('.')
            section = parts[0]
            item_key = parts[1] if len(parts) > 1 else None

            # 获取数据
            section_data = data.get(section, {})
            if item_key and item_key in section_data:
                item_data = section_data[item_key]
                current = item_data.get('current_period', '-')
                previous = item_data.get('previous_period', '-')

                row[f'{company}_本期'] = current
                row[f'{company}_上期'] = previous
            else:
                row[f'{company}_本期'] = '-'
                row[f'{company}_上期'] = '-'

        rows.append(row)

    return pd.DataFrame(rows)


def create_validation_dataframe(all_results):
    """创建验证结果DataFrame"""
    rows = []

    for result in all_results:
        if result is None:
            continue

        company = result['company']
        validation = result['validation']

        row = {
            '公司': company,
            '总体验证': '通过' if validation['is_valid'] else '失败',
            '完整性评分': f"{validation['completeness_score']:.1%}",
            '错误数': len(validation['errors']),
            '警告数': len(validation['warnings'])
        }

        # 添加层级验证结果
        balance_check = validation.get('balance_check', {})

        # 层级1
        level1_checks = balance_check.get('level1_subtotal_checks', [])
        level1_passed = sum(1 for c in level1_checks if c.get('passed', False))
        row['层级1验证'] = f"{level1_passed}/{len(level1_checks)}"

        # 层级2
        level2_checks = balance_check.get('level2_profit_checks', [])
        level2_passed = sum(1 for c in level2_checks if c.get('passed', False))
        row['层级2验证'] = f"{level2_passed}/{len(level2_checks)}"

        # 层级3
        level3_checks = balance_check.get('level3_attribution_checks', [])
        level3_passed = sum(1 for c in level3_checks if c.get('passed', False))
        row['层级3验证'] = f"{level3_passed}/{len(level3_checks)}"

        rows.append(row)

    return pd.DataFrame(rows)


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("利润表数据导出工具")
    print("=" * 80)

    # 解析所有公司
    all_results = []
    for test_case in TEST_CASES:
        result = parse_company_income_statement(test_case)
        all_results.append(result)

    # 转换为DataFrame
    print("\n正在生成Excel文件...")
    df_data = convert_to_dataframe(all_results)
    df_validation = create_validation_dataframe(all_results)

    # 导出到Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'output/income_statement_export_{timestamp}.xlsx'

    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_data.to_excel(writer, sheet_name='利润表数据', index=False)
        df_validation.to_excel(writer, sheet_name='验证结果', index=False)

    print(f"\n✓ 导出成功: {output_file}")
    print(f"  - 利润表数据: {len(df_data)} 行")
    print(f"  - 验证结果: {len(df_validation)} 行")
    print("=" * 80)


if __name__ == '__main__':
    main()
