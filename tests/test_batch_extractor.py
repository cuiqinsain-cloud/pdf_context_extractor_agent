"""
测试批量注释提取器
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
        logging.FileHandler('/tmp/batch_notes_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_batch_extractor():
    """测试批量提取器"""

    # 使用 ConfigLoader 加载配置
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        llm_config = config['llm_api']

        # 检查 API key
        if not llm_config.get('api_key'):
            logger.error("API key 未设置，请设置环境变量 LLM_API_KEY")
            return

        logger.info(f"使用配置: provider={llm_config['provider']}, model={llm_config['model']}")

    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return

    # PDF路径
    pdf_path = 'tests/sample_pdfs/福耀玻璃：福耀玻璃2024年年度报告.pdf'

    # 测试不同的批量大小
    batch_sizes = [5, 10]
    page_range = (125, 134)  # 先测试10页

    for batch_size in batch_sizes:
        logger.info(f"\n{'='*60}")
        logger.info(f"测试批量大小: {batch_size} 页/批次")
        logger.info(f"{'='*60}")

        start_time = time.time()

        try:
            # 创建提取器
            extractor = BatchNotesExtractor(llm_config, batch_size=batch_size)

            # 读取PDF
            with PDFReader(pdf_path) as pdf_reader:
                pages = pdf_reader.get_pages(page_range)

                # 批量提取
                result = extractor.extract_notes_from_pages_batch(
                    pages,
                    start_page_num=page_range[0]
                )

                end_time = time.time()
                elapsed = end_time - start_time

                # 输出结果
                logger.info(f"\n提取完成:")
                logger.info(f"  成功: {result['success']}")
                logger.info(f"  总页数: {result['total_pages']}")
                logger.info(f"  提取标题数: {result['total_notes']}")
                logger.info(f"  耗时: {elapsed:.2f} 秒")
                logger.info(f"  平均速度: {elapsed/result['total_pages']:.2f} 秒/页")
                logger.info(f"  错误数: {len(result['errors'])}")

                if result['errors']:
                    logger.warning(f"  错误信息: {result['errors']}")

                # 保存结果
                output_file = f'/tmp/batch_notes_result_{batch_size}.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"  结果已保存到: {output_file}")

                # 显示前3个标题
                if result['notes']:
                    logger.info(f"\n前3个标题:")
                    for i, note in enumerate(result['notes'][:3], 1):
                        logger.info(
                            f"  {i}. [{note['page_num']}页] "
                            f"{note['full_title']} "
                            f"(level={note['level']})"
                        )

        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)


def compare_with_original():
    """对比原始方法和批量方法的性能"""

    logger.info(f"\n{'='*60}")
    logger.info("性能对比测试")
    logger.info(f"{'='*60}")

    # 原始方法预估
    pages_count = 10
    original_time_per_page = 60  # 秒
    original_total = pages_count * original_time_per_page

    logger.info(f"\n原始方法（逐页处理）:")
    logger.info(f"  页数: {pages_count}")
    logger.info(f"  LLM调用次数: {pages_count}")
    logger.info(f"  预估耗时: {original_total} 秒 ({original_total/60:.1f} 分钟)")

    # 批量方法预估
    batch_size = 5
    batch_count = pages_count // batch_size
    batch_time_per_call = 90  # 秒（批量处理稍慢）
    batch_total = batch_count * batch_time_per_call

    logger.info(f"\n批量方法（{batch_size}页/批次）:")
    logger.info(f"  页数: {pages_count}")
    logger.info(f"  LLM调用次数: {batch_count}")
    logger.info(f"  预估耗时: {batch_total} 秒 ({batch_total/60:.1f} 分钟)")
    logger.info(f"  性能提升: {original_total/batch_total:.1f}x")


if __name__ == '__main__':
    # 先显示性能对比
    compare_with_original()

    # 运行测试
    test_batch_extractor()
