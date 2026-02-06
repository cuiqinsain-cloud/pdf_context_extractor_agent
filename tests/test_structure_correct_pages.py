"""
调试财务报表结构识别 - 金山办公和深信服（正确页码）
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


def debug_structure_identification(company_name, pdf_path, pages, statement_type, statement_name):
    """
    调试结构识别过程

    Args:
        company_name: 公司名称
        pdf_path: PDF文件路径
        pages: 页码范围
        statement_type: 报表类型
        statement_name: 报表名称
    """
    print("\n" + "=" * 100)
    print(f"【{statement_name}】{company_name} | 页面: {pages}")
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

            print(f"提取到 {len(merged_data)} 行数据")

            # 使用结构识别器
            identifier = StatementStructureIdentifier(statement_type)
            result = identifier.identify_structure(merged_data)

            # 显示识别结果
            print(f"\n✨ 识别结果:")
            print(f"  是否有效: {'✅ 成功' if result['is_valid'] else '❌ 失败'}")
            print(f"  置信度: {result['confidence']:.0%}")
            if result['missing_keys']:
                print(f"  缺失: {result['missing_keys']}")

            if result['key_positions']:
                print(f"\n📍 找到的关键结构 ({len(result['key_positions'])}个):")
                for key_name, row_idx in sorted(result['key_positions'].items(), key=lambda x: x[1]):
                    if row_idx < len(merged_data):
                        row = merged_data[row_idx]
                        item_name = row[0] if row else ""
                        item_name = str(item_name).replace('\n', ' ').replace('\r', '').strip()[:50]
                        print(f"  第{row_idx:3d}行: {key_name:20s} - '{item_name}'")

            if result['is_valid']:
                print(f"\n📋 数据范围:")
                print(f"  表头行: 第{result['header_row']}行")
                print(f"  数据范围: 第{result['start_row']}行 到 第{result['end_row']}行")

                # 显示表头内容
                if result['header_row'] is not None and result['header_row'] < len(merged_data):
                    print(f"\n  表头内容:")
                    header_row = merged_data[result['header_row']]
                    for i, cell in enumerate(header_row[:5]):
                        cell_str = str(cell).replace('\n', ' ').replace('\r', '').strip()
                        print(f"    列{i}: '{cell_str}'")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("财务报表结构识别测试 - 金山办公和深信服")
    print("=" * 100)

    # 测试金山办公
    print("\n\n" + "🏢 " * 20)
    print("金山办公")
    print("🏢 " * 20)

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (126, 128),  # 资产负债表在第126页
        'balance_sheet',
        '资产负债表'
    )

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (130, 132),  # 利润表在第130页
        'income_statement',
        '利润表'
    )

    debug_structure_identification(
        '金山办公',
        'tests/sample_pdfs/金山办公-2024-年报.pdf',
        (134, 136),  # 现金流量表在第134页
        'cash_flow',
        '现金流量表'
    )

    # 测试深信服
    print("\n\n" + "🏢 " * 20)
    print("深信服")
    print("🏢 " * 20)

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (120, 122),  # 资产负债表在第120页
        'balance_sheet',
        '资产负债表'
    )

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (124, 126),  # 利润表在第124页
        'income_statement',
        '利润表'
    )

    debug_structure_identification(
        '深信服',
        'tests/sample_pdfs/深信服：2024年年度报告.PDF',
        (127, 129),  # 现金流量表在第127页
        'cash_flow',
        '现金流量表'
    )

    print("\n" + "=" * 100)
    print("测试完成")
    print("=" * 100)
