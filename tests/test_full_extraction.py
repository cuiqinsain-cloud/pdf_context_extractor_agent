"""
完整提取福耀玻璃合并资产负债表附注
"""
import sys
import os
import json
import time
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pdf_reader import PDFReader
from src.parsers.batch_notes_extractor import BatchNotesExtractor
from src.parsers.config_loader import ConfigLoader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/full_extraction.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def extract_full_notes():
    """完整提取财务报表附注"""

    # 使用 ConfigLoader 加载配置
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        llm_config = config['llm_api']

        # 检查 API key
        if not llm_config.get('api_key'):
            logger.error("API key 未设置，请设置环境变量 LLM_API_KEY")
            return None

        logger.info(f"使用配置: provider={llm_config['provider']}, model={llm_config['model']}")

    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return None

    # PDF路径
    pdf_path = 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf'

    # 合并资产负债表附注通常在第125页开始
    # 完整提取所有附注内容
    page_range = (125, 200)  # 提取到文件末尾
    batch_size = 5

    logger.info(f"\n{'='*60}")
    logger.info(f"完整提取合并资产负债表附注")
    logger.info(f"{'='*60}")
    logger.info(f"页面范围: {page_range[0]}-{page_range[1]}")
    logger.info(f"批次大小: {batch_size} 页/批次")

    start_time = time.time()

    try:
        # 创建提取器
        extractor = BatchNotesExtractor(llm_config, batch_size=batch_size)

        # 读取PDF
        with PDFReader(pdf_path) as pdf_reader:
            pages = pdf_reader.get_pages(page_range)

            # 批量提取
            logger.info(f"开始提取 {len(pages)} 页内容...")
            result = extractor.extract_notes_from_pages_batch(
                pages,
                start_page_num=page_range[0]
            )

            end_time = time.time()
            elapsed = end_time - start_time

            # 输出结果
            logger.info(f"\n{'='*60}")
            logger.info(f"提取完成")
            logger.info(f"{'='*60}")
            logger.info(f"  成功: {result['success']}")
            logger.info(f"  总页数: {result['total_pages']}")
            logger.info(f"  提取注释数: {result['total_notes']}")
            logger.info(f"  总耗时: {elapsed:.2f} 秒 ({elapsed/60:.1f} 分钟)")
            logger.info(f"  平均速度: {elapsed/result['total_pages']:.2f} 秒/页")
            logger.info(f"  错误数: {len(result['errors'])}")

            if result['errors']:
                logger.warning(f"\n错误信息:")
                for error in result['errors']:
                    logger.warning(f"  - {error}")

            # 保存结果
            output_file = '/tmp/batch_notes_result_full.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"\n✓ 结果已保存到 {output_file}")

            # 统计信息
            level1_notes = [n for n in result['notes'] if n['level'] == 1]
            level2_notes = [n for n in result['notes'] if n['level'] == 2]
            notes_with_tables = [n for n in result['notes'] if n.get('tables')]
            total_tables = sum(len(n.get('tables', [])) for n in result['notes'])

            logger.info(f"\n统计信息：")
            logger.info(f"  一级注释: {len(level1_notes)}")
            logger.info(f"  二级注释: {len(level2_notes)}")
            logger.info(f"  包含表格的注释: {len(notes_with_tables)}/{result['total_notes']}")
            logger.info(f"  总表格数: {total_tables}")

            # 显示前10个标题
            if result['notes']:
                logger.info(f"\n前10个注释标题:")
                for i, note in enumerate(result['notes'][:10], 1):
                    tables_info = f", {len(note.get('tables', []))}个表格" if note.get('tables') else ""
                    logger.info(
                        f"  {i}. [{note['page_num']}页] "
                        f"{note['full_title']} "
                        f"(level={note['level']}{tables_info})"
                    )

            return result

    except Exception as e:
        logger.error(f"提取失败: {e}", exc_info=True)
        return None


if __name__ == '__main__':
    result = extract_full_notes()
    if result:
        logger.info(f"\n{'='*60}")
        logger.info("提取成功！")
        logger.info(f"{'='*60}")
