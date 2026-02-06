"""
完整测试：福耀玻璃注释章节提取（125-174页）
"""
import sys
import os
import json
import time
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


def test_full_notes_extraction():
    """完整测试福耀玻璃注释章节"""
    print(f"\n{'='*80}")
    print(f"福耀玻璃 - 完整注释章节提取测试")
    print(f"页面范围: 125 - 174 (共50页)")
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

    # PDF路径
    pdf_path = os.path.join(
        os.path.dirname(__file__),
        'sample_pdfs',
        '福耀玻璃：福耀玻璃2024年年度报告.pdf'
    )

    if not os.path.exists(pdf_path):
        print(f"✗ PDF文件不存在: {pdf_path}")
        return

    # 创建提取器
    extractor = NotesExtractor(llm_config)

    # 记录开始时间
    start_time = time.time()

    # 读取PDF
    with PDFReader(pdf_path) as pdf_reader:
        print(f"\n开始提取页面 125 - 174...")
        print(f"预计耗时: 25-50分钟（取决于LLM响应速度）")
        print(f"{'='*80}\n")

        # 提取所有页面
        pages = pdf_reader.get_pages((125, 174))

        # 提取注释
        result = extractor.extract_notes_from_pages(pages, 125)

        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time

        # 显示结果
        print(f"\n{'='*80}")
        print(f"提取完成")
        print(f"{'='*80}\n")

        print(f"成功: {result['success']}")
        print(f"总页数: {result['total_pages']}")
        print(f"提取的注释数量: {result['total_notes']}")
        print(f"耗时: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)")
        print(f"平均每页: {elapsed_time/result['total_pages']:.1f}秒")

        if result['errors']:
            print(f"\n错误:")
            for error in result['errors']:
                print(f"  - {error}")

        # 统计信息
        print(f"\n{'='*80}")
        print(f"统计信息")
        print(f"{'='*80}\n")

        # 按层级统计
        level_1_count = sum(1 for n in result['notes'] if n['level'] == 1)
        level_2_count = sum(1 for n in result['notes'] if n['level'] == 2)
        print(f"主标题数量: {level_1_count}")
        print(f"子标题数量: {level_2_count}")

        # 统计包含表格的注释
        with_table_count = sum(1 for n in result['notes'] if n['has_table'])
        print(f"包含表格的注释: {with_table_count}")

        # 统计总表格数
        total_tables = sum(
            n['content']['table_count']
            for n in result['notes']
            if isinstance(n.get('content'), dict)
        )
        print(f"总表格数量: {total_tables}")

        # 显示前10个注释
        print(f"\n{'='*80}")
        print(f"前10个注释预览")
        print(f"{'='*80}\n")

        for i, note in enumerate(result['notes'][:10], 1):
            indent = "  " if note['level'] == 2 else ""
            print(f"{i}. {indent}{note['full_title']} (页码: {note['page_num']})")
            if note['has_table']:
                table_count = note['content'].get('table_count', 0)
                print(f"   {indent}└─ 包含 {table_count} 个表格")

        if len(result['notes']) > 10:
            print(f"\n... 还有 {len(result['notes']) - 10} 个注释")

        # 保存结果
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(
            output_dir,
            f'福耀玻璃_完整注释_{int(time.time())}.json'
        )

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_file}")

        # 生成摘要报告
        summary_file = os.path.join(
            output_dir,
            f'福耀玻璃_注释摘要_{int(time.time())}.txt'
        )

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"福耀玻璃 - 财务报表注释提取报告\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"提取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"页面范围: 125 - 174 (共{result['total_pages']}页)\n")
            f.write(f"提取耗时: {elapsed_time:.1f}秒 ({elapsed_time/60:.1f}分钟)\n")
            f.write(f"平均每页: {elapsed_time/result['total_pages']:.1f}秒\n\n")

            f.write(f"统计信息:\n")
            f.write(f"  - 总注释数量: {result['total_notes']}\n")
            f.write(f"  - 主标题数量: {level_1_count}\n")
            f.write(f"  - 子标题数量: {level_2_count}\n")
            f.write(f"  - 包含表格: {with_table_count}\n")
            f.write(f"  - 总表格数: {total_tables}\n\n")

            if result['errors']:
                f.write(f"错误信息:\n")
                for error in result['errors']:
                    f.write(f"  - {error}\n")
                f.write(f"\n")

            f.write(f"注释列表:\n")
            f.write(f"{'-'*80}\n\n")

            for i, note in enumerate(result['notes'], 1):
                indent = "  " if note['level'] == 2 else ""
                f.write(f"{i}. {indent}{note['full_title']}\n")
                f.write(f"   {indent}页码: {note['page_num']}\n")
                if note['has_table']:
                    table_count = note['content'].get('table_count', 0)
                    f.write(f"   {indent}表格: {table_count}个\n")
                f.write(f"\n")

        print(f"摘要报告已保存到: {summary_file}")


if __name__ == '__main__':
    test_full_notes_extraction()
