#!/usr/bin/env python3
"""
详细调试海天味业数据提取
查看匹配过程
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer
from unittest.mock import patch

def debug_matching():
    """调试匹配过程"""

    print("=" * 80)
    print("详细调试 - 海天味业数据提取")
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

            # 创建解析器
            parser = BalanceSheetParser()
            parser.column_analyzer = HybridColumnAnalyzer()

            # 手动测试几个关键行
            print("\n" + "=" * 80)
            print("测试关键行的匹配:")
            print("=" * 80)

            # 先识别表头
            header_info = parser._identify_header_structure(merged_data)
            print(f"\n表头信息: {header_info}")

            # 测试货币资金行（第2行）
            test_rows = [
                (2, merged_data[2]),  # 货币资金
                (5, merged_data[5]),  # 交易性金融资产
                (8, merged_data[8]),  # 应收账款
                (18, merged_data[18]),  # 存货
            ]

            for row_idx, row in test_rows:
                print(f"\n{'='*60}")
                print(f"行{row_idx}: {row}")

                # 获取项目名称
                item_name = row[0].strip() if row[0] else ""
                print(f"项目名称: '{item_name}'")

                # 提取数值
                values = parser._extract_values_from_row(row, header_info)
                print(f"提取的数值: {values}")

                # 测试匹配
                asset_patterns = parser.asset_patterns['current_assets']
                matched = False
                for standard_name, pattern_list in asset_patterns.items():
                    for pattern in pattern_list:
                        if re.search(pattern, item_name):
                            print(f"✓ 匹配成功: {standard_name} (模式: {pattern})")
                            matched = True
                            break
                    if matched:
                        break

                if not matched:
                    print(f"✗ 未匹配")

            # 运行完整解析
            print("\n" + "=" * 80)
            print("运行完整解析:")
            print("=" * 80)
            result = parser.parse_balance_sheet(merged_data)

            # 显示解析信息
            parsing_info = result.get('parsing_info', {})
            print(f"\n匹配项目数: {parsing_info.get('matched_items', 0)}")
            print(f"未匹配项目数: {len(parsing_info.get('unmatched_items', []))}")

            # 显示前10个未匹配项目
            unmatched = parsing_info.get('unmatched_items', [])
            if unmatched:
                print(f"\n前10个未匹配项目:")
                for item in unmatched[:10]:
                    print(f"  行{item['row_index']:3d}: {item['item_name']:30s} - {item['values']}")

if __name__ == '__main__':
    debug_matching()
