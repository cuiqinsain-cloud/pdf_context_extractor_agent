"""
集成结构识别器的示例 - 资产负债表解析器

展示如何将 StatementStructureIdentifier 集成到现有解析器中
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from .base_statement_parser import BaseStatementParser

logger = logging.getLogger(__name__)


class BalanceSheetParserV2(BaseStatementParser):
    """合并资产负债表解析器 V2 - 集成结构识别器"""

    def __init__(self):
        """初始化解析器"""
        super().__init__('balance_sheet')

        # 资产项目关键词映射（保持原有的patterns）
        self.asset_patterns = {
            'current_assets': {
                '货币资金': [r'货币资金'],
                '交易性金融资产': [r'交易性金融资产'],
                # ... 其他项目
            },
            'non_current_assets': {
                '债权投资': [r'债权投资'],
                # ... 其他项目
            }
        }

        # 负债项目关键词映射
        self.liability_patterns = {
            'current_liabilities': {
                '短期借款': [r'短期借款'],
                # ... 其他项目
            },
            'non_current_liabilities': {
                '长期借款': [r'长期借款'],
                # ... 其他项目
            }
        }

        # 所有者权益项目关键词映射
        self.equity_patterns = {
            '实收资本': [r'实收资本', r'股本'],
            # ... 其他项目
        }

    def parse_balance_sheet(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        解析合并资产负债表

        Args:
            table_data: 表格数据

        Returns:
            Dict: 解析后的结构化数据
        """
        logger.info("开始解析合并资产负债表...")

        # 重置缓存
        self.reset_cache()

        # 初始化结果结构
        result = {
            'report_type': '合并资产负债表',
            'assets': {
                'current_assets': {},
                'current_assets_total': {},
                'non_current_assets': {},
                'non_current_assets_total': {},
                'assets_total': {}
            },
            'liabilities': {
                'current_liabilities': {},
                'current_liabilities_total': {},
                'non_current_liabilities': {},
                'non_current_liabilities_total': {},
                'liabilities_total': {}
            },
            'equity': {
                'items': {},
                'parent_equity_total': {},
                'equity_total': {}
            },
            'liabilities_and_equity_total': {},
            'parsing_info': {
                'total_rows': len(table_data),
                'matched_items': 0,
                'unmatched_items': []
            },
            'ordered_items': [],
            'structure_info': {}  # 新增：结构识别信息
        }

        if not table_data:
            logger.warning("表格数据为空")
            return result

        # ========== 新增：使用结构识别器 ==========
        logger.info("步骤1: 识别报表结构...")
        structure_result = self.identify_statement_structure(table_data)

        # 保存结构识别信息
        result['structure_info'] = {
            'is_valid': structure_result['is_valid'],
            'confidence': structure_result['confidence'],
            'key_positions': structure_result['key_positions'],
            'header_row': structure_result['header_row'],
            'data_range': (structure_result['start_row'], structure_result['end_row'])
        }

        if not structure_result['is_valid']:
            logger.warning(f"结构识别失败，置信度: {structure_result['confidence']:.2%}")
            logger.warning(f"缺失的关键结构: {structure_result['missing_keys']}")
            # 继续使用原有逻辑处理
        else:
            logger.info(f"结构识别成功，置信度: {structure_result['confidence']:.2%}")
            logger.info(f"数据范围: 第{structure_result['start_row']}行 到 第{structure_result['end_row']}行")

        # ========== 新增：提取有效数据范围 ==========
        logger.info("步骤2: 提取有效数据范围...")
        if structure_result['is_valid']:
            # 只处理识别到的数据范围
            data_to_parse = self.extract_statement_data(table_data, structure_result)
            # 调整行索引偏移量
            row_offset = structure_result['start_row']
        else:
            # 使用全部数据
            data_to_parse = table_data
            row_offset = 0

        # ========== 新增：获取表头信息 ==========
        logger.info("步骤3: 分析表头结构...")
        header_info = self.get_header_info(table_data, structure_result)

        # ========== 逐行解析数据（保持原有逻辑）==========
        logger.info("步骤4: 逐行解析数据...")
        for row_idx, row in enumerate(data_to_parse):
            if not row or len(row) == 0:
                continue

            # 使用新的方法获取项目名称（支持深信服等特殊格式）
            item_name = self.get_item_name_from_row(row, header_info)

            if not item_name:
                continue

            # 使用基类的方法提取数值
            values = self.extract_values_from_row(row, header_info)

            # 分类匹配项目（保持原有逻辑）
            matched = False

            # 匹配资产项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.asset_patterns['current_assets'],
                    result['assets']['current_assets'], result, 'assets.current_assets'
                )

            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.asset_patterns['non_current_assets'],
                    result['assets']['non_current_assets'], result, 'assets.non_current_assets'
                )

            # 匹配负债项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.liability_patterns['current_liabilities'],
                    result['liabilities']['current_liabilities'], result, 'liabilities.current_liabilities'
                )

            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.liability_patterns['non_current_liabilities'],
                    result['liabilities']['non_current_liabilities'], result, 'liabilities.non_current_liabilities'
                )

            # 匹配所有者权益项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.equity_patterns,
                    result['equity']['items'], result, 'equity.items'
                )

            # 匹配总计项目
            if not matched:
                matched = self._match_total_items(item_name, values, result)

            # 记录匹配结果
            if matched:
                result['parsing_info']['matched_items'] += 1
            else:
                result['parsing_info']['unmatched_items'].append({
                    'row_index': row_idx + row_offset,
                    'item_name': item_name,
                    'values': values
                })

        logger.info(f"解析完成，匹配项目: {result['parsing_info']['matched_items']}, "
                   f"未匹配项目: {len(result['parsing_info']['unmatched_items'])}")

        return result

    def _match_and_store_item_with_name(self, item_name: str, values: Dict[str, str],
                            patterns: Dict[str, List[str]], storage: Dict[str, Dict],
                            result: Dict, section_path: str) -> Tuple[bool, Optional[str]]:
        """
        匹配项目并存储数据（保持原有逻辑）
        """
        for standard_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, item_name):
                    if standard_name in storage:
                        return True, standard_name

                    item_data = {
                        'original_name': item_name,
                        **values
                    }
                    storage[standard_name] = item_data

                    result['ordered_items'].append({
                        'section': section_path,
                        'standard_name': standard_name,
                        'data': item_data
                    })

                    return True, standard_name
        return False, None

    def _match_total_items(self, item_name: str, values: Dict[str, str], result: Dict) -> bool:
        """
        匹配总计类项目（保持原有逻辑）
        """
        item_data = {
            'original_name': item_name,
            **values
        }

        # 流动资产合计
        if re.search(r'^流动资产合计$', item_name):
            result['assets']['current_assets_total'] = item_data
            result['ordered_items'].append({
                'section': 'assets.current_assets_total',
                'standard_name': 'current_assets_total',
                'data': item_data
            })
            return True

        # ... 其他总计项目的匹配逻辑

        return False


# ========== 集成说明 ==========
"""
集成步骤：

1. 继承 BaseStatementParser 基类
   - 自动获得结构识别能力
   - 自动获得统一的表头识别和数据提取方法

2. 在 parse_balance_sheet 方法中：
   - 步骤1: 调用 identify_statement_structure() 识别结构
   - 步骤2: 调用 extract_statement_data() 提取有效数据范围
   - 步骤3: 调用 get_header_info() 获取表头信息
   - 步骤4: 使用 get_item_name_from_row() 和 extract_values_from_row() 解析数据

3. 保持原有的项目匹配逻辑不变
   - _match_and_store_item_with_name()
   - _match_total_items()
   - validate_balance_sheet()

4. 新增结构识别信息到结果中
   - structure_info 字段包含识别结果

优势：
- ✅ 自动识别报表范围，避免处理无关数据
- ✅ 自动处理深信服等特殊格式（项目名称在第1列）
- ✅ 统一的表头识别逻辑
- ✅ 保持原有的项目匹配和验证逻辑
- ✅ 向后兼容：如果结构识别失败，仍使用原有逻辑
"""
