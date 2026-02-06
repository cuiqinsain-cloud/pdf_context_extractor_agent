"""
财务报表结构识别器
基于关键结构顺序识别报表类型、范围和表头位置
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class StatementStructureIdentifier:
    """财务报表结构识别器"""

    def __init__(self, statement_type: str):
        """
        初始化结构识别器

        Args:
            statement_type: 报表类型 ('balance_sheet', 'income_statement', 'cash_flow')
        """
        self.statement_type = statement_type
        self.key_structures = self._get_key_structures()
        self.end_patterns = self._get_end_patterns()

    def _get_key_structures(self) -> List[Dict[str, Any]]:
        """
        获取关键结构模式

        Returns:
            List[Dict]: 关键结构列表，每个结构包含name和patterns
        """
        if self.statement_type == 'balance_sheet':
            return [
                {'name': '流动资产', 'patterns': [r'^流动资产：?$'], 'required': True},
                {'name': '非流动资产', 'patterns': [r'^非流动资产：?$'], 'required': True},
                {'name': '流动负债', 'patterns': [r'^流动负债：?$'], 'required': True},
                {'name': '非流动负债', 'patterns': [r'^非流动负债：?$'], 'required': True},
                {'name': '所有者权益', 'patterns': [r'^所有者权益.*：?$', r'^股东权益.*：?$'], 'required': True}
            ]

        elif self.statement_type == 'income_statement':
            return [
                {'name': '营业总收入', 'patterns': [r'^一、营业总收入$', r'^营业总收入$'], 'required': True},
                {'name': '营业总成本', 'patterns': [r'^二、营业总成本$', r'^营业总成本$'], 'required': True},
                {'name': '营业利润', 'patterns': [r'^三、营业利润', r'^二、营业利润', r'^营业利润'], 'required': True},
                {'name': '利润总额', 'patterns': [r'^四、利润总额', r'^三、利润总额', r'^利润总额'], 'required': True},
                {'name': '净利润', 'patterns': [r'^五、净利润', r'^四、净利润', r'^净利润(?!（)'], 'required': True},
                {'name': '其他综合收益', 'patterns': [r'^六、其他综合收益的税后净额', r'^其他综合收益.*税后净额'], 'required': False},
                {'name': '综合收益总额', 'patterns': [r'^七、综合收益总额', r'^八、综合收益总额', r'^综合收益总额'], 'required': False},
                {'name': '每股收益', 'patterns': [r'^八、每股收益', r'^九、每股收益'], 'required': False}
            ]

        elif self.statement_type == 'cash_flow':
            return [
                {'name': '经营活动', 'patterns': [r'^一、经营活动产生的现金流\s*量：?$'], 'required': True},
                {'name': '经营活动流入小计', 'patterns': [r'^经营活动现金流入小计$'], 'required': True},
                {'name': '经营活动流出小计', 'patterns': [r'^经营活动现金流出小计$'], 'required': True},
                {'name': '经营活动净额', 'patterns': [r'^经营活动产生的现金流\s*量净\s*额$', r'^经营活动产生的现金流量净额$'], 'required': True},
                {'name': '投资活动', 'patterns': [r'^二、投资活动产生的现金流\s*量：?$'], 'required': True},
                {'name': '投资活动流入小计', 'patterns': [r'^投资活动现金流入小计$'], 'required': True},
                {'name': '投资活动流出小计', 'patterns': [r'^投资活动现金流出小计$'], 'required': True},
                {'name': '投资活动净额', 'patterns': [r'^投资活动产生的现金流\s*量净\s*额$', r'^投资活动产生的现金流量净额$'], 'required': True},
                {'name': '筹资活动', 'patterns': [r'^三、筹资活动产生的现金流\s*量：?$'], 'required': True},
                {'name': '筹资活动流入小计', 'patterns': [r'^筹资活动现金流入小计$'], 'required': True},
                {'name': '筹资活动流出小计', 'patterns': [r'^筹资活动现金流出小计$'], 'required': True},
                {'name': '筹资活动净额', 'patterns': [r'^筹资活动产生的现金流\s*量净\s*额$', r'^筹资活动产生的现金流量净额$'], 'required': True},
                {'name': '汇率影响', 'patterns': [r'^四、汇率变动对现金及现金等\s*价物的\s*影响$'], 'required': False},
                {'name': '现金净增加额', 'patterns': [r'^五、现金及现金等价物净增加\s*额$'], 'required': False},
                {'name': '期末余额', 'patterns': [r'^六、期末现金及现金等价物余\s*额$'], 'required': True}
            ]

        else:
            raise ValueError(f"不支持的报表类型: {self.statement_type}")

    def _get_end_patterns(self) -> List[str]:
        """
        获取结束标识模式

        Returns:
            List[str]: 结束标识的正则表达式列表
        """
        if self.statement_type == 'balance_sheet':
            return [
                r'^负债和所有者权益总计$',
                r'^负债和所有者权益.*总计$',
                r'^负债和股东权益.*总计$'
            ]

        elif self.statement_type == 'income_statement':
            return [
                r'^.*稀释每股收益.*$'  # 稀释每股收益是最后一行
            ]

        elif self.statement_type == 'cash_flow':
            return [
                r'^六、期末现金及现金等价物余\s*额$'
            ]

        else:
            return []

    def identify_structure(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        识别报表结构

        Args:
            table_data: 表格数据

        Returns:
            Dict: 识别结果
                {
                    'is_valid': bool,  # 是否识别到完整结构
                    'key_positions': {key_name: row_idx},  # 关键结构的位置
                    'header_row': int,  # 表头行索引
                    'start_row': int,  # 数据开始行索引
                    'end_row': int,  # 数据结束行索引
                    'confidence': float,  # 置信度 (0-1)
                    'missing_keys': List[str]  # 缺失的关键结构
                }
        """
        logger.info(f"开始识别{self.statement_type}结构...")

        # 1. 查找所有关键结构的位置
        key_positions = self._find_key_positions(table_data)

        logger.info(f"找到的关键结构: {list(key_positions.keys())}")
        for key_name, row_idx in key_positions.items():
            if row_idx < len(table_data):
                item_name = table_data[row_idx][0] if table_data[row_idx] else ""
                logger.info(f"  {key_name}: 第{row_idx}行 - '{item_name}'")

        # 2. 验证关键结构的完整性和顺序
        is_valid, confidence, missing_keys = self._validate_structure(key_positions)

        if not is_valid:
            logger.warning(f"结构验证失败，置信度: {confidence:.2f}, 缺失: {missing_keys}")
            return {
                'is_valid': False,
                'key_positions': key_positions,
                'header_row': None,
                'start_row': None,
                'end_row': None,
                'confidence': confidence,
                'missing_keys': missing_keys
            }

        # 3. 定位表头
        header_row = self._locate_header(table_data, key_positions)
        logger.info(f"定位到表头: 第{header_row}行")

        # 4. 定位开始和结束行
        start_row = self._locate_start_row(key_positions)
        end_row = self._locate_end_row(table_data, key_positions)

        logger.info(f"数据范围: 第{start_row}行 到 第{end_row}行")
        logger.info(f"结构识别成功，置信度: {confidence:.2f}")

        return {
            'is_valid': True,
            'key_positions': key_positions,
            'header_row': header_row,
            'start_row': start_row,
            'end_row': end_row,
            'confidence': confidence,
            'missing_keys': missing_keys
        }

    def _find_key_positions(self, table_data: List[List[str]]) -> Dict[str, int]:
        """
        查找所有关键结构的位置

        Args:
            table_data: 表格数据

        Returns:
            Dict[str, int]: 关键结构名称到行索引的映射
        """
        key_positions = {}

        for key_struct in self.key_structures:
            key_name = key_struct['name']
            patterns = key_struct['patterns']

            # 查找该关键结构
            for row_idx, row in enumerate(table_data):
                if not row or len(row) == 0:
                    continue

                # 获取项目名称（可能在第0列或第1列）
                for col_idx in [0, 1]:
                    if len(row) <= col_idx:
                        continue

                    item_name = row[col_idx].strip() if row[col_idx] else ""
                    item_name = item_name.replace('\n', '').replace('\r', '').strip()

                    if not item_name:
                        continue

                    # 尝试匹配所有模式
                    for pattern in patterns:
                        if re.search(pattern, item_name):
                            key_positions[key_name] = row_idx
                            logger.debug(f"找到关键结构 '{key_name}' 于第{row_idx}行第{col_idx}列: '{item_name}'")
                            break

                    if key_name in key_positions:
                        break

                if key_name in key_positions:
                    break

        return key_positions

    def _validate_structure(self, key_positions: Dict[str, int]) -> Tuple[bool, float, List[str]]:
        """
        验证关键结构的完整性和顺序

        Args:
            key_positions: 关键结构位置

        Returns:
            Tuple[bool, float, List[str]]: (是否有效, 置信度, 缺失的关键结构)
        """
        # 检查必需的关键结构是否都存在
        required_keys = [k['name'] for k in self.key_structures if k.get('required', True)]
        found_keys = list(key_positions.keys())
        missing_keys = [k for k in required_keys if k not in found_keys]

        if missing_keys:
            logger.warning(f"缺失必需的关键结构: {missing_keys}")
            confidence = len(found_keys) / len(required_keys)
            return False, confidence, missing_keys

        # 检查关键结构的顺序是否正确
        key_order = [k['name'] for k in self.key_structures]
        found_order = sorted(key_positions.items(), key=lambda x: x[1])

        order_correct = True
        for i in range(len(found_order) - 1):
            current_key = found_order[i][0]
            next_key = found_order[i + 1][0]

            current_idx = key_order.index(current_key)
            next_idx = key_order.index(next_key)

            if current_idx >= next_idx:
                logger.warning(f"关键结构顺序错误: '{current_key}' 应该在 '{next_key}' 之前")
                order_correct = False
                break

        if not order_correct:
            confidence = 0.5  # 顺序错误，置信度降低
            return False, confidence, []

        # 计算置信度
        confidence = len(found_keys) / len(self.key_structures)

        return True, confidence, missing_keys

    def _locate_header(self, table_data: List[List[str]], key_positions: Dict[str, int]) -> Optional[int]:
        """
        定位表头行

        从第一个关键结构往上查找，找到包含"项目"关键字的行

        Args:
            table_data: 表格数据
            key_positions: 关键结构位置

        Returns:
            Optional[int]: 表头行索引
        """
        if not key_positions:
            return None

        # 获取第一个关键结构的位置
        first_key_row = min(key_positions.values())

        # 从第一个关键结构往上查找（最多查找20行）
        search_start = max(0, first_key_row - 20)

        for row_idx in range(first_key_row - 1, search_start - 1, -1):
            if row_idx < 0 or row_idx >= len(table_data):
                continue

            row = table_data[row_idx]
            if not row or len(row) == 0:
                continue

            # 检查是否包含"项目"关键字
            row_text = ' '.join([str(cell) for cell in row if cell])

            # 表头特征：包含"项目"、"期末"、"期初"等关键字
            if re.search(r'项目', row_text):
                # 进一步验证：应该包含期末/期初相关的关键字
                if re.search(r'期末|期初|本期|上期|年度|金额', row_text):
                    logger.info(f"找到表头于第{row_idx}行: '{row_text[:50]}'")
                    return row_idx

        # 如果没找到，使用第一个关键结构的前一行作为表头
        header_row = first_key_row - 1
        if header_row >= 0:
            logger.warning(f"未找到明确的表头，使用第{header_row}行作为表头")
            return header_row

        return None

    def _locate_start_row(self, key_positions: Dict[str, int]) -> Optional[int]:
        """
        定位数据开始行

        数据从第一个关键结构开始

        Args:
            key_positions: 关键结构位置

        Returns:
            Optional[int]: 数据开始行索引
        """
        if not key_positions:
            return None

        return min(key_positions.values())

    def _locate_end_row(self, table_data: List[List[str]], key_positions: Dict[str, int]) -> Optional[int]:
        """
        定位数据结束行

        从最后一个关键结构往下查找结束标识

        Args:
            table_data: 表格数据
            key_positions: 关键结构位置

        Returns:
            Optional[int]: 数据结束行索引
        """
        if not key_positions:
            return None

        # 获取最后一个关键结构的位置
        last_key_row = max(key_positions.values())

        # 从最后一个关键结构往下查找结束标识（最多查找50行）
        search_end = min(len(table_data), last_key_row + 50)

        for row_idx in range(last_key_row, search_end):
            if row_idx >= len(table_data):
                break

            row = table_data[row_idx]
            if not row or len(row) == 0:
                continue

            item_name = row[0].strip() if row[0] else ""
            item_name = item_name.replace('\n', '').replace('\r', '').strip()

            if not item_name:
                continue

            # 检查是否匹配结束标识
            for pattern in self.end_patterns:
                if re.search(pattern, item_name):
                    logger.info(f"找到结束标识于第{row_idx}行: '{item_name}'")
                    return row_idx

        # 如果没找到结束标识，使用最后一个关键结构后的合理范围
        end_row = min(len(table_data) - 1, last_key_row + 30)
        logger.warning(f"未找到明确的结束标识，使用第{end_row}行作为结束行")
        return end_row

    def get_structure_info(self) -> Dict[str, Any]:
        """
        获取结构信息（用于调试）

        Returns:
            Dict: 结构信息
        """
        return {
            'statement_type': self.statement_type,
            'key_structures': self.key_structures,
            'end_patterns': self.end_patterns
        }
