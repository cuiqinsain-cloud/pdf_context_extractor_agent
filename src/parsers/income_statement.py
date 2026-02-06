"""
合并利润表解析器
负责将提取的表格数据解析为标准化的利润表结构
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from .base_statement_parser import BaseStatementParser
from .column_analyzer import ColumnType

logger = logging.getLogger(__name__)


class IncomeStatementParser(BaseStatementParser):
    """合并利润表解析器"""

    def __init__(self):
        """初始化解析器"""
        # 初始化基类
        super().__init__('income_statement')

        # 营业收入项目模式
        self.revenue_patterns = {
            'operating_revenue': [r'^营业收入$', r'^其中：营业收入$'],
            'operating_total_revenue': [r'^一、营业总收入$', r'^营业总收入$']
        }

        # 营业成本项目模式
        self.cost_patterns = {
            'operating_cost': [r'^营业成本$', r'^其中：营业成本$'],
            'taxes_and_surcharges': [r'^税金及附加$'],
            'selling_expenses': [r'^销售费用$'],
            'administrative_expenses': [r'^管理费用$'],
            'rd_expenses': [r'^研发费用$'],
            'financial_expenses': [r'^财务费用$'],
            'operating_total_cost': [r'^二、营业总成本$', r'^营业总成本$']
        }

        # 其他损益项目模式
        self.other_items_patterns = {
            'other_income': [r'^加：其他收益$', r'^其他收益$'],
            'investment_income': [r'^投资收益', r'^加：投资收益'],
            'fair_value_change': [r'^公允价值变动收益', r'^其中：对联营企业和合营企业的投资收益'],
            'credit_impairment': [r'^信用减值损失', r'^加：信用减值损失'],
            'asset_impairment': [r'^资产减值损失', r'^加：资产减值损失'],
            'asset_disposal': [r'^资产处置收益', r'^加：资产处置收益']
        }

        # 利润项目模式
        self.profit_patterns = {
            'operating_profit': [r'^三、营业利润', r'^二、营业利润', r'^营业利润'],
            'non_operating_income': [r'^加：营业外收入', r'^营业外收入'],
            'non_operating_expenses': [r'^减：营业外支出', r'^营业外支出'],
            'total_profit': [r'^四、利润总额', r'^三、利润总额', r'^利润总额'],
            'income_tax': [r'^减：所得税费用', r'^所得税费用'],
            'net_profit': [r'^五、净利润', r'^四、净利润', r'^净利润(?!（)'],
            'continuing_operations_profit': [r'持续经营净利润', r'^1\.持续经营净利润'],
            'discontinued_operations_profit': [r'终止经营净利润', r'^2\.终止经营净利润'],
            'parent_net_profit': [r'归属于母公司.*的净利润', r'归属于母公司股东的净利润', r'^1\.归属于母公司'],
            'minority_profit': [r'少数股东损益', r'^2\.少数股东损益']
        }

        # 综合收益项目模式
        self.comprehensive_income_patterns = {
            'other_comprehensive_income': [r'^六、其他综合收益的税后净额', r'^其他综合收益.*税后净额'],
            'total_comprehensive_income': [r'^七、综合收益总额', r'^八、综合收益总额', r'^综合收益总额'],
            'parent_comprehensive_income': [r'归属于母公司.*的综合收益总额', r'归属.*母公司.*综合收益', r'^\(一\)|（一）.*归属.*母公司'],
            'minority_comprehensive_income': [r'归属于少数股东的综合收益总额', r'归属.*少数股东.*综合收益', r'^\(二\)|（二）.*归属.*少数股东']
        }

        # 每股收益项目模式
        self.eps_patterns = {
            'basic_eps': [r'基本每股收益', r'^1\.基本每股收益', r'^\(一\)|（一）.*基本每股收益'],
            'diluted_eps': [r'稀释每股收益', r'^2\.稀释每股收益', r'^\(二\)|（二）.*稀释每股收益']
        }

    def parse_income_statement(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        解析合并利润表

        Args:
            table_data (List[List[str]]): 表格数据

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        logger.info("开始解析合并利润表...")

        # 重置缓存
        self.reset_cache()

        # 初始化结果结构
        result = {
            'report_type': '合并利润表',
            'revenue': {},
            'costs': {},
            'other_items': {},
            'profit': {},
            'comprehensive_income': {},
            'eps': {},
            'parsing_info': {
                'total_rows': len(table_data),
                'matched_items': 0,
                'unmatched_items': []
            },
            'ordered_items': [],
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
            matched_item_name = None

            # 匹配营业收入项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.revenue_patterns,
                    result['revenue'], result, 'revenue'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配营业成本项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.cost_patterns,
                    result['costs'], result, 'costs'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配其他损益项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.other_items_patterns,
                    result['other_items'], result, 'other_items'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配利润项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.profit_patterns,
                    result['profit'], result, 'profit'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配综合收益项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.comprehensive_income_patterns,
                    result['comprehensive_income'], result, 'comprehensive_income'
                )
                if matched:
                    matched_item_name = matched_name

            # 匹配每股收益项目
            if not matched:
                matched, matched_name = self._match_and_store_item_with_name(
                    item_name, values, self.eps_patterns,
                    result['eps'], result, 'eps'
                )
                if matched:
                    matched_item_name = matched_name

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
            result (Dict): 完整的结果字典
            section_path (str): 在数据结构中的路径

        Returns:
            Tuple[bool, Optional[str]]: (是否成功匹配, 匹配的标准名称)
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

    def validate_income_statement(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证利润表数据的完整性和准确性

        实现三层级验证：
        - 层级1：子项目合计验证（营业总成本）
        - 层级2：利润计算验证（营业利润、利润总额、净利润）
        - 层级3：归属验证（净利润分配、综合收益）

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
                'level1_subtotal_checks': [],
                'level2_profit_checks': [],
                'level3_attribution_checks': []
            },
            'completeness_score': 0.0
        }

        try:
            tolerance_rate = 0.01  # 1%容差（利润表计算更复杂，容差稍大）

            # ========== 层级1：营业总成本验证 ==========
            logger.info("开始层级1验证：营业总成本")

            operating_cost = self._get_numeric_value(
                parsed_data.get('costs', {}).get('operating_cost', {}).get('current_period')
            )
            taxes = self._get_numeric_value(
                parsed_data.get('costs', {}).get('taxes_and_surcharges', {}).get('current_period')
            )
            selling = self._get_numeric_value(
                parsed_data.get('costs', {}).get('selling_expenses', {}).get('current_period')
            )
            admin = self._get_numeric_value(
                parsed_data.get('costs', {}).get('administrative_expenses', {}).get('current_period')
            )
            rd = self._get_numeric_value(
                parsed_data.get('costs', {}).get('rd_expenses', {}).get('current_period')
            )
            financial = self._get_numeric_value(
                parsed_data.get('costs', {}).get('financial_expenses', {}).get('current_period')
            )
            total_cost = self._get_numeric_value(
                parsed_data.get('costs', {}).get('operating_total_cost', {}).get('current_period')
            )

            if all(v is not None for v in [operating_cost, total_cost]):
                calculated = operating_cost
                if taxes is not None:
                    calculated += taxes
                if selling is not None:
                    calculated += selling
                if admin is not None:
                    calculated += admin
                if rd is not None:
                    calculated += rd
                if financial is not None:
                    calculated += financial

                difference = abs(calculated - total_cost)
                tolerance = max(abs(calculated), abs(total_cost)) * tolerance_rate
                passed = difference <= tolerance

                level1_result = {
                    'name': '营业总成本',
                    'formula': '营业成本 + 税金及附加 + 销售费用 + 管理费用 + 研发费用 + 财务费用',
                    'calculated': float(calculated),
                    'reported': float(total_cost),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"营业总成本验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={total_cost:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level1_subtotal_checks'].append(level1_result)
                if not passed:
                    validation_result['warnings'].append(level1_result['message'])

            # ========== 层级2：利润计算验证 ==========
            logger.info("开始层级2验证：利润计算")

            # 2.1 净利润 = 利润总额 - 所得税费用
            total_profit = self._get_numeric_value(
                parsed_data.get('profit', {}).get('total_profit', {}).get('current_period')
            )
            income_tax = self._get_numeric_value(
                parsed_data.get('profit', {}).get('income_tax', {}).get('current_period')
            )
            net_profit = self._get_numeric_value(
                parsed_data.get('profit', {}).get('net_profit', {}).get('current_period')
            )

            if all(v is not None for v in [total_profit, income_tax, net_profit]):
                calculated = total_profit - income_tax
                difference = abs(calculated - net_profit)
                tolerance = max(abs(calculated), abs(net_profit)) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '净利润',
                    'formula': '利润总额 - 所得税费用',
                    'calculated': float(calculated),
                    'reported': float(net_profit),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"净利润验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={net_profit:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_profit_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # ========== 层级3：归属验证 ==========
            logger.info("开始层级3验证：归属验证")

            # 3.1 净利润 = 归属于母公司净利润 + 少数股东损益
            parent_profit = self._get_numeric_value(
                parsed_data.get('profit', {}).get('parent_net_profit', {}).get('current_period')
            )
            minority_profit = self._get_numeric_value(
                parsed_data.get('profit', {}).get('minority_profit', {}).get('current_period')
            )

            if all(v is not None for v in [net_profit, parent_profit, minority_profit]):
                calculated = parent_profit + minority_profit
                difference = abs(calculated - net_profit)
                tolerance = max(abs(calculated), abs(net_profit)) * tolerance_rate
                passed = difference <= tolerance

                level3_result = {
                    'name': '净利润归属',
                    'formula': '归属于母公司净利润 + 少数股东损益',
                    'calculated': float(calculated),
                    'reported': float(net_profit),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"净利润归属验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={net_profit:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level3_attribution_checks'].append(level3_result)
                if not passed:
                    validation_result['errors'].append(level3_result['message'])
                    validation_result['is_valid'] = False

            # ========== 完整性检查 ==========
            essential_items = [
                'operating_revenue', 'operating_cost', 'net_profit',
                'total_profit', 'operating_profit'
            ]

            found_items = 0
            missing_items = []
            all_items = {}
            all_items.update(parsed_data.get('revenue', {}))
            all_items.update(parsed_data.get('costs', {}))
            all_items.update(parsed_data.get('profit', {}))

            for item in essential_items:
                if item in all_items:
                    # 检查是否有数据
                    item_data = all_items[item]
                    if item_data.get('current_period') is not None:
                        found_items += 1
                    else:
                        missing_items.append(item)
                        logger.warning(f"关键项目 {item} 缺少数据")
                else:
                    missing_items.append(item)
                    logger.warning(f"关键项目 {item} 未被识别")

            validation_result['completeness_score'] = found_items / len(essential_items)

            if validation_result['completeness_score'] < 0.7:
                validation_result['warnings'].append(
                    f"关键项目完整性较低: {validation_result['completeness_score']:.1%}"
                )

            if missing_items:
                validation_result['warnings'].append(
                    f"缺失的关键项目: {', '.join(missing_items)}"
                )

        except Exception as e:
            validation_result['errors'].append(f"验证过程中出现错误: {str(e)}")
            validation_result['is_valid'] = False
            logger.error(f"验证过程中出现错误: {str(e)}", exc_info=True)

        logger.info(f"验证完成，总体结果: {validation_result['is_valid']}")

        return validation_result

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
            cleaned = re.sub(r'[^\d.\-]', '', str(value_str))
            if cleaned and cleaned not in ['-', '--']:
                return float(cleaned)
        except (ValueError, TypeError):
            pass

        return None
