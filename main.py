"""
合并资产负债表提取器主入口
整合所有模块，提供统一的调用接口
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import logging

from src.pdf_reader import PDFReader
from src.table_extractor import TableExtractor
from src.parsers.balance_sheet import BalanceSheetParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialReportExtractor:
    """财务报表提取器主类"""

    def __init__(self, pdf_path: str):
        """
        初始化提取器

        Args:
            pdf_path (str): PDF文件路径
        """
        self.pdf_path = pdf_path
        self.pdf_reader = None
        self.table_extractor = TableExtractor()
        self.balance_sheet_parser = BalanceSheetParser()

        # 验证文件存在
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        logger.info(f"初始化财务报表提取器，PDF: {pdf_path}")

    def extract_balance_sheet(self, page_range: Tuple[int, int]) -> Dict[str, Any]:
        """
        提取合并资产负债表

        Args:
            page_range (Tuple[int, int]): 页面范围 (start, end)

        Returns:
            Dict[str, Any]: 提取结果
        """
        logger.info(f"开始提取合并资产负债表，页面范围: {page_range}")

        result = {
            'extraction_info': {
                'pdf_path': self.pdf_path,
                'page_range': page_range,
                'extraction_time': datetime.now().isoformat(),
                'version': '1.0.0'
            },
            'balance_sheet_data': None,
            'validation_result': None,
            'success': False,
            'error_message': None
        }

        try:
            # 1. 读取PDF页面
            with PDFReader(self.pdf_path) as reader:
                pages = reader.get_pages(page_range)
                logger.info(f"成功读取 {len(pages)} 个页面")

                # 2. 提取表格数据
                balance_sheet_tables = self.table_extractor.extract_balance_sheet_tables(pages)

                if not balance_sheet_tables:
                    raise ValueError("未能提取到合并资产负债表数据")

                # 3. 合并跨页表格
                merged_table = self.table_extractor.merge_cross_page_tables(balance_sheet_tables)

                # 4. 清洗表格数据
                cleaned_table = self.table_extractor.clean_table_data(merged_table)

                logger.info(f"表格数据处理完成，共 {len(cleaned_table)} 行")

                # 5. 解析资产负债表
                parsed_data = self.balance_sheet_parser.parse_balance_sheet(cleaned_table)

                # 6. 验证数据
                validation_result = self.balance_sheet_parser.validate_balance_sheet(parsed_data)

                # 7. 整合结果
                result['balance_sheet_data'] = parsed_data
                result['validation_result'] = validation_result
                result['success'] = True

                logger.info("合并资产负债表提取完成")

        except Exception as e:
            error_msg = f"提取过程中发生错误: {str(e)}"
            logger.error(error_msg)
            result['error_message'] = error_msg
            result['success'] = False

        return result

    def save_result(self, result: Dict[str, Any], output_path: str, format_type: str = 'json'):
        """
        保存提取结果

        Args:
            result (Dict[str, Any]): 提取结果
            output_path (str): 输出文件路径
            format_type (str): 输出格式 ('json', 'excel', 'csv')
        """
        logger.info(f"保存结果到: {output_path}, 格式: {format_type}")

        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if format_type.lower() == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

            elif format_type.lower() == 'excel':
                self._save_to_excel(result, output_path)

            elif format_type.lower() == 'csv':
                self._save_to_csv(result, output_path)

            else:
                raise ValueError(f"不支持的输出格式: {format_type}")

            logger.info(f"结果保存成功: {output_path}")

        except Exception as e:
            logger.error(f"保存结果时发生错误: {e}")
            raise

    def _save_to_excel(self, result: Dict[str, Any], output_path: str):
        """保存为Excel格式"""
        import pandas as pd

        if not result['success'] or not result['balance_sheet_data']:
            raise ValueError("没有有效的数据可以保存到Excel")

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 保存概要信息
            summary_data = {
                'extraction_time': [result['extraction_info']['extraction_time']],
                'pdf_path': [result['extraction_info']['pdf_path']],
                'page_range': [str(result['extraction_info']['page_range'])],
                'success': [result['success']],
                'validation_passed': [result['validation_result']['is_valid'] if result['validation_result'] else None]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

            # 使用原始顺序构建资产负债表数据
            balance_sheet_data = []
            balance_sheet = result['balance_sheet_data']

            # 添加大标题
            balance_sheet_data.append({
                'section': '合并资产负债表',
                'category': '',
                'item_name': '',
                'original_name': '',
                'current_period': '',
                'previous_period': '',
                'note': ''
            })

            # 空行
            balance_sheet_data.append({
                'section': '',
                'category': '',
                'item_name': '',
                'original_name': '',
                'current_period': '',
                'previous_period': '',
                'note': ''
            })

            # 如果存在ordered_items，使用原始顺序
            if 'ordered_items' in balance_sheet:
                current_section = None
                current_category = None

                for item in balance_sheet['ordered_items']:
                    section_path = item['section']
                    data = item['data']

                    # 确定显示的部分和类别
                    if section_path.startswith('assets.current_assets'):
                        if current_section != '资产':
                            current_section = '资产'
                            balance_sheet_data.append({
                                'section': '资产',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                        if current_category != '流动资产':
                            current_category = '流动资产'
                            balance_sheet_data.append({
                                'section': '',
                                'category': '流动资产',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                    elif section_path.startswith('assets.non_current_assets'):
                        if current_section != '资产':
                            current_section = '资产'
                            balance_sheet_data.append({
                                'section': '资产',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                        if current_category != '非流动资产':
                            current_category = '非流动资产'
                            balance_sheet_data.append({
                                'section': '',
                                'category': '非流动资产',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                    elif section_path == 'assets.assets_total':
                        current_category = None  # 总计不需要类别

                    elif section_path.startswith('liabilities.current_liabilities'):
                        if current_section != '负债和所有者权益':
                            current_section = '负债和所有者权益'
                            # 添加空行
                            balance_sheet_data.append({
                                'section': '',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })
                            balance_sheet_data.append({
                                'section': '负债和所有者权益',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                        if current_category != '流动负债':
                            current_category = '流动负债'
                            balance_sheet_data.append({
                                'section': '',
                                'category': '流动负债',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                    elif section_path.startswith('liabilities.non_current_liabilities'):
                        if current_section != '负债和所有者权益':
                            current_section = '负债和所有者权益'
                            # 添加空行
                            balance_sheet_data.append({
                                'section': '',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })
                            balance_sheet_data.append({
                                'section': '负债和所有者权益',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                        if current_category != '非流动负债':
                            current_category = '非流动负债'
                            balance_sheet_data.append({
                                'section': '',
                                'category': '非流动负债',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                    elif section_path.startswith('equity'):
                        if current_section != '负债和所有者权益':
                            current_section = '负债和所有者权益'
                            # 添加空行
                            balance_sheet_data.append({
                                'section': '',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })
                            balance_sheet_data.append({
                                'section': '负债和所有者权益',
                                'category': '',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                        if current_category != '所有者权益':
                            current_category = '所有者权益'
                            balance_sheet_data.append({
                                'section': '',
                                'category': '所有者权益',
                                'item_name': '',
                                'original_name': '',
                                'current_period': '',
                                'previous_period': '',
                                'note': ''
                            })

                    elif section_path in ['liabilities.liabilities_total', 'liabilities_and_equity_total']:
                        current_category = None  # 总计不需要类别

                    # 添加具体项目
                    balance_sheet_data.append({
                        'section': '',
                        'category': '',
                        'item_name': data.get('original_name', ''),
                        'original_name': data.get('original_name', ''),
                        'current_period': data.get('current_period', ''),
                        'previous_period': data.get('previous_period', ''),
                        'note': data.get('note', '')
                    })
            else:
                # 如果没有ordered_items，使用旧的逻辑（向后兼容）
                # ... 这里可以保留原来的逻辑作为fallback
                pass

            # 将数据保存到资产负债表sheet
            df = pd.DataFrame(balance_sheet_data)
            df.columns = ['部分', '类别', '项目名称', '原始名称', '本期末金额', '上期末金额', '附注']
            df.to_excel(writer, sheet_name='资产负债表', index=False)

            # 格式化Excel样式
            workbook = writer.book
            worksheet = writer.sheets['资产负债表']

            # 设置列宽
            worksheet.column_dimensions['A'].width = 15  # 部分
            worksheet.column_dimensions['B'].width = 15  # 类别
            worksheet.column_dimensions['C'].width = 20  # 项目名称
            worksheet.column_dimensions['D'].width = 20  # 原始名称
            worksheet.column_dimensions['E'].width = 15  # 本期末金额
            worksheet.column_dimensions['F'].width = 15  # 上期末金额
            worksheet.column_dimensions['G'].width = 10  # 附注

    def _save_to_csv(self, result: Dict[str, Any], output_path: str):
        """保存为CSV格式"""
        import pandas as pd

        if not result['success'] or not result['balance_sheet_data']:
            raise ValueError("没有有效的数据可以保存到CSV")

        # 将所有数据合并为一个表格
        all_data = []
        balance_sheet = result['balance_sheet_data']

        # 资产数据
        for category in ['current_assets', 'non_current_assets']:
            for item_name, item_data in balance_sheet['assets'][category].items():
                all_data.append({
                    'section': 'assets',
                    'category': category,
                    'item_name': item_name,
                    'original_name': item_data.get('original_name', ''),
                    'current_period': item_data.get('current_period', ''),
                    'previous_period': item_data.get('previous_period', ''),
                    'note': item_data.get('note', '')
                })

        # 负债数据
        for category in ['current_liabilities', 'non_current_liabilities']:
            for item_name, item_data in balance_sheet['liabilities'][category].items():
                all_data.append({
                    'section': 'liabilities',
                    'category': category,
                    'item_name': item_name,
                    'original_name': item_data.get('original_name', ''),
                    'current_period': item_data.get('current_period', ''),
                    'previous_period': item_data.get('previous_period', ''),
                    'note': item_data.get('note', '')
                })

        # 权益数据
        for item_name, item_data in balance_sheet['equity'].items():
            all_data.append({
                'section': 'equity',
                'category': 'equity',
                'item_name': item_name,
                'original_name': item_data.get('original_name', ''),
                'current_period': item_data.get('current_period', ''),
                'previous_period': item_data.get('previous_period', ''),
                'note': item_data.get('note', '')
            })

        pd.DataFrame(all_data).to_csv(output_path, index=False, encoding='utf-8-sig')

    def get_extraction_summary(self, result: Dict[str, Any]) -> str:
        """
        生成提取结果摘要

        Args:
            result (Dict[str, Any]): 提取结果

        Returns:
            str: 结果摘要
        """
        if not result['success']:
            return f"提取失败: {result.get('error_message', '未知错误')}"

        balance_sheet = result['balance_sheet_data']
        validation = result['validation_result']

        # 安全获取平衡性检查状态
        balance_check = validation.get('balance_check') or {}
        balance_status = balance_check.get('status', '未知') if isinstance(balance_check, dict) else '未知'

        summary_lines = [
            "=== 合并资产负债表提取摘要 ===",
            f"提取时间: {result['extraction_info']['extraction_time']}",
            f"页面范围: {result['extraction_info']['page_range']}",
            f"",
            f"数据统计:",
            f"- 流动资产项目: {len(balance_sheet['assets']['current_assets'])}",
            f"- 非流动资产项目: {len(balance_sheet['assets']['non_current_assets'])}",
            f"- 流动负债项目: {len(balance_sheet['liabilities']['current_liabilities'])}",
            f"- 非流动负债项目: {len(balance_sheet['liabilities']['non_current_liabilities'])}",
            f"- 所有者权益项目: {len(balance_sheet['equity'])}",
            f"",
            f"验证结果:",
            f"- 整体验证: {'通过' if validation['is_valid'] else '失败'}",
            f"- 平衡性检查: {balance_status}",
            f"- 完整性评分: {validation.get('completeness_score', 0):.1%}",
            f"- 匹配项目数: {balance_sheet['parsing_info']['matched_items']}",
            f"- 未匹配项目数: {len(balance_sheet['parsing_info']['unmatched_items'])}",
        ]

        if validation['errors']:
            summary_lines.extend([
                f"",
                f"错误信息:",
                *[f"- {error}" for error in validation['errors']]
            ])

        if validation['warnings']:
            summary_lines.extend([
                f"",
                f"警告信息:",
                *[f"- {warning}" for warning in validation['warnings']]
            ])

        return "\n".join(summary_lines)


def main():
    """主函数，提供命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='财务报表数据提取工具')
    parser.add_argument('pdf_path', help='PDF文件路径')
    parser.add_argument('--pages', required=True, help='页面范围，格式: start-end (如: 126-128)')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--format', choices=['json', 'excel', 'csv'], default='json', help='输出格式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # 解析页面范围
        start_page, end_page = map(int, args.pages.split('-'))
        page_range = (start_page, end_page)

        # 创建提取器
        extractor = FinancialReportExtractor(args.pdf_path)

        # 执行提取
        result = extractor.extract_balance_sheet(page_range)

        # 输出摘要
        summary = extractor.get_extraction_summary(result)
        print(summary)

        # 保存结果
        if args.output:
            extractor.save_result(result, args.output, args.format)
            print(f"\n结果已保存到: {args.output}")
        else:
            # 默认保存到output目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/balance_sheet_{timestamp}.{args.format}"
            extractor.save_result(result, output_path, args.format)
            print(f"\n结果已保存到: {output_path}")

    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())