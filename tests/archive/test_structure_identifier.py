"""
测试财务报表结构识别器
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_balance_sheet_structure():
    """测试资产负债表结构识别"""
    logger.info("=" * 80)
    logger.info("测试资产负债表结构识别")
    logger.info("=" * 80)

    # 读取PDF
    pdf_path = 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf'

    if not os.path.exists(pdf_path):
        logger.error(f"PDF文件不存在: {pdf_path}")
        return

    with PDFReader(pdf_path) as pdf_reader:
        # 提取资产负债表页面（假设在89-91页）
        pages = pdf_reader.get_pages((89, 91))

        table_extractor = TableExtractor()
        tables = table_extractor.extract_tables_from_pages(pages)

        # 合并所有表格数据
        merged_data = []
        for table_dict in tables:
            merged_data.extend(table_dict['data'])

        logger.info(f"提取到 {len(merged_data)} 行数据")

        # 使用结构识别器
        identifier = StatementStructureIdentifier('balance_sheet')
        result = identifier.identify_structure(merged_data)

        # 打印结果
        print("\n" + "=" * 80)
        print("资产负债表结构识别结果")
        print("=" * 80)
        print(f"是否有效: {result['is_valid']}")
        print(f"置信度: {result['confidence']:.2%}")
        print(f"缺失的关键结构: {result['missing_keys']}")
        print(f"\n表头行: 第{result['header_row']}行")
        print(f"数据开始行: 第{result['start_row']}行")
        print(f"数据结束行: 第{result['end_row']}行")

        print(f"\n关键结构位置:")
        for key_name, row_idx in sorted(result['key_positions'].items(), key=lambda x: x[1]):
            if row_idx < len(merged_data):
                item_name = merged_data[row_idx][0] if merged_data[row_idx] else ""
                print(f"  第{row_idx:3d}行: {key_name:15s} - '{item_name}'")

        # 显示表头内容
        if result['header_row'] is not None and result['header_row'] < len(merged_data):
            print(f"\n表头内容:")
            header_row = merged_data[result['header_row']]
            for i, cell in enumerate(header_row[:5]):  # 只显示前5列
                print(f"  列{i}: '{cell}'")

        # 显示数据范围的前几行和后几行
        if result['is_valid']:
            print(f"\n数据范围预览:")
            print(f"前3行:")
            for i in range(result['start_row'], min(result['start_row'] + 3, len(merged_data))):
                row = merged_data[i]
                item_name = row[0] if row else ""
                print(f"  第{i:3d}行: '{item_name[:50]}'")

            print(f"\n后3行:")
            for i in range(max(result['end_row'] - 2, result['start_row']), result['end_row'] + 1):
                if i < len(merged_data):
                    row = merged_data[i]
                    item_name = row[0] if row else ""
                    print(f"  第{i:3d}行: '{item_name[:50]}'")


def test_income_statement_structure():
    """测试利润表结构识别"""
    logger.info("\n" + "=" * 80)
    logger.info("测试利润表结构识别")
    logger.info("=" * 80)

    # 读取PDF
    pdf_path = 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf'

    if not os.path.exists(pdf_path):
        logger.error(f"PDF文件不存在: {pdf_path}")
        return

    with PDFReader(pdf_path) as pdf_reader:
        # 提取利润表页面（假设在93-95页）
        pages = pdf_reader.get_pages((93, 95))

        table_extractor = TableExtractor()
        tables = table_extractor.extract_tables_from_pages(pages)

        # 合并所有表格数据
        merged_data = []
        for table_dict in tables:
            merged_data.extend(table_dict['data'])

        logger.info(f"提取到 {len(merged_data)} 行数据")

        # 使用结构识别器
        identifier = StatementStructureIdentifier('income_statement')
        result = identifier.identify_structure(merged_data)

        # 打印结果
        print("\n" + "=" * 80)
        print("利润表结构识别结果")
        print("=" * 80)
        print(f"是否有效: {result['is_valid']}")
        print(f"置信度: {result['confidence']:.2%}")
        print(f"缺失的关键结构: {result['missing_keys']}")
        print(f"\n表头行: 第{result['header_row']}行")
        print(f"数据开始行: 第{result['start_row']}行")
        print(f"数据结束行: 第{result['end_row']}行")

        print(f"\n关键结构位置:")
        for key_name, row_idx in sorted(result['key_positions'].items(), key=lambda x: x[1]):
            if row_idx < len(merged_data):
                item_name = merged_data[row_idx][0] if merged_data[row_idx] else ""
                print(f"  第{row_idx:3d}行: {key_name:15s} - '{item_name}'")

        # 显示表头内容
        if result['header_row'] is not None and result['header_row'] < len(merged_data):
            print(f"\n表头内容:")
            header_row = merged_data[result['header_row']]
            for i, cell in enumerate(header_row[:5]):
                print(f"  列{i}: '{cell}'")

        # 显示数据范围的前几行和后几行
        if result['is_valid']:
            print(f"\n数据范围预览:")
            print(f"前3行:")
            for i in range(result['start_row'], min(result['start_row'] + 3, len(merged_data))):
                row = merged_data[i]
                item_name = row[0] if row else ""
                print(f"  第{i:3d}行: '{item_name[:50]}'")

            print(f"\n后3行:")
            for i in range(max(result['end_row'] - 2, result['start_row']), result['end_row'] + 1):
                if i < len(merged_data):
                    row = merged_data[i]
                    item_name = row[0] if row else ""
                    print(f"  第{i:3d}行: '{item_name[:50]}'")


def test_cash_flow_structure():
    """测试现金流量表结构识别"""
    logger.info("\n" + "=" * 80)
    logger.info("测试现金流量表结构识别")
    logger.info("=" * 80)

    # 读取PDF
    pdf_path = 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf'

    if not os.path.exists(pdf_path):
        logger.error(f"PDF文件不存在: {pdf_path}")
        return

    with PDFReader(pdf_path) as pdf_reader:
        # 提取现金流量表页面（假设在96-97页）
        pages = pdf_reader.get_pages((96, 97))

        table_extractor = TableExtractor()
        tables = table_extractor.extract_tables_from_pages(pages)

        # 合并所有表格数据
        merged_data = []
        for table_dict in tables:
            merged_data.extend(table_dict['data'])

        logger.info(f"提取到 {len(merged_data)} 行数据")

        # 使用结构识别器
        identifier = StatementStructureIdentifier('cash_flow')
        result = identifier.identify_structure(merged_data)

        # 打印结果
        print("\n" + "=" * 80)
        print("现金流量表结构识别结果")
        print("=" * 80)
        print(f"是否有效: {result['is_valid']}")
        print(f"置信度: {result['confidence']:.2%}")
        print(f"缺失的关键结构: {result['missing_keys']}")
        print(f"\n表头行: 第{result['header_row']}行")
        print(f"数据开始行: 第{result['start_row']}行")
        print(f"数据结束行: 第{result['end_row']}行")

        print(f"\n关键结构位置:")
        for key_name, row_idx in sorted(result['key_positions'].items(), key=lambda x: x[1]):
            if row_idx < len(merged_data):
                item_name = merged_data[row_idx][0] if merged_data[row_idx] else ""
                print(f"  第{row_idx:3d}行: {key_name:15s} - '{item_name}'")

        # 显示表头内容
        if result['header_row'] is not None and result['header_row'] < len(merged_data):
            print(f"\n表头内容:")
            header_row = merged_data[result['header_row']]
            for i, cell in enumerate(header_row[:5]):
                print(f"  列{i}: '{cell}'")

        # 显示数据范围的前几行和后几行
        if result['is_valid']:
            print(f"\n数据范围预览:")
            print(f"前3行:")
            for i in range(result['start_row'], min(result['start_row'] + 3, len(merged_data))):
                row = merged_data[i]
                item_name = row[0] if row else ""
                print(f"  第{i:3d}行: '{item_name[:50]}'")

            print(f"\n后3行:")
            for i in range(max(result['end_row'] - 2, result['start_row']), result['end_row'] + 1):
                if i < len(merged_data):
                    row = merged_data[i]
                    item_name = row[0] if row else ""
                    print(f"  第{i:3d}行: '{item_name[:50]}'")


if __name__ == '__main__':
    # 测试三张表的结构识别
    test_balance_sheet_structure()
    test_income_statement_structure()
    test_cash_flow_structure()
