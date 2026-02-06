"""
调试财务报表结构识别 - 查看详细的识别过程
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.statement_structure_identifier import StatementStructureIdentifier
import logging

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def debug_structure_identification(company_name, pdf_path, pages, statement_type):
    """
    调试结构识别过程

    Args:
        company_name: 公司名称
        pdf_path: PDF文件路径
        pages: 页码范围
        statement_type: 报表类型
    """
    print("\n" + "=" * 100)
    print(f"公司: {company_name} | 报表类型: {statement_type} | 页面: {pages}")
    print("=" * 100)

    if not os.path.exists(pdf_path):
        print(f"❌ PDF文件不存在: {pdf_path}")
        return

    try:
        with PDFReader(pdf_path) as pdf_reader:
            pages_data = pdf_reader.get_pages(pages)
            table_extractor = TableExtractor()
            tables = table_extractor.extract_tables_from_pages(pages_data)

            # 合并所有表格数据
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])

            print(f"\n提取到 {len(merged_data)} 行数据")

            # 显示前20行数据
            print(f"\n前20行数据预览:")
            print("-" * 100)
            for i in range(min(20, len(merged_data))):
                row = merged_data[i]
                if row and len(row) > 0:
                    # 显示第0列和第1列（如果存在）
                    col0 = row[0] if len(row) > 0 else ""
                    col1 = row[1] if len(row) > 1 else ""
                    col0_str = str(col0).replace('\n', ' ').replace('\r', '').strip()[:60]
                    col1_str = str(col1).replace('\n', ' ').replace('\r', '').strip()[:30]
                    print(f"第{i:3d}行: 列0='{col0_str}' | 列1='{col1_str}'")

            # 使用结构识别器
            identifier = StatementStructureIdentifier(statement_type)
            result = identifier.identify_structure(merged_data)

            # 显示识别结果
            print(f"\n识别结果:")
            print("-" * 100)
            print(f"是否有效: {result['is_valid']}")
            print(f"置信度: {result['confidence']:.2%}")
            print(f"缺失的关键结构: {result['missing_keys']}")

            if result['key_positions']:
                print(f"\n找到的关键结构 ({len(result['key_positions'])}个):")
                for key_name, row_idx in sorted(result['key_positions'].items(), key=lambda x: x[1]):
                    if row_idx < len(merged_data):
                        row = merged_data[row_idx]
                        item_name = row[0] if row else ""
                        item_name = str(item_name).replace('\n', ' ').replace('\r', '').strip()
                        print(f"  第{row_idx:3d}行: {key_name:20s} - '{item_name}'")
            else:
                print(f"\n❌ 未找到任何关键结构")

            if result['is_valid']:
                print(f"\n表头行: 第{result['header_row']}行")
                print(f"数据范围: 第{result['start_row']}行 到 第{result['end_row']}行")

                # 显示表头内容
                if result['header_row'] is not None and result['header_row'] < len(merged_data):
                    print(f"\n表头内容:")
                    header_row = merged_data[result['header_row']]
                    for i, cell in enumerate(header_row[:6]):
                        cell_str = str(cell).replace('\n', ' ').replace('\r', '').strip()
                        print(f"  列{i}: '{cell_str}'")

            # 显示中间部分数据（第40-60行）
            print(f"\n中间部分数据预览 (第40-60行):")
            print("-" * 100)
            for i in range(40, min(60, len(merged_data))):
                row = merged_data[i]
                if row and len(row) > 0:
                    col0 = row[0] if len(row) > 0 else ""
                    col1 = row[1] if len(row) > 1 else ""
                    col0_str = str(col0).replace('\n', ' ').replace('\r', '').strip()[:60]
                    col1_str = str(col1).replace('\n', ' ').replace('\r', '').strip()[:30]
                    print(f"第{i:3d}行: 列0='{col0_str}' | 列1='{col1_str}'")

            # 显示后20行数据
            print(f"\n后20行数据预览:")
            print("-" * 100)
            start_idx = max(0, len(merged_data) - 20)
            for i in range(start_idx, len(merged_data)):
                row = merged_data[i]
                if row and len(row) > 0:
                    col0 = row[0] if len(row) > 0 else ""
                    col1 = row[1] if len(row) > 1 else ""
                    col0_str = str(col0).replace('\n', ' ').replace('\r', '').strip()[:60]
                    col1_str = str(col1).replace('\n', ' ').replace('\r', '').strip()[:30]
                    print(f"第{i:3d}行: 列0='{col0_str}' | 列1='{col1_str}'")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 测试金山办公
    print("\n" + "=" * 100)
    print("测试金山办公")
    print("=" * 100)

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (89, 91),
        'balance_sheet'
    )

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (93, 95),
        'income_statement'
    )

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (96, 97),
        'cash_flow'
    )

    # 测试深信服
    print("\n\n" + "=" * 100)
    print("测试深信服")
    print("=" * 100)

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (89, 91),
        'balance_sheet'
    )

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (93, 95),
        'income_statement'
    )

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (96, 97),
        'cash_flow'
    )
