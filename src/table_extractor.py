"""
表格提取模块
负责从PDF页面中提取和预处理表格数据
"""
import re
from typing import List, Dict, Optional, Tuple, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class TableExtractor:
    """表格数据提取器"""

    def __init__(self):
        """初始化表格提取器"""
        self.balance_sheet_end_patterns = [
            r"负债和所有者权益总计",
            r"负债和所有者权益（或股东权益）总计",
            r"负债和股东权益总计"
        ]

        self.balance_sheet_start_patterns = [
            r"合并资产负债表",
            r"资产负债表"
        ]

        self.next_table_patterns = [
            r"母公司资产负债表",
            r"母公司合并资产负债表"
        ]

    def extract_tables_from_pages(self, pages: List) -> List[Dict]:
        """
        从多个页面中提取表格数据

        Args:
            pages (List): PDF页面对象列表

        Returns:
            List[Dict]: 提取的表格数据，包含页码和表格内容
        """
        all_tables = []

        for i, page in enumerate(pages):
            page_num = i + 126  # 假设从第126页开始
            logger.info(f"正在提取第 {page_num} 页的表格...")

            # 提取页面表格
            tables = page.extract_tables()
            if tables:
                for j, table in enumerate(tables):
                    all_tables.append({
                        'page': page_num,
                        'table_index': j,
                        'data': table,
                        'raw_text': page.extract_text()
                    })
                logger.info(f"第 {page_num} 页提取到 {len(tables)} 个表格")
            else:
                logger.warning(f"第 {page_num} 页未检测到表格")

        return all_tables

    def identify_balance_sheet_content(self, pages: List) -> Dict:
        """
        识别合并资产负债表的具体内容范围

        Args:
            pages (List): PDF页面对象列表

        Returns:
            Dict: 包含起始位置、结束位置和内容的字典
        """
        result = {
            'start_page': None,
            'end_page': None,
            'start_position': None,
            'end_position': None,
            'content': []
        }

        # 遍历所有页面查找边界
        for i, page in enumerate(pages):
            page_num = i + 126
            page_text = page.extract_text() or ""

            # 查找开始标志
            if result['start_page'] is None:
                for pattern in self.balance_sheet_start_patterns:
                    if re.search(pattern, page_text):
                        result['start_page'] = page_num
                        result['start_position'] = self._find_text_position(page, pattern)
                        logger.info(f"找到合并资产负债表开始位置: 第{page_num}页")
                        break

            # 查找结束标志
            for pattern in self.balance_sheet_end_patterns:
                match = re.search(pattern, page_text)
                if match:
                    result['end_page'] = page_num
                    result['end_position'] = self._find_text_position(page, pattern)
                    logger.info(f"找到合并资产负债表结束位置: 第{page_num}页, 标志: {match.group()}")
                    break

            # 检查是否遇到下一个表格
            for pattern in self.next_table_patterns:
                if re.search(pattern, page_text):
                    if result['end_page'] is None:
                        result['end_page'] = page_num
                        logger.info(f"在第{page_num}页找到母公司资产负债表，确定边界")
                    break

        return result

    def extract_balance_sheet_tables(self, pages: List) -> List[List[List[str]]]:
        """
        提取合并资产负债表的表格数据

        Args:
            pages (List): PDF页面对象列表

        Returns:
            List[List[List[str]]]: 合并后的表格数据
        """
        # 首先识别内容边界
        boundary_info = self.identify_balance_sheet_content(pages)

        if boundary_info['start_page'] is None:
            logger.error("未找到合并资产负债表开始位置")
            return []

        # 提取表格数据
        balance_sheet_tables = []

        for i, page in enumerate(pages):
            page_num = i + 126

            # 跳过边界之外的页面
            if boundary_info['start_page'] and page_num < boundary_info['start_page']:
                continue
            if boundary_info['end_page'] and page_num > boundary_info['end_page']:
                break

            # 提取页面表格
            tables = page.extract_tables()
            if tables:
                if page_num == boundary_info['end_page']:
                    # 最后一页需要特殊处理，只取结束位置之前的表格
                    filtered_tables = self._filter_tables_by_boundary(
                        tables, page, boundary_info['end_position'], is_end=True
                    )
                    balance_sheet_tables.extend(filtered_tables)
                else:
                    balance_sheet_tables.extend(tables)

                logger.info(f"第 {page_num} 页提取表格 {len(tables)} 个")

        return balance_sheet_tables

    def _find_text_position(self, page, pattern: str) -> Optional[Dict]:
        """
        查找文本在页面中的位置坐标

        Args:
            page: PDF页面对象
            pattern (str): 要查找的正则表达式

        Returns:
            Optional[Dict]: 位置信息字典
        """
        try:
            # 获取页面中的所有文字对象
            chars = page.chars
            page_text = page.extract_text() or ""

            match = re.search(pattern, page_text)
            if not match:
                return None

            # 简化的位置估算，实际项目中可能需要更精确的定位
            return {
                'pattern': pattern,
                'match_text': match.group(),
                'start_char': match.start(),
                'end_char': match.end()
            }

        except Exception as e:
            logger.warning(f"查找文本位置时出错: {e}")
            return None

    def _filter_tables_by_boundary(self, tables: List[List[List[str]]],
                                 page, boundary_position: Dict,
                                 is_end: bool = True) -> List[List[List[str]]]:
        """
        根据边界位置过滤表格

        Args:
            tables: 页面表格列表
            page: PDF页面对象
            boundary_position: 边界位置信息
            is_end: 是否为结束边界

        Returns:
            List[List[List[str]]]: 过滤后的表格
        """
        if not boundary_position:
            return tables

        filtered_tables = []

        for table in tables:
            # 检查表格是否包含结束标志
            table_text = ' '.join([' '.join([str(cell) if cell is not None else '' for cell in row]) for row in table if row])

            # 如果表格包含合并资产负债表的结束标志，则包含此表格
            contains_balance_sheet_end = False
            for pattern in self.balance_sheet_end_patterns:
                if re.search(pattern, table_text):
                    contains_balance_sheet_end = True
                    break

            # 如果表格包含下一个表格（母公司资产负债表）的开始标志，则排除此表格
            contains_next_table_start = False
            for pattern in self.next_table_patterns:
                if re.search(pattern, table_text):
                    contains_next_table_start = True
                    break

            # 决策逻辑：
            # 1. 如果包含合并资产负债表结束标志，包含这个表格
            # 2. 如果包含母公司资产负债表开始标志，排除这个表格
            # 3. 如果都不包含，则需要检查表格内容的位置
            if contains_next_table_start:
                # 如果表格同时包含结束标志和开始标志，需要拆分表格
                if contains_balance_sheet_end:
                    # 找到结束标志的位置，只保留结束标志之前的内容
                    filtered_table = []
                    for row in table:
                        row_text = ' '.join([str(cell) if cell is not None else '' for cell in row]) if row else ''

                        # 检查是否遇到母公司资产负债表标志
                        found_next_table = False
                        for pattern in self.next_table_patterns:
                            if re.search(pattern, row_text):
                                found_next_table = True
                                break

                        if found_next_table:
                            break

                        filtered_table.append(row)

                        # 检查是否遇到合并资产负债表结束标志
                        found_end = False
                        for pattern in self.balance_sheet_end_patterns:
                            if re.search(pattern, row_text):
                                found_end = True
                                break

                        if found_end:
                            break

                    if filtered_table:
                        filtered_tables.append(filtered_table)
                # 如果只包含开始标志，不包含结束标志，则完全排除
            else:
                # 不包含母公司表格标志，包含此表格
                filtered_tables.append(table)

        return filtered_tables

    def merge_cross_page_tables(self, tables: List[List[List[str]]]) -> List[List[str]]:
        """
        合并跨页面的表格数据

        Args:
            tables (List[List[List[str]]]): 多个表格的数据

        Returns:
            List[List[str]]: 合并后的单个表格
        """
        if not tables:
            return []

        # 简单的表格合并逻辑
        merged_table = []

        for table in tables:
            if table:  # 确保表格不为空
                if not merged_table:
                    # 第一个表格，直接添加
                    merged_table.extend(table)
                else:
                    # 后续表格，跳过表头（如果有重复）
                    start_row = 0

                    # 检查是否有重复的表头
                    if len(table) > 0 and len(merged_table) > 0:
                        # 更精确的表头检测：真正的表头应该包含列名关键词
                        first_row_text = ' '.join([str(cell) if cell is not None else '' for cell in table[0]]) if table[0] else ''
                        # 只有当第一行包含明确的列名关键词时，才认为是表头
                        # 注意：不能只检查"资产"或"负债"，因为数据行也可能包含这些词
                        is_header = (
                            ('项目' in first_row_text and '附注' in first_row_text) or  # 包含"项目"和"附注"
                            ('本期末' in first_row_text and '上期末' in first_row_text) or  # 包含"本期末"和"上期末"
                            ('2024年' in first_row_text and '2023年' in first_row_text)  # 包含年份
                        )
                        if is_header:
                            start_row = 1  # 跳过表头

                    # 添加表格数据
                    merged_table.extend(table[start_row:])

        logger.info(f"合并后的表格行数: {len(merged_table)}")
        return merged_table

    def clean_table_data(self, table: List[List[str]]) -> List[List[str]]:
        """
        清洗表格数据

        Args:
            table (List[List[str]]): 原始表格数据

        Returns:
            List[List[str]]: 清洗后的表格数据
        """
        cleaned_table = []

        for row in table:
            if not row:  # 跳过空行
                continue

            # 清洗每个单元格
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_cell = ""
                else:
                    # 去除多余空白和特殊字符
                    cleaned_cell = str(cell).strip()
                    # 可以添加更多清洗规则
                    cleaned_cell = re.sub(r'\s+', ' ', cleaned_cell)

                cleaned_row.append(cleaned_cell)

            # 只保留非空行
            if any(cell.strip() for cell in cleaned_row):
                cleaned_table.append(cleaned_row)

        logger.info(f"数据清洗完成，保留 {len(cleaned_table)} 行数据")
        return cleaned_table


def test_table_extractor():
    """测试表格提取器"""
    # 这里添加测试代码
    pass


if __name__ == "__main__":
    test_table_extractor()