#!/usr/bin/env python3
"""
自动化测试海天味业数据提取
自动选择LLM结果，无需人工干预
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer
from unittest.mock import patch

def test_haitian_auto():
    """自动化测试海天味业数据提取"""

    print("=" * 80)
    print("自动化测试 - 海天味业数据提取（自动选择LLM结果）")
    print("=" * 80)

    # 测试配置
    pdf_path = 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf'
    page_range = (76, 78)

    print(f"\nPDF文件: {pdf_path}")
    print(f"页码范围: {page_range[0]}-{page_range[1]}")

    # 模拟用户输入"2"（选择LLM结果）
    with patch('builtins.input', return_value='2'):
        # 读取 PDF 和提取表格
        print("\n[1/4] 读取PDF和提取表格...")
        with PDFReader(pdf_path) as pdf_reader:
            table_extractor = TableExtractor()
            pages = pdf_reader.get_pages(page_range)
            tables = table_extractor.extract_tables_from_pages(pages)

            print(f"  ✓ 共提取 {len(tables)} 个表格")

            # 合并所有表格数据
            print("\n[2/4] 合并表格数据...")
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])
            print(f"  ✓ 共 {len(merged_data)} 行数据")

            # 使用混合列分析器解析
            print("\n[3/4] 使用混合列分析器解析资产负债表...")
            parser = BalanceSheetParser()
            # 替换为混合列分析器
            parser.column_analyzer = HybridColumnAnalyzer()

            result = parser.parse_balance_sheet(merged_data)

            # 显示结果
            print("\n[4/4] 数据提取结果:")
            print("=" * 80)

            # 资产
            print("\n【流动资产】")
            assets = result['assets']
            current_assets = assets.get('current_assets', {})
            key_assets = ['货币资金', '应收账款', '存货', '流动资产合计']
            for item_name in key_assets:
                if item_name in current_assets:
                    item = current_assets[item_name]
                    current = item.get('current_period', 'N/A')
                    previous = item.get('previous_period', 'N/A')
                    print(f"  {item_name:20s}: 本期={current}, 上期={previous}")

            print("\n【非流动资产】")
            non_current_assets_dict = assets.get('non_current_assets', {})
            non_current_items = ['固定资产', '无形资产', '非流动资产合计']
            for item_name in non_current_items:
                if item_name in non_current_assets_dict:
                    item = non_current_assets_dict[item_name]
                    current = item.get('current_period', 'N/A')
                    previous = item.get('previous_period', 'N/A')
                    print(f"  {item_name:20s}: 本期={current}, 上期={previous}")

            # 资产总计
            if 'assets_total' in assets:
                item = assets['assets_total']
                current = item.get('current_period', 'N/A')
                previous = item.get('previous_period', 'N/A')
                print(f"  {'资产总计':20s}: 本期={current}, 上期={previous}")

            # 负债
            print("\n【流动负债】")
            liabilities = result['liabilities']
            current_liabilities = liabilities.get('current_liabilities', {})
            key_liabilities = ['短期借款', '应付账款', '流动负债合计']
            for item_name in key_liabilities:
                if item_name in current_liabilities:
                    item = current_liabilities[item_name]
                    current = item.get('current_period', 'N/A')
                    previous = item.get('previous_period', 'N/A')
                    print(f"  {item_name:20s}: 本期={current}, 上期={previous}")

            print("\n【非流动负债】")
            non_current_liabilities_dict = liabilities.get('non_current_liabilities', {})
            non_current_liab_items = ['长期借款', '非流动负债合计']
            for item_name in non_current_liab_items:
                if item_name in non_current_liabilities_dict:
                    item = non_current_liabilities_dict[item_name]
                    current = item.get('current_period', 'N/A')
                    previous = item.get('previous_period', 'N/A')
                    print(f"  {item_name:20s}: 本期={current}, 上期={previous}")

            # 负债合计
            if 'liabilities_total' in liabilities:
                item = liabilities['liabilities_total']
                current = item.get('current_period', 'N/A')
                previous = item.get('previous_period', 'N/A')
                print(f"  {'负债合计':20s}: 本期={current}, 上期={previous}")

            # 所有者权益
            print("\n【所有者权益】")
            equity = result['equity']
            key_equity = ['股本', '资本公积', '盈余公积', '未分配利润', '所有者权益合计']
            for item_name in key_equity:
                if item_name in equity:
                    item = equity[item_name]
                    current = item.get('current_period', 'N/A')
                    previous = item.get('previous_period', 'N/A')
                    print(f"  {item_name:20s}: 本期={current}, 上期={previous}")

            # 统计信息
            print("\n" + "=" * 80)
            print("统计信息:")
            print("=" * 80)
            parsing_info = result.get('parsing_info', {})
            print(f"  总行数: {parsing_info.get('total_rows', 'N/A')}")
            print(f"  已匹配: {parsing_info.get('matched_rows', 'N/A')}")
            print(f"  未匹配: {parsing_info.get('unmatched_rows', 'N/A')}")

            # 验证
            print("\n" + "=" * 80)
            print("数据验证:")
            print("=" * 80)

            # 检查关键数据是否提取成功
            success = True
            current_assets = assets.get('current_assets', {})
            if '货币资金' in current_assets:
                current = current_assets['货币资金'].get('current_period')
                if current and current != 'N/A':
                    print(f"  ✓ 货币资金提取成功: {current}")
                else:
                    print(f"  ✗ 货币资金提取失败: {current}")
                    success = False
            else:
                print(f"  ✗ 未找到货币资金项目")
                success = False

            if 'assets_total' in assets:
                current = assets['assets_total'].get('current_period')
                if current and current != 'N/A':
                    print(f"  ✓ 资产总计提取成功: {current}")
                else:
                    print(f"  ✗ 资产总计提取失败: {current}")
                    success = False
            else:
                print(f"  ✗ 未找到资产总计项目")
                success = False

            # 平衡性检查
            parsing_info = result.get('parsing_info', {})
            balance_check = parsing_info.get('balance_check', False)
            if balance_check:
                print(f"  ✓ 平衡性检查通过")
            else:
                print(f"  ⚠️  平衡性检查未通过（可能是数据不完整）")

            print("\n" + "=" * 80)
            if success:
                print("✓ 测试成功！海天味业数据提取正常")
            else:
                print("✗ 测试失败！部分数据提取失败")
            print("=" * 80)

if __name__ == '__main__':
    test_haitian_auto()
