#!/usr/bin/env python3
"""
海尔智家数据提取调试脚本
用于分析11列格式的表格结构问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

def main():
    print("=" * 80)
    print("海尔智家数据提取调试")
    print("=" * 80)

    pdf_path = 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf'
    pages = (117, 119)

    print(f"\n[1/4] 读取PDF: {pdf_path}")
    print(f"页码范围: {pages}")

    with PDFReader(pdf_path) as pdf_reader:
        # 提取表格
        print("\n[2/4] 提取表格...")
        table_extractor = TableExtractor()
        page_objs = pdf_reader.get_pages(pages)
        tables = table_extractor.extract_tables_from_pages(page_objs)

        print(f"  ✓ 共提取 {len(tables)} 个表格")

        # 合并表格数据
        print("\n[3/4] 合并表格数据...")
        merged_data = []
        for table_dict in tables:
            merged_data.extend(table_dict['data'])

        print(f"  ✓ 合并后共 {len(merged_data)} 行数据")

        # 分析前10行的结构
        print("\n[4/4] 分析表格结构...")
        print("\n" + "=" * 80)
        print("前10行数据分析:")
        print("=" * 80)

        for i, row in enumerate(merged_data[:10]):
            print(f"\n行 {i}: 列数={len(row)}")
            for j, cell in enumerate(row):
                print(f"  列{j}: '{cell}'")

        # 查找货币资金行
        print("\n" + "=" * 80)
        print("查找关键项目:")
        print("=" * 80)

        key_items = ['货币资金', '应收账款', '固定资产', '资产总计']
        for item_name in key_items:
            print(f"\n查找: {item_name}")
            found = False
            for i, row in enumerate(merged_data):
                if any(item_name in str(cell) for cell in row):
                    print(f"  找到于行 {i}: 列数={len(row)}")
                    for j, cell in enumerate(row):
                        if cell and str(cell).strip():
                            print(f"    列{j}: '{cell}'")
                    found = True
                    break
            if not found:
                print(f"  未找到")

        # 使用解析器解析
        print("\n" + "=" * 80)
        print("使用BalanceSheetParser解析:")
        print("=" * 80)

        parser = BalanceSheetParser()
        result = parser.parse_balance_sheet(merged_data)

        # 显示关键项目的提取结果
        print("\n关键项目提取结果:")
        for item_name in key_items:
            found = False
            if item_name in result['assets']['current_assets']:
                item = result['assets']['current_assets'][item_name]
                print(f"  {item_name}: 本期={item['current_period']}, 上期={item['previous_period']}")
                found = True
            elif item_name in result['assets']['non_current_assets']:
                item = result['assets']['non_current_assets'][item_name]
                print(f"  {item_name}: 本期={item['current_period']}, 上期={item['previous_period']}")
                found = True

            # 检查汇总数据
            if not found:
                for category in ['assets', 'liabilities', 'equity']:
                    if category in result:
                        for subcategory in result[category].values():
                            if isinstance(subcategory, dict) and item_name in subcategory:
                                item = subcategory[item_name]
                                print(f"  {item_name}: 本期={item['current_period']}, 上期={item['previous_period']}")
                                found = True
                                break
                    if found:
                        break

            if not found:
                print(f"  {item_name}: 未找到")

if __name__ == '__main__':
    main()
