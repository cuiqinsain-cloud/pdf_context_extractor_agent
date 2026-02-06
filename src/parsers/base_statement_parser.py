"""
财务报表解析器基类
提供统一的表头识别和数据提取逻辑
"""
import re
from typing import Dict, List, Optional, Any
import logging
from .column_analyzer import ColumnAnalyzer, ColumnType
from .statement_structure_identifier import StatementStructureIdentifier

logger = logging.getLogger(__name__)


class BaseStatementParser:
    """财务报表解析器基类"""

    def __init__(self, statement_type: str):
        """
        初始化解析器

        Args:
            statement_type: 报表类型 ('balance_sheet', 'income_statement', 'cash_flow')
        """
        self.statement_type = statement_type
        self.column_analyzer = ColumnAnalyzer()
        self.structure_identifier = StatementStructureIdentifier(statement_type)

    def identify_statement_structure(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        识别报表结构

        Args:
            table_data: 表格数据

        Returns:
            Dict: 结构识别结果
        """
        return self.structure_identifier.identify_structure(table_data)

    def extract_statement_data(self, table_data: List[List[str]],
                              structure_result: Dict[str, Any]) -> List[List[str]]:
        """
        根据结构识别结果提取报表数据

        Args:
            table_data: 完整的表格数据
            structure_result: 结构识别结果

        Returns:
            List[List[str]]: 提取的报表数据（只包含有效范围）
        """
        if not structure_result['is_valid']:
            logger.warning("结构识别失败，返回完整数据")
            return table_data

        start_row = structure_result['start_row']
        end_row = structure_result['end_row']

        if start_row is None or end_row is None:
            logger.warning("未找到有效的数据范围，返回完整数据")
            return table_data

        # 提取有效范围的数据
        extracted_data = table_data[start_row:end_row + 1]
        logger.info(f"提取数据范围: 第{start_row}行 到 第{end_row}行，共{len(extracted_data)}行")

        return extracted_data

    def get_header_info(self, table_data: List[List[str]],
                       structure_result: Dict[str, Any]) -> Dict[str, int]:
        """
        获取表头信息

        Args:
            table_data: 表格数据
            structure_result: 结构识别结果

        Returns:
            Dict[str, int]: 表头列索引映射
        """
        header_info = {
            'item_name_col': 0,
            'current_period_col': None,
            'previous_period_col': None,
            'note_col': None
        }

        if not structure_result['is_valid']:
            return header_info

        header_row_idx = structure_result['header_row']
        if header_row_idx is None or header_row_idx >= len(table_data):
            return header_info

        # 使用 ColumnAnalyzer 分析表头行
        header_row = table_data[header_row_idx]
        column_map = self.column_analyzer.analyze_row_structure(header_row, use_cache=False)

        # 转换为 header_info 格式
        if ColumnType.ITEM_NAME in column_map:
            header_info['item_name_col'] = column_map[ColumnType.ITEM_NAME]
        if ColumnType.CURRENT_PERIOD in column_map:
            header_info['current_period_col'] = column_map[ColumnType.CURRENT_PERIOD]
        if ColumnType.PREVIOUS_PERIOD in column_map:
            header_info['previous_period_col'] = column_map[ColumnType.PREVIOUS_PERIOD]
        if ColumnType.NOTE in column_map:
            header_info['note_col'] = column_map[ColumnType.NOTE]

        logger.info(f"表头信息: {header_info}")

        return header_info

    def extract_values_from_row(self, row: List[str], header_info: Dict[str, int]) -> Dict[str, str]:
        """
        从行数据中提取数值
        使用 ColumnAnalyzer 进行动态列结构识别

        Args:
            row: 行数据
            header_info: 表头信息

        Returns:
            Dict[str, str]: 提取的数值
        """
        values = {}

        # 检查行的列数是否与表头匹配
        row_col_count = len(row)
        expected_col_count = max(
            header_info.get('current_period_col', 0) or 0,
            header_info.get('previous_period_col', 0) or 0
        ) + 1

        # 如果列数不匹配或没有表头信息，使用 ColumnAnalyzer 动态分析
        if (header_info['current_period_col'] is None or
            row_col_count < expected_col_count or
            abs(row_col_count - expected_col_count) > 1):

            column_map = self.column_analyzer.analyze_row_structure(row, use_cache=False)
            extracted_values = self.column_analyzer.extract_values_from_row(row, column_map)

            if 'current_period' in extracted_values:
                values['current_period'] = extracted_values['current_period']
            if 'previous_period' in extracted_values:
                values['previous_period'] = extracted_values['previous_period']
            if 'note' in extracted_values:
                values['note'] = extracted_values['note']

            return values

        # 使用标准的列索引提取
        column_map = {}
        if header_info.get('item_name_col') is not None:
            column_map[ColumnType.ITEM_NAME] = header_info['item_name_col']
        if header_info.get('current_period_col') is not None:
            column_map[ColumnType.CURRENT_PERIOD] = header_info['current_period_col']
        if header_info.get('previous_period_col') is not None:
            column_map[ColumnType.PREVIOUS_PERIOD] = header_info['previous_period_col']
        if header_info.get('note_col') is not None:
            column_map[ColumnType.NOTE] = header_info['note_col']

        extracted_values = self.column_analyzer.extract_values_from_row(row, column_map)

        if 'current_period' in extracted_values:
            values['current_period'] = extracted_values['current_period']
        if 'previous_period' in extracted_values:
            values['previous_period'] = extracted_values['previous_period']
        if 'note' in extracted_values:
            values['note'] = extracted_values['note']

        return values

    def get_item_name_from_row(self, row: List[str], header_info: Dict[str, int]) -> str:
        """
        从行中获取项目名称

        Args:
            row: 行数据
            header_info: 表头信息

        Returns:
            str: 项目名称
        """
        item_name_col = header_info.get('item_name_col', 0)

        # 检查第0列和第1列（处理深信服等特殊格式）
        for col_idx in [item_name_col, 0, 1]:
            if col_idx < len(row) and row[col_idx]:
                item_name = str(row[col_idx]).strip()
                item_name = item_name.replace('\n', '').replace('\r', '').strip()
                if item_name:
                    return item_name

        return ""

    def reset_cache(self):
        """重置缓存"""
        self.column_analyzer.reset_cache()
        logger.info("解析器缓存已重置")
