"""
测试财务报表注释提取器
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pdf_reader import PDFReader
from src.parsers.notes_extractor import NotesExtractor


def load_llm_config():
    """加载LLM配置"""
    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'llm_config.json'
    )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 获取API key
    api_key_env = config['llm_api'].get('api_key_env', 'LLM_API_KEY')
    api_key = os.environ.get(api_key_env)

    if not api_key:
        raise ValueError(f"环境变量 {api_key_env} 未设置")

    # 构建LLM配置
    llm_config = config['llm_api'].copy()
    llm_config['api_key'] = api_key

    return llm_config


def test_notes_extraction(pdf_path: str, page_range: tuple, company_name: str, sample_pages: int = 3):
    """
    测试注释提取

    Args:
        pdf_path: PDF文件路径
        page_range: 页面范围 (start, end)
        company_name: 公司名称
        sample_pages: 测试的页面数量
    """
    print(f"\n{'='*80}")
    print(f"测试 {company_name} 的注释提取")
    print(f"页面范围: {page_range[0]} - {page_range[1]}")
    print(f"测试页数: {sample_pages}")
    print(f"{'='*80}\n")

    # 加载LLM配置
    try:
        llm_config = load_llm_config()
        print(f"✓ LLM配置加载成功")
        print(f"  Provider: {llm_config['provider']}")
        print(f"  Model: {llm_config['model']}")
    except Exception as e:
        print(f"✗ LLM配置加载失败: {e}")
        return

    # 创建注释提取器
    extractor = NotesExtractor(llm_config)

    # 读取PDF
    with PDFReader(pdf_path) as pdf_reader:
        # 只测试前几页
        start_page = page_range[0]
        end_page = min(start_page + sample_pages - 1, page_range[1])

        print(f"\n提取页面 {start_page} - {end_page}")

        pages = pdf_reader.get_pages((start_page, end_page))

        # 提取注释
        result = extractor.extract_notes_from_pages(pages, start_page)

        # 显示结果
        print(f"\n{'='*80}")
        print(f"提取结果")
        print(f"{'='*80}\n")

        print(f"成功: {result['success']}")
        print(f"总页数: {result['total_pages']}")
        print(f"提取的注释数量: {result['total_notes']}")

        if result['errors']:
            print(f"\n错误:")
            for error in result['errors']:
                print(f"  - {error}")

        if result['notes']:
            print(f"\n提取的注释:")
            for i, note in enumerate(result['notes'], 1):
                print(f"\n{i}. 注释 {note['number']}")
                print(f"   标题: {note['full_title']}")
                print(f"   层级: {note['level']}")
                print(f"   页码: {note['page_num']}")
                print(f"   完整: {note['is_complete']}")
                print(f"   包含表格: {note['has_table']}")

                # 显示内容摘要
                if isinstance(note.get('content'), dict):
                    content = note['content']
                    text = content.get('text', '')
                    table_count = content.get('table_count', 0)

                    if text:
                        # 只显示前200字符
                        text_preview = text[:200] + '...' if len(text) > 200 else text
                        print(f"   文本内容: {text_preview}")

                    if table_count > 0:
                        print(f"   表格数量: {table_count}")
                        # 显示第一个表格的维度
                        tables = content.get('tables', [])
                        if tables:
                            first_table = tables[0]
                            rows = len(first_table)
                            cols = len(first_table[0]) if first_table else 0
                            print(f"   第一个表格维度: {rows}行 x {cols}列")

        # 保存结果到文件
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(
            output_dir,
            f'{company_name}_notes_test.json'
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_file}")


if __name__ == '__main__':
    # 测试数据路径
    base_path = os.path.join(os.path.dirname(__file__), 'sample_pdfs')

    # 福耀玻璃
    fuyao_pdf = os.path.join(base_path, '福耀玻璃：福耀玻璃2024年年度报告.pdf')
    fuyao_range = (125, 174)

    # 深信服
    sangfor_pdf = os.path.join(base_path, '深信服：2024年年度报告.PDF')
    sangfor_range = (162, 199)

    # 测试福耀玻璃（前3页）
    if os.path.exists(fuyao_pdf):
        test_notes_extraction(fuyao_pdf, fuyao_range, '福耀玻璃', sample_pages=3)
    else:
        print(f"文件不存在: {fuyao_pdf}")

    print("\n" + "="*80 + "\n")

    # 测试深信服（前3页）
    if os.path.exists(sangfor_pdf):
        test_notes_extraction(sangfor_pdf, sangfor_range, '深信服', sample_pages=3)
    else:
        print(f"文件不存在: {sangfor_pdf}")
