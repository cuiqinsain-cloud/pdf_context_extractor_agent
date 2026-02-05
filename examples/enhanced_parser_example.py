"""
优化后的资产负债表解析器集成示例
展示如何使用新的列分析器和LLM辅助
"""
import logging
from typing import List, Dict, Any
from src.parsers.column_analyzer import ColumnAnalyzer, ColumnType
from src.parsers.llm_assistant import LLMAssistant, KeywordLibrary

logger = logging.getLogger(__name__)


class EnhancedBalanceSheetParser:
    """
    增强版资产负债表解析器

    主要改进：
    1. 动态列结构识别，支持跨页列数变化
    2. 基于关键字库的灵活匹配
    3. LLM辅助处理不确定情况
    4. 无硬编码，完全自适应
    """

    def __init__(self, enable_llm: bool = False, keyword_library_path: str = None):
        """
        初始化解析器

        Args:
            enable_llm: 是否启用LLM辅助
            keyword_library_path: 关键字库文件路径
        """
        # 初始化列分析器
        self.column_analyzer = ColumnAnalyzer()

        # 初始化LLM辅助器
        self.llm_assistant = LLMAssistant(enable_llm=enable_llm)

        # 初始化关键字库
        self.keyword_library = KeywordLibrary(library_path=keyword_library_path)

        # 将关键字库注入到列分析器
        self.column_analyzer.column_keywords = {
            ColumnType.ITEM_NAME: self.keyword_library.get_keywords('item_name'),
            ColumnType.CURRENT_PERIOD: self.keyword_library.get_keywords('current_period'),
            ColumnType.PREVIOUS_PERIOD: self.keyword_library.get_keywords('previous_period'),
            ColumnType.NOTE: self.keyword_library.get_keywords('note')
        }

        # 资产、负债、权益项目的匹配模式（保持不变）
        self.asset_patterns = {...}  # 与原来相同
        self.liability_patterns = {...}  # 与原来相同
        self.equity_patterns = {...}  # 与原来相同

    def parse_balance_sheet(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        解析合并资产负债表（优化版）

        Args:
            table_data: 表格数据

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        logger.info("开始解析合并资产负债表（使用增强版解析器）...")

        # 初始化结果结构
        result = {
            'report_type': '合并资产负债表',
            'assets': {
                'current_assets': {},
                'non_current_assets': {},
                'assets_total': {}
            },
            'liabilities': {
                'current_liabilities': {},
                'non_current_liabilities': {},
                'liabilities_total': {}
            },
            'equity': {},
            'liabilities_and_equity_total': {},
            'parsing_info': {
                'total_rows': len(table_data),
                'matched_items': 0,
                'unmatched_items': [],
                'column_changes': []  # 记录列结构变化
            },
            'ordered_items': []
        }

        if not table_data:
            logger.warning("表格数据为空")
            return result

        # 重置列分析器缓存（开始新的解析）
        self.column_analyzer.reset_cache()

        # 逐行解析数据
        current_column_map = None

        for row_idx, row in enumerate(table_data):
            if not row or len(row) == 0:
                continue

            # 关键改进1：每行动态分析列结构
            # 首先尝试使用缓存的列模式
            column_map = self.column_analyzer.analyze_row_structure(row, use_cache=True)

            # 如果列结构发生变化，记录下来
            if current_column_map != column_map:
                logger.info(f"第{row_idx}行检测到列结构变化: {column_map}")
                result['parsing_info']['column_changes'].append({
                    'row_index': row_idx,
                    'old_map': current_column_map,
                    'new_map': column_map
                })
                current_column_map = column_map

            # 如果列结构识别失败或置信度低，尝试使用LLM辅助
            if not column_map or len(column_map) < 2:
                logger.warning(f"第{row_idx}行列结构识别失败，尝试LLM辅助")
                llm_result = self.llm_assistant.analyze_header_with_llm(row)

                if llm_result['used_llm'] and llm_result['confidence'] > 0.7:
                    # 转换LLM结果为ColumnType格式
                    column_map = self._convert_llm_result(llm_result['column_map'])
                    logger.info(f"LLM辅助成功: {column_map}")

            # 关键改进2：使用列映射提取数值（无硬编码）
            values = self.column_analyzer.extract_values_from_row(row, column_map)

            # 获取项目名称
            item_name = values.get('item_name', '')
            if not item_name:
                continue

            # 后续的匹配和存储逻辑与原来相同
            matched = False

            # 匹配资产项目
            if not matched:
                matched, _ = self._match_and_store_item(
                    item_name, values, self.asset_patterns['current_assets'],
                    result['assets']['current_assets'], result, 'assets.current_assets'
                )

            if not matched:
                matched, _ = self._match_and_store_item(
                    item_name, values, self.asset_patterns['non_current_assets'],
                    result['assets']['non_current_assets'], result, 'assets.non_current_assets'
                )

            # 匹配负债项目
            if not matched:
                matched, _ = self._match_and_store_item(
                    item_name, values, self.liability_patterns['current_liabilities'],
                    result['liabilities']['current_liabilities'], result, 'liabilities.current_liabilities'
                )

            if not matched:
                matched, _ = self._match_and_store_item(
                    item_name, values, self.liability_patterns['non_current_liabilities'],
                    result['liabilities']['non_current_liabilities'], result, 'liabilities.non_current_liabilities'
                )

            # 匹配所有者权益项目
            if not matched:
                matched, _ = self._match_and_store_item(
                    item_name, values, self.equity_patterns,
                    result['equity'], result, 'equity'
                )

            # 匹配总计项目
            if not matched:
                matched = self._match_total_items(item_name, values, result)

            # 记录匹配结果
            if matched:
                result['parsing_info']['matched_items'] += 1
            else:
                result['parsing_info']['unmatched_items'].append({
                    'row_index': row_idx,
                    'item_name': item_name,
                    'values': values
                })

        logger.info(f"解析完成，匹配项目: {result['parsing_info']['matched_items']}, "
                   f"未匹配项目: {len(result['parsing_info']['unmatched_items'])}, "
                   f"列结构变化次数: {len(result['parsing_info']['column_changes'])}")

        return result

    def _convert_llm_result(self, llm_column_map: Dict[str, int]) -> Dict[ColumnType, int]:
        """
        将LLM返回的列映射转换为ColumnType格式

        Args:
            llm_column_map: LLM返回的列映射（字符串键）

        Returns:
            Dict[ColumnType, int]: ColumnType格式的列映射
        """
        type_mapping = {
            'item_name': ColumnType.ITEM_NAME,
            'current_period': ColumnType.CURRENT_PERIOD,
            'previous_period': ColumnType.PREVIOUS_PERIOD,
            'note': ColumnType.NOTE
        }

        converted = {}
        for key, value in llm_column_map.items():
            if key in type_mapping:
                converted[type_mapping[key]] = value

        return converted

    def _match_and_store_item(self, item_name: str, values: Dict[str, str],
                             patterns: Dict[str, List[str]], storage: Dict[str, Dict],
                             result: Dict, section_path: str):
        """
        匹配项目并存储数据（与原来相同）
        """
        # 实现与原balance_sheet.py中的_match_and_store_item_with_name相同
        pass

    def _match_total_items(self, item_name: str, values: Dict[str, str], result: Dict) -> bool:
        """
        匹配总计类项目（与原来相同）
        """
        # 实现与原balance_sheet.py中的_match_total_items相同
        pass


# 使用示例
def example_usage():
    """使用示例"""

    # 示例1：基本使用（不启用LLM）
    parser = EnhancedBalanceSheetParser(enable_llm=False)

    # 模拟表格数据（跨页，列数变化）
    table_data = [
        # 第126页：4列格式（项目、附注、期末、期初）
        ['项目', '附注', '2024年12月31日', '2023年12月31日'],
        ['流动资产：', '', '', ''],
        ['货币资金', '七、1', '1000000.00', '900000.00'],
        ['应收账款', '七、5', '500000.00', '450000.00'],

        # 第127页：继续4列格式
        ['固定资产', '七、21', '2000000.00', '1900000.00'],
        ['无形资产', '七、26', '100000.00', '95000.00'],

        # 第128页：变为3列格式（项目、期末、期初）- 附注列消失
        ['资产总计', '3900000.00', '3625000.00'],
        ['流动负债：', '', ''],
        ['短期借款', '200000.00', '180000.00'],
    ]

    result = parser.parse_balance_sheet(table_data)

    print(f"解析结果:")
    print(f"- 匹配项目数: {result['parsing_info']['matched_items']}")
    print(f"- 列结构变化次数: {len(result['parsing_info']['column_changes'])}")

    # 示例2：启用LLM辅助
    parser_with_llm = EnhancedBalanceSheetParser(
        enable_llm=True,
        keyword_library_path='config/keywords.json'
    )

    result_with_llm = parser_with_llm.parse_balance_sheet(table_data)

    print(f"\n使用LLM辅助的解析结果:")
    print(f"- 匹配项目数: {result_with_llm['parsing_info']['matched_items']}")


if __name__ == '__main__':
    example_usage()
