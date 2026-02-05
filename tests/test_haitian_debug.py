#!/usr/bin/env python3
"""
调试海天味业数据提取
查看所有提取到的项目
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer
from unittest.mock import patch

def debug_haitian():
    """调试海天味业数据提取"""

    print("=" * 80)
    print("调试 - 海天味业数据提取")
    print("=" * 80)

    # 测试配置
    pdf_path = 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf'
    page_range = (76, 78)

    # 模拟用户输入"2"（选择LLM结果）
    with patch('builtins.input', return_value='2'):
        # 读取 PDF 和提取表格
        with PDFReader(pdf_path) as pdf_reader:
            table_extractor = TableExtractor()
            pages = pdf_reader.get_pages(page_range)
            tables = table_extractor.extract_tables_from_pages(pages)

            # 合并所有表格数据
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])

            # 使用混合列分析器解析
            parser = BalanceSheetParser()
            parser.column_analyzer = HybridColumnAnalyzer()

            result = parser.parse_balance_sheet(merged_data)

            # 显示所有提取到的项目
            print("\n" + "=" * 80)
            print("所有提取到的项目:")
            print("=" * 80)

            print("\n【资产】")
            assets = result['assets']
            if assets:
                for item_name, item_data in assets.items():
                    current = item_data.get('current_period', 'N/A')
                    previous = item_data.get('previous_period', 'N/A')
                    print(f"  {item_name:30s}: 本期={current}, 上期={previous}")
            else:
                print("  （无数据）")

            print("\n【负债】")
            liabilities = result['liabilities']
            if liabilities:
                for item_name, item_data in liabilities.items():
                    current = item_data.get('current_period', 'N/A')
                    previous = item_data.get('previous_period', 'N/A')
                    print(f"  {item_name:30s}: 本期={current}, 上期={previous}")
            else:
                print("  （无数据）")

            print("\n【所有者权益】")
            equity = result['equity']
            if equity:
                for item_name, item_data in equity.items():
                    current = item_data.get('current_period', 'N/A')
                    previous = item_data.get('previous_period', 'N/A')
                    print(f"  {item_name:30s}: 本期={current}, 上期={previous}")
            else:
                print("  （无数据）")

            # 显示原始数据的前20行
            print("\n" + "=" * 80)
            print("原始数据（前20行）:")
            print("=" * 80)
            for i, row in enumerate(merged_data[:20]):
                print(f"  行{i:3d}: {row}")

if __name__ == '__main__':
    debug_haitian()
