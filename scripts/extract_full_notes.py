#!/usr/bin/env python3
"""
完整文档注释提取脚本

使用批量处理方法提取完整的财务报表注释章节
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parsers.batch_notes_extractor import BatchNotesExtractor
from src.parsers.config_loader import load_llm_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def extract_full_document(
    pdf_path: str,
    start_page: int,
    end_page: int,
    output_path: str,
    batch_size: int = 5
):
    """
    提取完整文档的注释内容

    Args:
        pdf_path: PDF文件路径
        start_page: 起始页码
        end_page: 结束页码
        output_path: 输出JSON文件路径
        batch_size: 批次大小（默认5页）
    """
    logger.info("=" * 70)
    logger.info("开始提取完整文档注释")
    logger.info("=" * 70)
    logger.info(f"PDF文件: {pdf_path}")
    logger.info(f"页码范围: {start_page}-{end_page} (共{end_page - start_page + 1}页)")
    logger.info(f"批次大小: {batch_size}页/批次")
    logger.info(f"输出文件: {output_path}")
    logger.info("")

    # 加载配置
    config = load_llm_config()
    logger.info(f"使用配置: provider={config['provider']}, model={config['model']}")
    logger.info("")

    # 创建提取器
    extractor = BatchNotesExtractor(
        provider=config['provider'],
        model=config['model'],
        api_key=config.get('api_key'),
        base_url=config.get('base_url')
    )

    # 预估时间
    total_pages = end_page - start_page + 1
    num_batches = (total_pages + batch_size - 1) // batch_size
    estimated_time = num_batches * 2.3  # 每批次约2.3分钟

    logger.info(f"预估信息:")
    logger.info(f"  • 批次数: {num_batches}")
    logger.info(f"  • 预估耗时: {estimated_time:.1f}分钟")
    logger.info(f"  • LLM调用次数: {num_batches}次")
    logger.info("")

    # 开始提取
    start_time = datetime.now()
    logger.info("开始提取...")
    logger.info("")

    try:
        result = extractor.extract_notes_batch(
            pdf_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            batch_size=batch_size
        )

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 打印结果
        logger.info("")
        logger.info("=" * 70)
        logger.info("提取完成！")
        logger.info("=" * 70)
        logger.info(f"成功: {result['success']}")
        logger.info(f"总页数: {result['total_pages']}")
        logger.info(f"提取标题数: {result['total_notes']}")
        logger.info(f"实际耗时: {elapsed:.2f}秒 ({elapsed/60:.1f}分钟)")
        logger.info(f"平均速度: {elapsed/total_pages:.2f}秒/页")

        if result['errors']:
            logger.warning(f"错误数: {len(result['errors'])}")
            for error in result['errors']:
                logger.warning(f"  • {error}")

        logger.info(f"结果已保存到: {output_path}")
        logger.info("")

        # 统计信息
        notes_with_content = sum(1 for n in result['notes'] if n.get('content'))
        notes_with_tables = sum(1 for n in result['notes'] if n.get('has_table'))
        total_tables = sum(n.get('content', {}).get('table_count', 0) for n in result['notes'])

        logger.info("内容统计:")
        logger.info(f"  • 包含内容的标题: {notes_with_content}/{result['total_notes']} ({notes_with_content/result['total_notes']*100:.1f}%)")
        logger.info(f"  • 包含表格的标题: {notes_with_tables}/{result['total_notes']} ({notes_with_tables/result['total_notes']*100:.1f}%)")
        logger.info(f"  • 总表格数: {total_tables}")
        logger.info("")

        # 显示前10个标题
        logger.info("前10个标题:")
        for i, note in enumerate(result['notes'][:10], 1):
            has_content = "✓" if note.get('content') else "✗"
            has_table = "📊" if note.get('has_table') else ""
            logger.info(f"  {i:2d}. [{note['page_num']:3d}页] {note['full_title']:<40s} {has_content} {has_table}")

        if result['total_notes'] > 10:
            logger.info(f"  ... 还有 {result['total_notes'] - 10} 个标题")

        logger.info("")
        logger.info("=" * 70)

        return result

    except Exception as e:
        logger.error(f"提取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='提取完整文档的财务报表注释')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('start_page', type=int, help='起始页码')
    parser.add_argument('end_page', type=int, help='结束页码')
    parser.add_argument('-o', '--output', help='输出JSON文件路径（默认：output/notes_full.json）')
    parser.add_argument('-b', '--batch-size', type=int, default=5, help='批次大小（默认：5）')

    args = parser.parse_args()

    # 设置默认输出路径
    if args.output is None:
        output_dir = project_root / 'output'
        output_dir.mkdir(exist_ok=True)
        args.output = str(output_dir / 'notes_full.json')

    # 执行提取
    extract_full_document(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        output_path=args.output,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()
