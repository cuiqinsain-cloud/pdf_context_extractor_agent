"""
结果对比器
对比规则匹配和 LLM 识别的结果
"""
import logging
from typing import Dict, Any, List
from src.parsers.column_analyzer import ColumnType

logger = logging.getLogger(__name__)


class ResultComparator:
    """结果对比器"""

    def __init__(self):
        """初始化对比器"""
        pass

    def compare(self,
                rule_result: Dict[ColumnType, int],
                llm_result: Dict[str, int],
                header_row: List[str]) -> Dict[str, Any]:
        """
        对比两个结果

        Args:
            rule_result: 规则匹配结果 {ColumnType: 列索引}
            llm_result: LLM识别结果 {'column_type': 列索引}
            header_row: 表头行数据

        Returns:
            Dict[str, Any]: 对比结果
                {
                    'is_match': bool,  # 是否严格一致
                    'differences': List[Dict],  # 差异列表
                    'rule_result': Dict,  # 规则结果（字符串键）
                    'llm_result': Dict,  # LLM结果
                    'summary': str  # 摘要
                }
        """
        # 转换 rule_result 的键为字符串，便于对比
        rule_result_str = {
            col_type.value: col_idx
            for col_type, col_idx in rule_result.items()
        }

        # 检查是否严格一致
        is_match = (rule_result_str == llm_result)

        # 计算差异
        differences = []
        if not is_match:
            differences = self._calculate_differences(
                rule_result_str, llm_result, header_row
            )

        # 生成摘要
        summary = self._generate_summary(
            is_match, differences, rule_result_str, llm_result
        )

        result = {
            'is_match': is_match,
            'differences': differences,
            'rule_result': rule_result_str,
            'llm_result': llm_result,
            'summary': summary,
            'header_row': header_row
        }

        if is_match:
            logger.info("✓ 规则匹配和LLM识别结果严格一致，自动进入下一步")
        else:
            logger.warning(f"✗ 规则匹配和LLM识别结果不一致，发现 {len(differences)} 处差异，需要人为决策")
            for diff in differences:
                logger.warning(f"  - {diff['description']}")

        return result

    def _calculate_differences(self,
                              rule_result: Dict[str, int],
                              llm_result: Dict[str, int],
                              header_row: List[str]) -> List[Dict[str, Any]]:
        """
        计算差异

        Args:
            rule_result: 规则匹配结果
            llm_result: LLM识别结果
            header_row: 表头行数据

        Returns:
            List[Dict[str, Any]]: 差异列表
        """
        differences = []

        # 获取所有列类型
        all_column_types = set(rule_result.keys()) | set(llm_result.keys())

        for col_type in all_column_types:
            rule_idx = rule_result.get(col_type)
            llm_idx = llm_result.get(col_type)

            if rule_idx != llm_idx:
                # 获取单元格内容
                rule_cell = header_row[rule_idx] if rule_idx is not None and rule_idx < len(header_row) else None
                llm_cell = header_row[llm_idx] if llm_idx is not None and llm_idx < len(header_row) else None

                diff = {
                    'column_type': col_type,
                    'rule_index': rule_idx,
                    'llm_index': llm_idx,
                    'rule_cell': rule_cell,
                    'llm_cell': llm_cell,
                    'description': self._describe_difference(
                        col_type, rule_idx, llm_idx, rule_cell, llm_cell
                    )
                }
                differences.append(diff)

        return differences

    def _describe_difference(self, col_type: str,
                           rule_idx: int, llm_idx: int,
                           rule_cell: str, llm_cell: str) -> str:
        """
        描述差异

        Args:
            col_type: 列类型
            rule_idx: 规则匹配的列索引
            llm_idx: LLM识别的列索引
            rule_cell: 规则匹配的单元格内容
            llm_cell: LLM识别的单元格内容

        Returns:
            str: 差异描述
        """
        if rule_idx is None and llm_idx is not None:
            return f"{col_type}: 规则未识别，LLM识别为列{llm_idx}('{llm_cell}')"
        elif rule_idx is not None and llm_idx is None:
            return f"{col_type}: 规则识别为列{rule_idx}('{rule_cell}')，LLM未识别"
        else:
            return (f"{col_type}: 规则识别为列{rule_idx}('{rule_cell}')，"
                   f"LLM识别为列{llm_idx}('{llm_cell}')")

    def _generate_summary(self, is_match: bool,
                         differences: List[Dict[str, Any]],
                         rule_result: Dict[str, int],
                         llm_result: Dict[str, int]) -> str:
        """
        生成摘要

        Args:
            is_match: 是否匹配
            differences: 差异列表
            rule_result: 规则匹配结果
            llm_result: LLM识别结果

        Returns:
            str: 摘要
        """
        if is_match:
            return f"结果严格一致：规则和LLM都识别出 {len(rule_result)} 列"
        else:
            rule_count = len(rule_result)
            llm_count = len(llm_result)
            diff_count = len(differences)

            summary = f"结果不一致：规则识别 {rule_count} 列，LLM识别 {llm_count} 列，"
            summary += f"发现 {diff_count} 处差异"

            return summary
