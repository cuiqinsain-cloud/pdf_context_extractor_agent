"""
列结构分析器
负责动态识别表格的列结构，支持跨页列数变化
"""
import re
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ColumnType(Enum):
    """列类型枚举"""
    ITEM_NAME = "item_name"  # 项目名称/科目
    CURRENT_PERIOD = "current_period"  # 期末/本期末
    PREVIOUS_PERIOD = "previous_period"  # 期初/上期末
    NOTE = "note"  # 附注
    UNKNOWN = "unknown"  # 未知


class ColumnAnalyzer:
    """列结构分析器"""

    def __init__(self):
        """初始化分析器"""
        # 列类型关键字库（可扩展）
        self.column_keywords = {
            ColumnType.ITEM_NAME: [
                r'项目', r'科目', r'会计科目', r'资产', r'负债', r'所有者权益'
            ],
            ColumnType.CURRENT_PERIOD: [
                r'期末', r'本期末', r'本年末', r'本期', r'2024\s*年.*期末',
                r'2024\s*年.*12\s*月.*31\s*日', r'当期', r'本年', r'年末余额', r'期末余额'
            ],
            ColumnType.PREVIOUS_PERIOD: [
                r'期初', r'上期末', r'上年末', r'上期', r'2023\s*年.*期末',
                r'2023\s*年.*12\s*月.*31\s*日', r'上年', r'年初余额', r'期初余额'
            ],
            ColumnType.NOTE: [
                r'附注', r'注释', r'注', r'备注'
            ]
        }

        # 列顺序模式缓存（用于跨行推断）
        self.column_pattern_cache = None

    def analyze_row_structure(self, row: List[str],
                             use_cache: bool = True) -> Dict[ColumnType, int]:
        """
        分析单行的列结构

        Args:
            row: 行数据
            use_cache: 是否使用缓存的列模式

        Returns:
            Dict[ColumnType, int]: 列类型到列索引的映射
        """
        if not row:
            return {}

        # 如果有缓存且允许使用，先尝试使用缓存
        if use_cache and self.column_pattern_cache:
            if self._validate_cached_pattern(row, self.column_pattern_cache):
                logger.debug(f"使用缓存的列模式: {self.column_pattern_cache}")
                return self.column_pattern_cache

        # 重新分析列结构
        column_map = self._analyze_columns(row)

        # 更新缓存
        if column_map:
            self.column_pattern_cache = column_map
            logger.info(f"更新列模式缓存: {column_map}")

        return column_map

    def _analyze_columns(self, row: List[str]) -> Dict[ColumnType, int]:
        """
        分析列结构的核心逻辑

        Args:
            row: 行数据

        Returns:
            Dict[ColumnType, int]: 列类型到列索引的映射
        """
        column_map = {}

        # 第一步：基于关键字匹配
        keyword_matches = self._match_by_keywords(row)

        # 第二步：基于内容特征推断
        feature_matches = self._infer_by_features(row, keyword_matches)

        # 第三步：合并结果
        column_map.update(keyword_matches)
        column_map.update(feature_matches)

        # 第四步：验证和修正
        column_map = self._validate_and_fix(row, column_map)

        return column_map

    def _match_by_keywords(self, row: List[str]) -> Dict[ColumnType, int]:
        """
        基于关键字匹配列类型

        Args:
            row: 行数据

        Returns:
            Dict[ColumnType, int]: 匹配到的列类型映射
        """
        matches = {}

        for col_idx, cell in enumerate(row):
            if not cell:
                continue

            cell_text = str(cell).strip()

            # 遍历所有列类型的关键字
            for col_type, keywords in self.column_keywords.items():
                # 如果该列类型已经被匹配，跳过
                if col_type in matches:
                    continue

                # 尝试匹配该列类型的关键字
                for keyword in keywords:
                    if re.search(keyword, cell_text):
                        matches[col_type] = col_idx
                        logger.debug(f"关键字匹配: 列{col_idx} -> {col_type.value} (关键字: {keyword})")
                        break  # 找到匹配后，跳出关键字循环，继续检查下一个列类型

        return matches

    def _infer_by_features(self, row: List[str],
                          keyword_matches: Dict[ColumnType, int]) -> Dict[ColumnType, int]:
        """
        基于内容特征推断列类型

        Args:
            row: 行数据
            keyword_matches: 已通过关键字匹配的列

        Returns:
            Dict[ColumnType, int]: 推断出的列类型映射
        """
        inferred = {}
        matched_indices = set(keyword_matches.values())

        # 分析每一列的特征
        for col_idx, cell in enumerate(row):
            if col_idx in matched_indices:
                continue  # 跳过已匹配的列

            if not cell:
                continue

            cell_text = str(cell).strip()

            # 特征1：附注格式（如"七、1"）
            if self._is_note_format(cell_text):
                if ColumnType.NOTE not in inferred:
                    inferred[ColumnType.NOTE] = col_idx
                    logger.debug(f"特征推断: 列{col_idx} -> NOTE (附注格式)")
                continue

            # 特征2：金额格式（数字）
            if self._is_numeric_format(cell_text):
                # 金额列可能是期末或期初
                # 根据位置推断：通常第一个金额列是期末，第二个是期初
                if ColumnType.CURRENT_PERIOD not in keyword_matches and \
                   ColumnType.CURRENT_PERIOD not in inferred:
                    inferred[ColumnType.CURRENT_PERIOD] = col_idx
                    logger.debug(f"特征推断: 列{col_idx} -> CURRENT_PERIOD (第一个金额列)")
                elif ColumnType.PREVIOUS_PERIOD not in keyword_matches and \
                     ColumnType.PREVIOUS_PERIOD not in inferred:
                    inferred[ColumnType.PREVIOUS_PERIOD] = col_idx
                    logger.debug(f"特征推断: 列{col_idx} -> PREVIOUS_PERIOD (第二个金额列)")
                continue

        # 特征3：第一列通常是项目名称
        if ColumnType.ITEM_NAME not in keyword_matches and \
           ColumnType.ITEM_NAME not in inferred:
            if len(row) > 0 and row[0]:
                inferred[ColumnType.ITEM_NAME] = 0
                logger.debug(f"特征推断: 列0 -> ITEM_NAME (默认第一列)")

        return inferred

    def _is_note_format(self, text: str) -> bool:
        """
        判断是否为附注格式

        Args:
            text: 单元格文本

        Returns:
            bool: 是否为附注格式
        """
        # 匹配"七、1"、"六、2"等格式
        if re.search(r'[一二三四五六七八九十]+、\d+', text):
            return True

        # 匹配纯数字（如"1"、"2"）
        if re.match(r'^\d+$', text) and len(text) <= 3:
            return True

        return False

    def _is_numeric_format(self, text: str) -> bool:
        """
        判断是否为金额格式

        Args:
            text: 单元格文本

        Returns:
            bool: 是否为金额格式
        """
        # 匹配金额格式：
        # 1. 带千分位：1,234,567.89
        # 2. 不带千分位：1234567.89
        # 3. 支持负数
        if re.match(r'^\s*-?(\d{1,3}(,\d{3})*|\d+)(\.\d+)?\s*$', text):
            return True

        return False

    def _validate_and_fix(self, row: List[str],
                         column_map: Dict[ColumnType, int]) -> Dict[ColumnType, int]:
        """
        验证和修正列映射

        Args:
            row: 行数据
            column_map: 列类型映射

        Returns:
            Dict[ColumnType, int]: 修正后的列映射
        """
        # 验证1：期末列必须在期初列之前
        if ColumnType.CURRENT_PERIOD in column_map and \
           ColumnType.PREVIOUS_PERIOD in column_map:
            current_idx = column_map[ColumnType.CURRENT_PERIOD]
            previous_idx = column_map[ColumnType.PREVIOUS_PERIOD]

            if current_idx > previous_idx:
                # 顺序错误，交换
                logger.warning(f"列顺序错误，交换期末列和期初列")
                column_map[ColumnType.CURRENT_PERIOD] = previous_idx
                column_map[ColumnType.PREVIOUS_PERIOD] = current_idx

        # 验证2：项目名称列必须是第一列
        if ColumnType.ITEM_NAME in column_map:
            if column_map[ColumnType.ITEM_NAME] != 0:
                logger.warning(f"项目名称列不是第一列: {column_map[ColumnType.ITEM_NAME]}")

        return column_map

    def _validate_cached_pattern(self, row: List[str],
                                 cached_pattern: Dict[ColumnType, int]) -> bool:
        """
        验证缓存的列模式是否适用于当前行

        Args:
            row: 当前行数据
            cached_pattern: 缓存的列模式

        Returns:
            bool: 是否可以使用缓存
        """
        # 检查1：列数是否匹配
        max_col_idx = max(cached_pattern.values()) if cached_pattern else -1
        if max_col_idx >= len(row):
            logger.debug(f"缓存失效: 列数不匹配 (需要{max_col_idx+1}列，实际{len(row)}列)")
            return False

        # 检查2：关键列的内容特征是否匹配
        for col_type, col_idx in cached_pattern.items():
            if col_idx >= len(row):
                continue

            cell = row[col_idx]
            if not cell:
                continue

            cell_text = str(cell).strip()

            # 验证金额列
            if col_type in [ColumnType.CURRENT_PERIOD, ColumnType.PREVIOUS_PERIOD]:
                if not self._is_numeric_format(cell_text) and cell_text:
                    # 如果不是金额格式且不为空，缓存可能失效
                    logger.debug(f"缓存失效: 列{col_idx}应为金额列，但内容为'{cell_text}'")
                    return False

            # 验证附注列
            if col_type == ColumnType.NOTE:
                if not self._is_note_format(cell_text) and cell_text:
                    logger.debug(f"缓存失效: 列{col_idx}应为附注列，但内容为'{cell_text}'")
                    return False

        return True

    def extract_values_from_row(self, row: List[str],
                               column_map: Dict[ColumnType, int]) -> Dict[str, Any]:
        """
        根据列映射从行中提取数值
        支持智能列偏移检测，处理合并单元格导致的列偏移问题

        Args:
            row: 行数据
            column_map: 列类型映射

        Returns:
            Dict[str, Any]: 提取的数值
        """
        values = {}

        # 提取项目名称
        if ColumnType.ITEM_NAME in column_map:
            idx = column_map[ColumnType.ITEM_NAME]
            value = self._extract_with_offset(row, idx, None)
            if value:
                values['item_name'] = str(value).strip()

        # 提取期末数据
        if ColumnType.CURRENT_PERIOD in column_map:
            idx = column_map[ColumnType.CURRENT_PERIOD]
            value = self._extract_with_offset(row, idx, 'numeric')
            if value:
                values['current_period'] = self._clean_numeric_value(value)

        # 提取期初数据
        if ColumnType.PREVIOUS_PERIOD in column_map:
            idx = column_map[ColumnType.PREVIOUS_PERIOD]
            value = self._extract_with_offset(row, idx, 'numeric')
            if value:
                values['previous_period'] = self._clean_numeric_value(value)

        # 提取附注
        if ColumnType.NOTE in column_map:
            idx = column_map[ColumnType.NOTE]
            value = self._extract_with_offset(row, idx, 'note')
            if value:
                note_value = str(value).strip()
                if self._is_note_format(note_value):
                    values['note'] = note_value

        return values

    def _extract_with_offset(self, row: List[str], base_idx: int,
                            value_type: Optional[str] = None) -> Optional[str]:
        """
        从行中提取值，支持列偏移检测

        当目标列为空或None时，尝试检查相邻列（处理合并单元格导致的列偏移）

        Args:
            row: 行数据
            base_idx: 基准列索引
            value_type: 期望的值类型 ('numeric', 'note', None)

        Returns:
            Optional[str]: 提取的值
        """
        # 定义搜索偏移量：先尝试原位置，然后尝试-1, +1, -2, +2, -3, +3
        offsets = [0, -1, 1, -2, 2, -3, 3]

        for offset in offsets:
            idx = base_idx + offset

            # 检查索引是否有效
            if idx < 0 or idx >= len(row):
                continue

            cell = row[idx]

            # 跳过None和空字符串
            if cell is None or (isinstance(cell, str) and not cell.strip()):
                continue

            cell_text = str(cell).strip()

            # 如果没有指定类型，返回第一个非空值
            if value_type is None:
                if offset != 0:
                    logger.debug(f"列偏移检测: 在列{idx}找到值(偏移{offset}): '{cell_text[:30]}'")
                return cell

            # 验证值类型
            if value_type == 'numeric':
                if self._is_numeric_format(cell_text):
                    if offset != 0:
                        logger.debug(f"列偏移检测: 在列{idx}找到数值(偏移{offset}): '{cell_text}'")
                    return cell
            elif value_type == 'note':
                if self._is_note_format(cell_text):
                    if offset != 0:
                        logger.debug(f"列偏移检测: 在列{idx}找到附注(偏移{offset}): '{cell_text}'")
                    return cell

        return None

    def _clean_numeric_value(self, value: str) -> Optional[str]:
        """
        清理数值数据

        Args:
            value: 原始数值字符串

        Returns:
            Optional[str]: 清理后的数值字符串
        """
        if not value:
            return None

        # 移除常见的非数字字符，保留数字、小数点、逗号、负号
        cleaned = re.sub(r'[^\d.,\-]', '', str(value))

        # 移除千分位逗号
        cleaned = cleaned.replace(',', '')

        # 空值处理
        if not cleaned or cleaned in ['-', '--', '—']:
            return None

        return cleaned

    def reset_cache(self):
        """重置列模式缓存"""
        self.column_pattern_cache = None
        logger.info("列模式缓存已重置")
