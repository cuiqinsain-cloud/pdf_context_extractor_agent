#!/usr/bin/env python3
"""
测试 LLM 集成功能
使用海天味业 PDF 测试混合列分析器
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.hybrid_column_analyzer import HybridColumnAnalyzer

def test_haitian_with_llm():
    """测试海天味业 PDF（使用 LLM 集成）"""

    print("=" * 80)
    print("测试 LLM 集成功能 - 海天味业")
    print("=" * 80)

    # 测试配置
    pdf_path = 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf'
    page_range = (76, 78)

    print(f"\nPDF文件: {pdf_path}")
    print(f"页码范围: {page_range[0]}-{page_range[1]}")

    # 读取 PDF 和提取表格
    print("\n[1/3] 读取PDF和提取表格...")
    with PDFReader(pdf_path) as pdf_reader:
        table_extractor = TableExtractor()
        pages = pdf_reader.get_pages(page_range)
        tables = table_extractor.extract_tables_from_pages(pages)

        print(f"  ✓ 共提取 {len(tables)} 个表格")

        if not tables:
            print("  ✗ 未提取到表格")
            return

        # 获取第一个表格的表头
        first_table = tables[0]['data']
        header_row = first_table[0]

        print(f"\n[2/3] 分析表头行...")
        print(f"  表头: {header_row}")

        # 使用混合列分析器
        print(f"\n[3/3] 使用混合列分析器...")
        try:
            analyzer = HybridColumnAnalyzer()

            print(f"\n配置信息:")
            print(f"  - LLM启用: {analyzer.enable_llm}")
            print(f"  - 结果对比: {analyzer.enable_comparison}")
            print(f"  - 用户选择: {analyzer.enable_user_choice}")

            # 分析表头
            result = analyzer.analyze_row_structure(header_row, use_cache=False)

            print(f"\n" + "=" * 80)
            print("最终识别结果:")
            print("=" * 80)

            if result:
                for col_type, col_idx in result.items():
                    cell_value = header_row[col_idx] if col_idx < len(header_row) else 'N/A'
                    print(f"  - {col_type.value:20s}: 列{col_idx} = '{cell_value}'")
            else:
                print("  （未识别出任何列）")

            # 显示统计信息
            stats = analyzer.get_statistics()
            print(f"\n" + "=" * 80)
            print("统计信息:")
            print("=" * 80)
            for key, value in stats.items():
                print(f"  - {key}: {value}")

        except FileNotFoundError as e:
            print(f"\n✗ 配置文件错误: {e}")
            print("\n请按照以下步骤配置:")
            print("  1. 复制配置模板: cp config/llm_config.template.json config/llm_config.json")
            print("  2. 设置环境变量: export LLM_API_KEY='your_api_key'")
            print("  3. 重新运行测试")
            return

        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return

    print(f"\n" + "=" * 80)
    print("✓ 测试完成")
    print("=" * 80)


if __name__ == '__main__':
    test_haitian_with_llm()
