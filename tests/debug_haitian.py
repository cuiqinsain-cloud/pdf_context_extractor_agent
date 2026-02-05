#!/usr/bin/env python3
"""
调试海天味业数据提取问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.column_analyzer import ColumnAnalyzer, ColumnType

# 测试海天味业
pdf_path = 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf'
page_range = (76, 78)

print("=" * 80)
print("调试海天味业数据提取问题")
print("=" * 80)

with PDFReader(pdf_path) as pdf_reader:
    table_extractor = TableExtractor()
    pages = pdf_reader.get_pages(page_range)
    tables = table_extractor.extract_tables_from_pages(pages)

    print(f"\n提取到 {len(tables)} 个表格\n")

    # 查看第一个表格的前10行
    if tables:
        first_table = tables[0]['data']
        print("=" * 80)
        print("第一个表格的前15行:")
        print("=" * 80)
        for i, row in enumerate(first_table[:15]):
            print(f"第{i}行 (共{len(row)}列): {row}")

        print("\n" + "=" * 80)
        print("使用 ColumnAnalyzer 分析表头:")
        print("=" * 80)

        analyzer = ColumnAnalyzer()

        # 分析前几行
        for i, row in enumerate(first_table[:5]):
            print(f"\n--- 分析第{i}行 ---")
            print(f"原始数据: {row}")
            column_map = analyzer.analyze_row_structure(row)
            print(f"识别结果: {column_map}")
