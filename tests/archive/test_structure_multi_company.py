"""
测试多个公司的财务报表结构识别
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
    level=logging.WARNING,  # 只显示警告和错误
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_company_statements(company_name, pdf_path, balance_pages, income_pages, cash_flow_pages):
    """测试一个公司的三张报表"""
    print("\n" + "=" * 100)
    print(f"测试公司: {company_name}")
    print("=" * 100)

    if not os.path.exists(pdf_path):
        print(f"❌ PDF文件不存在: {pdf_path}")
        return

    # 测试资产负债表
    print(f"\n【资产负债表】页面: {balance_pages}")
    try:
        with PDFReader(pdf_path) as pdf_reader:
            pages = pdf_reader.get_pages(balance_pages)
            table_extractor = TableExtractor()
            tables = table_extractor.extract_tables_from_pages(pages)
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])

            identifier = StatementStructureIdentifier('balance_sheet')
            result = identifier.identify_structure(merged_data)

            if result['is_valid']:
                print(f"✅ 识别成功 | 置信度: {result['confidence']:.0%} | 表头: 第{result['header_row']}行 | 范围: 第{result['start_row']}-{result['end_row']}行")
                print(f"   关键结构: {len(result['key_positions'])}个 | 缺失: {result['missing_keys']}")
            else:
                print(f"❌ 识别失败 | 置信度: {result['confidence']:.0%} | 缺失: {result['missing_keys']}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

    # 测试利润表
    print(f"\n【利润表】页面: {income_pages}")
    try:
        with PDFReader(pdf_path) as pdf_reader:
            pages = pdf_reader.get_pages(income_pages)
            table_extractor = TableExtractor()
            tables = table_extractor.extract_tables_from_pages(pages)
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])

            identifier = StatementStructureIdentifier('income_statement')
            result = identifier.identify_structure(merged_data)

            if result['is_valid']:
                print(f"✅ 识别成功 | 置信度: {result['confidence']:.0%} | 表头: 第{result['header_row']}行 | 范围: 第{result['start_row']}-{result['end_row']}行")
                print(f"   关键结构: {len(result['key_positions'])}个 | 缺失: {result['missing_keys']}")
            else:
                print(f"❌ 识别失败 | 置信度: {result['confidence']:.0%} | 缺失: {result['missing_keys']}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

    # 测试现金流量表
    print(f"\n【现金流量表】页面: {cash_flow_pages}")
    try:
        with PDFReader(pdf_path) as pdf_reader:
            pages = pdf_reader.get_pages(cash_flow_pages)
            table_extractor = TableExtractor()
            tables = table_extractor.extract_tables_from_pages(pages)
            merged_data = []
            for table_dict in tables:
                merged_data.extend(table_dict['data'])

            identifier = StatementStructureIdentifier('cash_flow')
            result = identifier.identify_structure(merged_data)

            if result['is_valid']:
                print(f"✅ 识别成功 | 置信度: {result['confidence']:.0%} | 表头: 第{result['header_row']}行 | 范围: 第{result['start_row']}-{result['end_row']}行")
                print(f"   关键结构: {len(result['key_positions'])}个 | 缺失: {result['missing_keys']}")
            else:
                print(f"❌ 识别失败 | 置信度: {result['confidence']:.0%} | 缺失: {result['missing_keys']}")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")


if __name__ == '__main__':
    # 测试所有公司
    companies = [
        {
            'name': '福耀玻璃',
            'pdf': 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf',
            'balance_pages': (89, 91),
            'income_pages': (93, 95),
            'cash_flow_pages': (96, 97)
        },
        {
            'name': '海尔智家',
            'pdf': 'tests/sample_pdfs/海尔智家：海尔智家股份有限公司2024年年度报告.pdf',
            'balance_pages': (89, 91),
            'income_pages': (93, 95),
            'cash_flow_pages': (96, 97)
        },
        {
            'name': '海天味业',
            'pdf': 'tests/sample_pdfs/海天味业：海天味业2024年年度报告.pdf',
            'balance_pages': (89, 91),
            'income_pages': (93, 95),
            'cash_flow_pages': (96, 97)
        },
        {
            'name': '金山办公',
            'pdf': 'tests/sample_pdfs/金山办公-2024-年报.pdf',
            'balance_pages': (89, 91),
            'income_pages': (93, 95),
            'cash_flow_pages': (96, 97)
        },
        {
            'name': '深信服',
            'pdf': 'tests/sample_pdfs/深信服：2024年年度报告.PDF',
            'balance_pages': (89, 91),
            'income_pages': (93, 95),
            'cash_flow_pages': (96, 97)
        }
    ]

    print("\n" + "=" * 100)
    print("财务报表结构识别测试 - 多公司测试")
    print("=" * 100)

    for company in companies:
        test_company_statements(
            company['name'],
            company['pdf'],
            company['balance_pages'],
            company['income_pages'],
            company['cash_flow_pages']
        )

    print("\n" + "=" * 100)
    print("测试完成")
    print("=" * 100)
