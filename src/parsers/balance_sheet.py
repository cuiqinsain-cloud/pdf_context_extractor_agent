"""
合并资产负债表解析器
负责将提取的表格数据解析为标准化的资产负债表结构
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
import pandas as pd
from decimal import Decimal
from .base_statement_parser import BaseStatementParser
from .column_analyzer import ColumnType

logger = logging.getLogger(__name__)


class BalanceSheetParser(BaseStatementParser):
    """合并资产负债表解析器"""

    def __init__(self):
        """初始化解析器"""
        # 初始化基类
        super().__init__('balance_sheet')

        # 资产项目关键词映射
        self.asset_patterns = {
            # 流动资产
            'current_assets': {
                '货币资金': [r'货币资金'],
                '交易性金融资产': [r'交易性金融资产'],
                '衍生金融资产': [r'衍生金融资产'],
                '应收票据': [r'应收票据'],
                '应收账款': [r'应收账款'],
                '应收款项融资': [r'应收款项融资'],
                '预付款项': [r'预付款项'],
                '其他应收款': [r'其他应收款'],
                '存货': [r'存货'],
                '合同资产': [r'合同资产'],
                '持有待售资产': [r'持有待售资产'],
                '一年内到期的非流动资产': [r'一年内到期的非流动资产'],
                '其他流动资产': [r'其他流动资产']
            },
            # 非流动资产
            'non_current_assets': {
                '债权投资': [r'债权投资'],
                '其他债权投资': [r'其他债权投资'],
                '长期应收款': [r'长期应收款'],
                '长期股权投资': [r'长期股权投资'],
                '其他权益工具投资': [r'其他权益工具投资'],
                '其他非流动金融资产': [r'其他非流动金融资产'],
                '投资性房地产': [r'投资性房地产'],
                '固定资产': [r'固定资产'],
                '在建工程': [r'在建工程'],
                '生产性生物资产': [r'生产性生物资产'],
                '油气资产': [r'油气资产'],
                '使用权资产': [r'使用权资产'],
                '无形资产': [r'无形资产'],
                '开发支出': [r'开发支出'],
                '商誉': [r'商誉'],
                '长期待摊费用': [r'长期待摊费用'],
                '递延所得税资产': [r'递延所得税资产'],
                '其他非流动资产': [r'其他非流动资产']
            }
        }

        # 负债项目关键词映射
        self.liability_patterns = {
            # 流动负债
            'current_liabilities': {
                '短期借款': [r'短期借款'],
                '交易性金融负债': [r'交易性金融负债'],
                '衍生金融负债': [r'衍生金融负债'],
                '应付票据': [r'应付票据'],
                '应付账款': [r'应付账款'],
                '预收款项': [r'预收款项'],
                '合同负债': [r'合同负债'],
                '应付职工薪酬': [r'^应付职工薪酬$'],
                '应交税费': [r'应交税费'],
                '其他应付款': [r'其他应付款'],
                '持有待售负债': [r'持有待售负债'],
                '一年内到期的非流动负债': [r'一年内到期的非流动负债'],
                '其他流动负债': [r'其他流动负债']
            },
            # 非流动负债
            'non_current_liabilities': {
                '长期借款': [r'长期借款'],
                '应付债券': [r'应付债券'],
                '其中：优先股': [r'其中：优先股'],
                '永续债': [r'永续债'],
                '租赁负债': [r'租赁负债'],
                '长期应付款': [r'长期应付款'],
                '长期应付职工薪酬': [r'长期应付职工薪酬'],
                '预计负债': [r'预计负债'],
                '递延收益': [r'递延收益'],
                '递延所得税负债': [r'递延所得税负债'],
                '其他非流动负债': [r'其他非流动负债']
            }
        }

        # 所有者权益项目关键词映射
        self.equity_patterns = {
            '实收资本': [r'实收资本', r'股本'],
            '其他权益工具': [r'其他权益工具'],
            '其中：优先股': [r'其中：优先股'],
            '永续债': [r'永续债'],
            '资本公积': [r'资本公积'],
            '减：库存股': [r'减：库存股'],
            '其他综合收益': [r'其他综合收益'],
            '专项储备': [r'专项储备'],
            '盈余公积': [r'盈余公积'],
            '未分配利润': [r'未分配利润'],
            '少数股东权益': [r'少数股东权益']
        }

    def parse_balance_sheet(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        解析合并资产负债表

        Args:
            table_data (List[List[str]]): 表格数据

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        logger.info("开始解析合并资产负债表...")

        # 重置缓存
        self.reset_cache()

        # 初始化结果结构
        result = {
            'report_type': '合并资产负债表',
            'assets': {
                'current_assets': {},
                'current_assets_total': {},  # 流动资产合计
                'non_current_assets': {},
                'non_current_assets_total': {},  # 非流动资产合计
                'assets_total': {}  # 资产总计
            },
            'liabilities': {
                'current_liabilities': {},
                'current_liabilities_total': {},  # 流动负债合计
                'non_current_liabilities': {},
                'non_current_liabilities_total': {},  # 非流动负债合计
                'liabilities_total': {}  # 负债合计
            },
            'equity': {
                'items': {},  # 所有者权益普通项目
                'parent_equity_total': {},  # 归属于母公司所有者权益合计
                'equity_total': {}  # 所有者权益合计
            },
            'liabilities_and_equity_total': {},
            'parsing_info': {
                'total_rows': len(table_data),
                'matched_items': 0,
                'unmatched_items': []
            },
            'ordered_items': [],  # 保持原始顺序的项目列表
            'structure_info': {}  # 结构识别信息
        }

        if not table_data:
            logger.warning("表格数据为空")
            return result

        # ========== 步骤1: 识别报表结构 ==========
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
        else:
            logger.info(f"结构识别成功，置信度: {structure_result['confidence']:.2%}")
            logger.info(f"数据范围: 第{structure_result['start_row']}行 到 第{structure_result['end_row']}行")

        # ========== 步骤2: 提取有效数据范围 ==========
        logger.info("步骤2: 提取有效数据范围...")
        if structure_result['is_valid']:
            data_to_parse = self.extract_statement_data(table_data, structure_result)
            row_offset = structure_result['start_row']
        else:
            data_to_parse = table_data
            row_offset = 0

        # ========== 步骤3: 获取表头信息 ==========
        logger.info("步骤3: 分析表头结构...")
        header_info = self.get_header_info(table_data, structure_result)

        # ========== 步骤4: 逐行解析数据 ==========
        logger.info("步骤4: 逐行解析数据...")
        for row_idx, row in enumerate(data_to_parse):
            if not row or len(row) == 0:
                continue

            # 使用基类方法获取项目名称（支持第0列和第1列）
            item_name = self.get_item_name_from_row(row, header_info)

            if not item_name:
                continue

            # 使用基类方法提取数值
            values = self.extract_values_from_row(row, header_info)

            # 分类匹配项目
            matched = False
            matched_item_name = None  # 用于记录已匹配的项目名称

            # 匹配资产项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.asset_patterns['current_assets'],
                    result['assets']['current_assets'], result, 'assets.current_assets'
                )
                if matched:
                    matched_item_name = matched_name

            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.asset_patterns['non_current_assets'],
                    result['assets']['non_current_assets'], result, 'assets.non_current_assets'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配负债项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.liability_patterns['current_liabilities'],
                    result['liabilities']['current_liabilities'], result, 'liabilities.current_liabilities'
                )
                if matched:
                    matched_item_name = matched_name

            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.liability_patterns['non_current_liabilities'],
                    result['liabilities']['non_current_liabilities'], result, 'liabilities.non_current_liabilities'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配所有者权益项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.equity_patterns,
                    result['equity']['items'], result, 'equity.items'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配总计项目
            if not matched:
                matched = self._match_total_items(item_name, values, result)

            # 记录匹配结果
            if matched:
                result['parsing_info']['matched_items'] += 1
            else:
                result['parsing_info']['unmatched_items'].append({
                    'row_index': row_idx + row_offset,  # 使用正确的行索引
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
        匹配项目并存储数据，返回匹配结果和标准名称

        Args:
            item_name (str): 项目名称
            values (Dict[str, str]): 数值数据
            patterns (Dict[str, List[str]]): 匹配模式
            storage (Dict[str, Dict]): 存储位置
            result (Dict): 完整的结果字典，用于访问ordered_items
            section_path (str): 在数据结构中的路径，如'assets.current_assets'

        Returns:
            Tuple[bool, Optional[str]]: (是否成功匹配, 匹配的标准名称)
        """
        for standard_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, item_name):
                    # 如果项目已经存在，跳过重复项目（保留第一个，即合并资产负债表的数据）
                    if standard_name in storage:
                        return True, standard_name  # 返回True表示匹配成功，但不覆盖现有数据

                    # 存储新项目数据
                    item_data = {
                        'original_name': item_name,
                        **values
                    }
                    storage[standard_name] = item_data

                    # 同时添加到有序列表中
                    result['ordered_items'].append({
                        'section': section_path,
                        'standard_name': standard_name,
                        'data': item_data
                    })

                    return True, standard_name
        return False, None

    def _match_total_items(self, item_name: str, values: Dict[str, str], result: Dict) -> bool:
        """
        匹配总计类项目（包括中间合计项和顶级合计项）

        Args:
            item_name (str): 项目名称
            values (Dict[str, str]): 数值数据
            result (Dict): 结果存储

        Returns:
            bool: 是否成功匹配
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

        # 非流动资产合计
        elif re.search(r'^非流动资产合计$', item_name):
            result['assets']['non_current_assets_total'] = item_data
            result['ordered_items'].append({
                'section': 'assets.non_current_assets_total',
                'standard_name': 'non_current_assets_total',
                'data': item_data
            })
            return True

        # 资产总计
        elif re.search(r'资产总计', item_name):
            result['assets']['assets_total'] = item_data
            result['ordered_items'].append({
                'section': 'assets.assets_total',
                'standard_name': 'assets_total',
                'data': item_data
            })
            return True

        # 流动负债合计
        elif re.search(r'^流动负债合计$', item_name):
            result['liabilities']['current_liabilities_total'] = item_data
            result['ordered_items'].append({
                'section': 'liabilities.current_liabilities_total',
                'standard_name': 'current_liabilities_total',
                'data': item_data
            })
            return True

        # 非流动负债合计
        elif re.search(r'^非流动负债合计$', item_name):
            result['liabilities']['non_current_liabilities_total'] = item_data
            result['ordered_items'].append({
                'section': 'liabilities.non_current_liabilities_total',
                'standard_name': 'non_current_liabilities_total',
                'data': item_data
            })
            return True

        # 负债合计
        elif re.search(r'负债合计', item_name):
            result['liabilities']['liabilities_total'] = item_data
            result['ordered_items'].append({
                'section': 'liabilities.liabilities_total',
                'standard_name': 'liabilities_total',
                'data': item_data
            })
            return True

        # 归属于母公司所有者权益合计
        elif re.search(r'归属于母公司所有者权益（或股东权益）?\s*合\s*计|归属于母公司.*权益.*合\s*计', item_name):
            result['equity']['parent_equity_total'] = item_data
            result['ordered_items'].append({
                'section': 'equity.parent_equity_total',
                'standard_name': 'parent_equity_total',
                'data': item_data
            })
            return True

        # 所有者权益合计（排除"归属于母公司所有者权益合计"）
        elif re.search(r'^所有者权益.*?合\s*计$|^股东权益\s*合\s*计$', item_name):
            result['equity']['equity_total'] = item_data
            result['ordered_items'].append({
                'section': 'equity.equity_total',
                'standard_name': 'equity_total',
                'data': item_data
            })
            return True

        # 负债和所有者权益总计
        elif re.search(r'负债和所有者权益.{0,10}总计|负债和股东权益.{0,10}总计', item_name):
            result['liabilities_and_equity_total'] = item_data
            result['ordered_items'].append({
                'section': 'liabilities_and_equity_total',
                'standard_name': 'liabilities_and_equity_total',
                'data': item_data
            })
            return True

        return False

    def validate_balance_sheet(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证资产负债表数据的完整性和准确性

        实现三层级平衡性检查：
        - 层级1：子项目合计验证（流动/非流动资产、负债、权益）
        - 层级2：大类合计验证（资产总计、负债合计）
        - 层级3：总平衡验证（资产总计 = 负债和所有者权益总计）

        Args:
            parsed_data (Dict[str, Any]): 解析后的数据

        Returns:
            Dict[str, Any]: 验证结果
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'balance_check': {
                'level1_subtotal_checks': [],  # 层级1：子项目合计
                'level2_category_checks': [],  # 层级2：大类合计
                'level3_total_check': None     # 层级3：总平衡
            },
            'completeness_score': 0.0
        }

        try:
            tolerance_rate = 0.001  # 0.1%容差

            # ========== 层级1：子项目合计验证 ==========
            logger.info("开始层级1验证：子项目合计")

            # 1.1 流动资产合计验证
            level1_result = self._validate_subtotal(
                parsed_data.get('assets', {}).get('current_assets', {}),
                parsed_data.get('assets', {}).get('current_assets_total'),
                '流动资产合计',
                tolerance_rate
            )
            validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
            if not level1_result['passed']:
                validation_result['errors'].append(level1_result['message'])
                validation_result['is_valid'] = False

            # 1.2 非流动资产合计验证
            level1_result = self._validate_subtotal(
                parsed_data.get('assets', {}).get('non_current_assets', {}),
                parsed_data.get('assets', {}).get('non_current_assets_total'),
                '非流动资产合计',
                tolerance_rate
            )
            validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
            if not level1_result['passed']:
                validation_result['errors'].append(level1_result['message'])
                validation_result['is_valid'] = False

            # 1.3 流动负债合计验证
            level1_result = self._validate_subtotal(
                parsed_data.get('liabilities', {}).get('current_liabilities', {}),
                parsed_data.get('liabilities', {}).get('current_liabilities_total'),
                '流动负债合计',
                tolerance_rate
            )
            validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
            if not level1_result['passed']:
                validation_result['errors'].append(level1_result['message'])
                validation_result['is_valid'] = False

            # 1.4 非流动负债合计验证
            level1_result = self._validate_subtotal(
                parsed_data.get('liabilities', {}).get('non_current_liabilities', {}),
                parsed_data.get('liabilities', {}).get('non_current_liabilities_total'),
                '非流动负债合计',
                tolerance_rate
            )
            validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
            if not level1_result['passed']:
                validation_result['errors'].append(level1_result['message'])
                validation_result['is_valid'] = False

            # 1.5 所有者权益合计验证
            level1_result = self._validate_subtotal(
                parsed_data.get('equity', {}).get('items', {}),
                parsed_data.get('equity', {}).get('equity_total') or
                parsed_data.get('equity', {}).get('parent_equity_total'),
                '所有者权益合计',
                tolerance_rate
            )
            validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
            if not level1_result['passed']:
                validation_result['warnings'].append(level1_result['message'])

            # ========== 层级2：大类合计验证 ==========
            logger.info("开始层级2验证：大类合计")

            # 2.1 资产总计 = 流动资产合计 + 非流动资产合计
            current_assets_total = self._get_numeric_value(
                parsed_data.get('assets', {}).get('current_assets_total', {}).get('current_period')
            )
            non_current_assets_total = self._get_numeric_value(
                parsed_data.get('assets', {}).get('non_current_assets_total', {}).get('current_period')
            )
            assets_total = self._get_numeric_value(
                parsed_data.get('assets', {}).get('assets_total', {}).get('current_period')
            )

            if current_assets_total is not None and non_current_assets_total is not None and assets_total is not None:
                calculated_total = current_assets_total + non_current_assets_total
                difference = abs(calculated_total - assets_total)
                tolerance = max(calculated_total, assets_total) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '资产总计',
                    'formula': '流动资产合计 + 非流动资产合计',
                    'calculated': float(calculated_total),
                    'reported': float(assets_total),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"资产总计验证{'通过' if passed else '失败'}：计算值={calculated_total:,.2f}, 报表值={assets_total:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_category_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # 2.2 负债合计 = 流动负债合计 + 非流动负债合计
            current_liabilities_total = self._get_numeric_value(
                parsed_data.get('liabilities', {}).get('current_liabilities_total', {}).get('current_period')
            )
            non_current_liabilities_total = self._get_numeric_value(
                parsed_data.get('liabilities', {}).get('non_current_liabilities_total', {}).get('current_period')
            )
            liabilities_total = self._get_numeric_value(
                parsed_data.get('liabilities', {}).get('liabilities_total', {}).get('current_period')
            )

            if current_liabilities_total is not None and non_current_liabilities_total is not None and liabilities_total is not None:
                calculated_total = current_liabilities_total + non_current_liabilities_total
                difference = abs(calculated_total - liabilities_total)
                tolerance = max(calculated_total, liabilities_total) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '负债合计',
                    'formula': '流动负债合计 + 非流动负债合计',
                    'calculated': float(calculated_total),
                    'reported': float(liabilities_total),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"负债合计验证{'通过' if passed else '失败'}：计算值={calculated_total:,.2f}, 报表值={liabilities_total:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_category_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # 2.3 负债和所有者权益总计 = 负债合计 + 所有者权益合计
            equity_total = self._get_numeric_value(
                parsed_data.get('equity', {}).get('equity_total', {}).get('current_period')
            ) or self._get_numeric_value(
                parsed_data.get('equity', {}).get('parent_equity_total', {}).get('current_period')
            )
            liab_equity_total = self._get_numeric_value(
                parsed_data.get('liabilities_and_equity_total', {}).get('current_period')
            )

            if liabilities_total is not None and equity_total is not None and liab_equity_total is not None:
                calculated_total = liabilities_total + equity_total
                difference = abs(calculated_total - liab_equity_total)
                tolerance = max(calculated_total, liab_equity_total) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '负债和所有者权益总计',
                    'formula': '负债合计 + 所有者权益合计',
                    'calculated': float(calculated_total),
                    'reported': float(liab_equity_total),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"负债和所有者权益总计验证{'通过' if passed else '失败'}：计算值={calculated_total:,.2f}, 报表值={liab_equity_total:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_category_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # ========== 层级3：总平衡验证 ==========
            logger.info("开始层级3验证：总平衡")

            if assets_total is not None and liab_equity_total is not None:
                difference = abs(assets_total - liab_equity_total)
                tolerance = max(assets_total, liab_equity_total) * tolerance_rate
                passed = difference <= tolerance

                validation_result['balance_check']['level3_total_check'] = {
                    'formula': '资产总计 = 负债和所有者权益总计',
                    'assets_total': float(assets_total),
                    'liabilities_and_equity_total': float(liab_equity_total),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"总平衡验证{'通过' if passed else '失败'}：资产总计={assets_total:,.2f}, 负债和所有者权益总计={liab_equity_total:,.2f}, 差额={difference:,.2f}"
                }

                if not passed:
                    validation_result['errors'].append(validation_result['balance_check']['level3_total_check']['message'])
                    validation_result['is_valid'] = False

            # ========== 完整性检查 ==========
            essential_items = [
                '货币资金', '应收账款', '存货', '固定资产',
                '短期借款', '应付账款', '实收资本', '未分配利润'
            ]

            found_items = 0
            all_items = {}

            # 收集所有已识别的项目
            for category in ['current_assets', 'non_current_assets']:
                all_items.update(parsed_data.get('assets', {}).get(category, {}))

            for category in ['current_liabilities', 'non_current_liabilities']:
                all_items.update(parsed_data.get('liabilities', {}).get(category, {}))

            all_items.update(parsed_data.get('equity', {}))

            # 检查必要项目
            for item in essential_items:
                if any(item in key for key in all_items.keys()):
                    found_items += 1

            validation_result['completeness_score'] = found_items / len(essential_items)

            if validation_result['completeness_score'] < 0.7:
                validation_result['warnings'].append(
                    f"关键项目完整性较低: {validation_result['completeness_score']:.1%}"
                )

            # ========== 数据合理性检查 ==========
            unmatched_count = len(parsed_data.get('parsing_info', {}).get('unmatched_items', []))
            total_rows = parsed_data.get('parsing_info', {}).get('total_rows', 1)

            if unmatched_count / total_rows > 0.3:
                validation_result['warnings'].append(
                    f"未匹配项目过多: {unmatched_count}/{total_rows}"
                )

        except Exception as e:
            validation_result['errors'].append(f"验证过程中出现错误: {str(e)}")
            validation_result['is_valid'] = False
            logger.error(f"验证过程中出现错误: {str(e)}", exc_info=True)

        # 统计验证结果
        level1_passed = sum(1 for check in validation_result['balance_check']['level1_subtotal_checks'] if check.get('passed', False))
        level1_total = len(validation_result['balance_check']['level1_subtotal_checks'])
        level2_passed = sum(1 for check in validation_result['balance_check']['level2_category_checks'] if check.get('passed', False))
        level2_total = len(validation_result['balance_check']['level2_category_checks'])
        level3_passed = validation_result['balance_check']['level3_total_check'].get('passed', False) if validation_result['balance_check']['level3_total_check'] else False

        logger.info(f"验证完成 - 层级1: {level1_passed}/{level1_total}, 层级2: {level2_passed}/{level2_total}, 层级3: {'通过' if level3_passed else '失败'}")
        logger.info(f"总体结果: {validation_result['is_valid']}, 错误: {len(validation_result['errors'])}, 警告: {len(validation_result['warnings'])}")

        return validation_result

    def _validate_subtotal(self, items_dict: Dict[str, Any], subtotal_item: Optional[Dict[str, Any]],
                          subtotal_name: str, tolerance_rate: float) -> Dict[str, Any]:
        """
        验证子项目合计的正确性

        Args:
            items_dict: 包含所有子项目的字典
            subtotal_item: 合计项目的数据
            subtotal_name: 合计项目名称
            tolerance_rate: 容差比例

        Returns:
            Dict[str, Any]: 验证结果
        """
        result = {
            'name': subtotal_name,
            'passed': False,
            'calculated': None,
            'reported': None,
            'difference': None,
            'tolerance': None,
            'message': '',
            'item_count': 0,
            'deduction_items': []  # 记录减项
        }

        try:
            # 获取报表中的合计值
            if subtotal_item is None:
                result['message'] = f"{subtotal_name}：未找到合计项目"
                logger.warning(result['message'])
                return result

            reported_total = self._get_numeric_value(subtotal_item.get('current_period'))
            if reported_total is None:
                result['message'] = f"{subtotal_name}：合计值为空"
                logger.warning(result['message'])
                return result

            # 定义减项关键字（这些项目需要从总额中减去）
            deduction_keywords = ['减：', '减:', '减-']

            # 计算子项目之和（排除合计项本身，正确处理减项）
            calculated_total = 0.0
            item_count = 0

            for item_name, item_data in items_dict.items():
                # 跳过合计项本身
                if '合计' in item_name:
                    continue

                item_value = self._get_numeric_value(item_data.get('current_period'))
                if item_value is not None:
                    # 判断是否为减项
                    is_deduction = any(keyword in item_name for keyword in deduction_keywords)

                    if is_deduction:
                        # 减项：从总额中减去
                        calculated_total -= item_value
                        result['deduction_items'].append({
                            'name': item_name,
                            'value': item_value
                        })
                        logger.debug(f"  减项: {item_name} = -{item_value:,.2f}")
                    else:
                        # 加项：加到总额中
                        calculated_total += item_value
                        logger.debug(f"  加项: {item_name} = +{item_value:,.2f}")

                    item_count += 1

            # 如果没有子项目，跳过验证
            if item_count == 0:
                result['message'] = f"{subtotal_name}：没有子项目数据"
                result['passed'] = True  # 没有数据时认为通过
                logger.info(result['message'])
                return result

            # 计算差额和容差
            difference = abs(calculated_total - reported_total)
            tolerance = max(abs(calculated_total), abs(reported_total)) * tolerance_rate
            passed = difference <= tolerance

            deduction_info = ""
            if result['deduction_items']:
                deduction_count = len(result['deduction_items'])
                deduction_total = sum(item['value'] for item in result['deduction_items'])
                deduction_info = f", 其中减项{deduction_count}个(合计{deduction_total:,.2f})"

            result.update({
                'passed': passed,
                'calculated': float(calculated_total),
                'reported': float(reported_total),
                'difference': float(difference),
                'tolerance': float(tolerance),
                'item_count': item_count,
                'message': f"{subtotal_name}验证{'通过' if passed else '失败'}：计算值={calculated_total:,.2f}（{item_count}项{deduction_info}）, 报表值={reported_total:,.2f}, 差额={difference:,.2f}"
            })

            if passed:
                logger.info(result['message'])
            else:
                logger.warning(result['message'])

        except Exception as e:
            result['message'] = f"{subtotal_name}验证出错: {str(e)}"
            logger.error(result['message'], exc_info=True)

        return result

    def _get_numeric_value(self, value_str: Optional[str]) -> Optional[float]:
        """
        将字符串转换为数值

        Args:
            value_str (Optional[str]): 数值字符串

        Returns:
            Optional[float]: 转换后的数值
        """
        if not value_str:
            return None

        try:
            # 移除千分位逗号等格式化字符
            cleaned = re.sub(r'[^\d.\-]', '', str(value_str))
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass

        return None


def test_balance_sheet_parser():
    """测试资产负债表解析器"""
    # 示例测试数据
    sample_data = [
        ['项目', '本期末', '上期末', '附注'],
        ['流动资产：', '', '', ''],
        ['货币资金', '1000000.00', '900000.00', '六、1'],
        ['应收账款', '500000.00', '450000.00', '六、2'],
        ['存货', '300000.00', '280000.00', '六、3'],
        ['流动资产合计', '1800000.00', '1630000.00', ''],
        ['非流动资产：', '', '', ''],
        ['固定资产', '2000000.00', '1900000.00', '六、4'],
        ['无形资产', '100000.00', '95000.00', '六、5'],
        ['非流动资产合计', '2100000.00', '1995000.00', ''],
        ['资产总计', '3900000.00', '3625000.00', ''],
        ['流动负债：', '', '', ''],
        ['短期借款', '200000.00', '180000.00', '六、6'],
        ['应付账款', '300000.00', '250000.00', '六、7'],
        ['流动负债合计', '500000.00', '430000.00', ''],
        ['所有者权益：', '', '', ''],
        ['实收资本', '2000000.00', '2000000.00', '六、8'],
        ['未分配利润', '1400000.00', '1195000.00', '六、9'],
        ['所有者权益合计', '3400000.00', '3195000.00', ''],
        ['负债和所有者权益总计', '3900000.00', '3625000.00', '']
    ]

    parser = BalanceSheetParser()
    result = parser.parse_balance_sheet(sample_data)
    validation = parser.validate_balance_sheet(result)

    print("解析结果:")
    print(f"资产项目数: {len(result['assets']['current_assets']) + len(result['assets']['non_current_assets'])}")
    print(f"负债项目数: {len(result['liabilities']['current_liabilities']) + len(result['liabilities']['non_current_liabilities'])}")
    print(f"权益项目数: {len(result['equity'])}")
    print(f"验证结果: {'通过' if validation['is_valid'] else '失败'}")


if __name__ == "__main__":
    test_balance_sheet_parser()