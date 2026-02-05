"""
测试换行符修复效果
验证包含换行符的项目名称能够正确匹配
"""
import sys
sys.path.insert(0, 'src')

from pdf_reader import PDFReader
from table_extractor import TableExtractor
from parsers.balance_sheet import BalanceSheetParser


def test_newline_fix():
    """测试换行符修复效果"""
    print("\n" + "="*60)
    print("测试：换行符修复效果")
    print("="*60)

    companies = [
        ('福耀玻璃', 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf', (89, 91)),
        ('海尔智家', 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf', (117, 119)),
        ('海天味业', 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf', (76, 78)),
        ('金山办公', 'tests/sample_pdfs/金山办公-2024-年报.pdf', (126, 128))
    ]

    print(f"\n{'公司':<10} {'匹配项目':<10} {'未匹配项目':<12} {'匹配率':<10} {'状态'}")
    print("-" * 60)

    all_passed = True

    for name, pdf_path, pages in companies:
        try:
            with PDFReader(pdf_path) as pdf_reader:
                table_extractor = TableExtractor()
                pages_data = pdf_reader.get_pages(pages)
                tables = table_extractor.extract_tables_from_pages(pages_data)

                parser = BalanceSheetParser()
                merged_data = []
                for table_dict in tables:
                    merged_data.extend(table_dict['data'])

                result = parser.parse_balance_sheet(merged_data)

                matched = result['parsing_info']['matched_items']
                unmatched = len(result['parsing_info']['unmatched_items'])
                total = result['parsing_info']['total_rows']
                rate = matched / total * 100 if total > 0 else 0

                # 检查关键合计项目是否匹配
                has_equity_total = bool(result['equity'].get('归属于母公司所有者权益合计') or
                                       result['equity'].get('所有者权益合计'))
                has_total = bool(result.get('liabilities_and_equity_total'))

                status = "✅ 通过" if (has_equity_total and has_total) else "⚠️ 部分"

                print(f"{name:<10} {matched:<10} {unmatched:<12} {rate:.1f}%{'':<6} {status}")

                if not (has_equity_total and has_total):
                    all_passed = False

        except Exception as e:
            print(f"{name:<10} 错误: {str(e)[:40]}")
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！换行符问题已修复。")
    else:
        print("⚠️ 部分测试未通过，需要进一步检查。")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = test_newline_fix()
    sys.exit(0 if success else 1)
