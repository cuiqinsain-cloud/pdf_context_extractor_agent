"""
测试脚本：查看财务报表注释章节的结构
用于分析福耀玻璃和深信服的注释章节内容
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader


def analyze_notes_structure(pdf_path: str, page_range: tuple, company_name: str):
    """
    分析注释章节的结构

    Args:
        pdf_path: PDF文件路径
        page_range: 页面范围 (start, end)
        company_name: 公司名称
    """
    print(f"\n{'='*80}")
    print(f"分析 {company_name} 的财务报表注释章节")
    print(f"页面范围: {page_range[0]} - {page_range[1]}")
    print(f"{'='*80}\n")

    with PDFReader(pdf_path) as pdf_reader:
        # 先分析前3页，了解结构
        start_page = page_range[0]
        sample_pages = min(3, page_range[1] - page_range[0] + 1)

        for i in range(sample_pages):
            page_num = start_page + i
            print(f"\n{'='*80}")
            print(f"第 {page_num} 页内容")
            print(f"{'='*80}\n")

            # 提取文本
            text = pdf_reader.extract_page_text(page_num)

            # 显示前2000字符
            print(text[:2000])
            print(f"\n... (共 {len(text)} 字符)")

            # 分析标题结构（查找数字开头的行）
            lines = text.split('\n')
            print(f"\n检测到的可能标题（数字开头的行）：")
            for line in lines[:50]:  # 只看前50行
                line = line.strip()
                # 匹配类似 "1. " 或 "1、" 或 "(1)" 开头的行
                if line and (
                    line[0].isdigit() or
                    line.startswith('(') and len(line) > 2 and line[1].isdigit()
                ):
                    print(f"  - {line[:100]}")


if __name__ == '__main__':
    # 测试数据路径
    base_path = os.path.join(os.path.dirname(__file__), 'sample_pdfs')

    # 福耀玻璃
    fuyao_pdf = os.path.join(base_path, '福耀玻璃：福耀玻璃2024年年度报告.pdf')
    fuyao_range = (125, 174)

    # 深信服
    sangfor_pdf = os.path.join(base_path, '深信服：2024年年度报告.PDF')
    sangfor_range = (162, 199)

    # 分析福耀玻璃
    if os.path.exists(fuyao_pdf):
        analyze_notes_structure(fuyao_pdf, fuyao_range, '福耀玻璃')
    else:
        print(f"文件不存在: {fuyao_pdf}")

    # 分析深信服
    if os.path.exists(sangfor_pdf):
        analyze_notes_structure(sangfor_pdf, sangfor_range, '深信服')
    else:
        print(f"文件不存在: {sangfor_pdf}")
