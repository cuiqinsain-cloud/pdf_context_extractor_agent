"""
调试金山办公现金流量表提取问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.cash_flow import CashFlowParser


def debug_jinshan():
    """调试金山办公数据提取"""
    print("\n" + "=" * 80)
    print("调试金山办公现金流量表")
    print("=" * 80)

    # 读取PDF
    with PDFReader('tests/sample_pdfs/金山办公-2024-年报.pdf') as pdf_reader:
        table_extractor = TableExtractor()
        pages = pdf_reader.get_pages((134, 135))
        all_tables = table_extractor.extract_tables_from_pages(pages)

        print(f"\n提取到 {len(all_tables)} 个表格")

        # 合并所有表格数据
        merged_table_data = []
        for table_dict in all_tables:
            merged_table_data.extend(table_dict['data'])

        print(f"合并后共 {len(merged_table_data)} 行数据\n")

        # 显示最后30行数据（可能包含现金净增加额和期末余额）
        print("=" * 80)
        print("最后30行数据:")
        print("=" * 80)
        for idx, row in enumerate(merged_table_data[-30:]):
            actual_idx = len(merged_table_data) - 30 + idx
            print(f"行{actual_idx}: 列数={len(row)}")
            for col_idx, cell in enumerate(row):
                if cell and cell.strip():
                    print(f"  列{col_idx}: {cell[:80]}")
            print()

        # 尝试解析
        print("=" * 80)
        print("解析结果:")
        print("=" * 80)
        parser = CashFlowParser()
        result = parser.parse_cash_flow(merged_table_data)

        print(f"匹配项目数: {result['parsing_info']['matched_items']}")
        print(f"未匹配项目数: {len(result['parsing_info']['unmatched_items'])}")

        # 检查关键项目
        print("\n关键项目:")
        print(f"  现金净增加额: {result['other_items'].get('net_increase_cash', {})}")
        print(f"  期末余额: {result['other_items'].get('ending_cash_balance', {})}")

        # 显示未匹配的最后10项
        print("\n未匹配项目（最后10个）:")
        for item in result['parsing_info']['unmatched_items'][-10:]:
            print(f"  行{item['row_index']}: {item['item_name'][:80]}")


if __name__ == '__main__':
    debug_jinshan()
