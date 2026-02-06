"""
简化测试：验证内容提取功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader

# 测试内容提取辅助类
def test_content_extraction():
    """测试内容提取"""
    pdf_path = os.path.join(
        os.path.dirname(__file__),
        'sample_pdfs',
        '福耀玻璃：福耀玻璃2024年年度报告.pdf'
    )

    print("测试内容提取功能")
    print("="*80)

    with PDFReader(pdf_path) as pdf_reader:
        # 只读取第125页
        pages = pdf_reader.get_pages((125, 125))
        page = pages[0]

        # 提取文本
        text = page.extract_text()
        print(f"\n页面文本长度: {len(text)} 字符")
        print(f"前500字符:\n{text[:500]}")

        # 提取表格
        tables = page.extract_tables()
        print(f"\n\n表格数量: {len(tables) if tables else 0}")

        if tables:
            for i, table in enumerate(tables):
                print(f"\n表格 {i+1}:")
                print(f"  行数: {len(table)}")
                print(f"  列数: {len(table[0]) if table else 0}")
                # 显示前3行
                for j, row in enumerate(table[:3]):
                    print(f"  行{j+1}: {row}")


if __name__ == '__main__':
    test_content_extraction()
