"""
合并现金流量表解析器
负责将提取的表格数据解析为标准化的现金流量表结构
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from .base_statement_parser import BaseStatementParser
from .column_analyzer import ColumnType

logger = logging.getLogger(__name__)


class CashFlowParser(BaseStatementParser):
    """合并现金流量表解析器"""

    def __init__(self):
        """初始化解析器"""
        # 初始化基类
        super().__init__('cash_flow')

        # 经营活动现金流量项目模式
        self.operating_patterns = {
            'sales_goods_cash': [r'^销售商品、提供劳务收到的\s*现金$'],
            'tax_refund': [r'^收到的税费返还$'],
            'other_operating_inflow': [r'^收到其他与经营活动有关的\s*现金$'],
            'operating_inflow_subtotal': [r'^经营活动现金流入小计$'],
            'purchase_goods_cash': [r'^购买商品、接受劳务支付的\s*现金$'],
            'employee_cash': [r'^支付给职工及?以?及?为职工支付的\s*现金$', r'^支付给职工.*的\s*现金$'],
            'tax_payment': [r'^支付的各项税费$'],
            'other_operating_outflow': [r'^支付其他与经营活动有关的\s*现金$'],
            'operating_outflow_subtotal': [r'^经营活动现金流出小计$'],
            'operating_net_cash_flow': [r'^经营活动产生的现金流\s*量净\s*额$', r'^经营活动产生的现金流量净额$']
        }

        # 投资活动现金流量项目模式
        self.investing_patterns = {
            'investment_recovery': [r'^收回投资收到的\s*现金$'],
            'investment_income': [r'^取得投资收益收到的\s*现金$'],
            'disposal_assets_cash': [r'^处置固定资产、无形资产和其他长期资产收.*回的\s*现金净额$', r'^处置固定资产、无形资产和其他\s*长期资产收.*回的\s*现金净额$'],
            'disposal_subsidiary_cash': [r'^处置子公司及其他营业单位收到的\s*现金净额$', r'^处置子公司及其他营业单位收到\s*的\s*现金净额$'],
            'other_investing_inflow': [r'^收到其他与投资活动有关的\s*现金$'],
            'investing_inflow_subtotal': [r'^投资活动现金流入小计$'],
            'purchase_assets_cash': [r'^购建固定资产、无形资产和其他长期资产支.*付的\s*现金$', r'^购建固定资产、无形资产和其他\s*长期资产支.*付的\s*现金$'],
            'investment_payment': [r'^投资支付的\s*现金$'],
            'acquire_subsidiary_cash': [r'^取得子公司及其他营业单位支付的\s*现金净额$', r'^取得子公司及其他营业单位支付\s*的\s*现金净额$'],
            'other_investing_outflow': [r'^支付其他与投资活动有关的\s*现金$'],
            'investing_outflow_subtotal': [r'^投资活动现金流出小计$'],
            'investing_net_cash_flow': [r'^投资活动产生的现金流\s*量净\s*额$', r'^投资活动产生的现金流量净额$']
        }

        # 筹资活动现金流量项目模式
        self.financing_patterns = {
            'investment_received': [r'^吸收投资收到的\s*现金$'],
            'minority_investment': [r'^其中：子公司吸收少数股东投资收到的\s*现金$', r'^其中：子公司吸收少数股东投资\s*收到的\s*现金$'],
            'borrowing_received': [r'^取得借款收到的\s*现金$'],
            'other_financing_inflow': [r'^收到其他与筹资活动有关的\s*现金$'],
            'financing_inflow_subtotal': [r'^筹资活动现金流入小计$'],
            'debt_repayment': [r'^偿还债务支付的\s*现金$'],
            'dividend_interest_payment': [r'^分配股利、利润或偿付利息支付的\s*现金$'],
            'minority_dividend': [r'^其中：子公司支付给少数股东的股利、利润$'],
            'other_financing_outflow': [r'^支付其他与筹资活动有关的\s*现金$'],
            'financing_outflow_subtotal': [r'^筹资活动现金流出小计$'],
            'financing_net_cash_flow': [r'^筹资活动产生的现金流\s*量净\s*额$', r'^筹资活动产生的现金流量净额$']
        }

        # 其他项目模式
        self.other_patterns = {
            'exchange_rate_effect': [r'^四、汇率变动对现金及现金等\s*价物的\s*影响$'],
            'net_increase_cash': [r'^五、现金及现金等价物净增加\s*额$'],
            'beginning_cash_balance': [r'^加：期初现金及现金等价物\s*余额$'],
            'ending_cash_balance': [r'^六、期末现金及现金等价物余\s*额$']
        }

    def parse_cash_flow(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """
        解析合并现金流量表

        Args:
            table_data (List[List[str]]): 表格数据

        Returns:
            Dict[str, Any]: 解析后的结构化数据
        """
        logger.info("开始解析合并现金流量表...")

        # 重置缓存
        self.reset_cache()

        # 初始化结果结构
        result = {
            'report_type': '合并现金流量表',
            'operating_activities': {},
            'investing_activities': {},
            'financing_activities': {},
            'other_items': {},
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
            return result
        else:
            logger.info(f"结构识别成功，置信度: {structure_result['confidence']:.2%}")
            logger.info(f"数据范围: 第{structure_result['start_row']}行 到 第{structure_result['end_row']}行")

        # ========== 步骤2: 提取有效数据范围 ==========
        logger.info("步骤2: 提取有效数据范围...")
        data_to_parse = self.extract_statement_data(table_data, structure_result)
        row_offset = structure_result['start_row']

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

            # 匹配经营活动项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.operating_patterns,
                    result['operating_activities'], result, 'operating_activities'
                )

            # 匹配投资活动项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.investing_patterns,
                    result['investing_activities'], result, 'investing_activities'
                )

            # 匹配筹资活动项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.financing_patterns,
                    result['financing_activities'], result, 'financing_activities'
                )

            # 匹配其他项目
            if not matched:
                matched, _ = self._match_and_store_item_with_name(
                    item_name, values, self.other_patterns,
                    result['other_items'], result, 'other_items'
                )

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

    def validate_cash_flow(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证现金流量表数据的完整性和准确性

        实现三层级验证：
        - 层级1：各活动小计验证（流入小计、流出小计）
        - 层级2：各活动净额验证（流入小计 - 流出小计 = 净额）
        - 层级3：现金净增加额验证（三大活动净额 + 汇率影响 = 现金净增加额）

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
                'level2_net_flow_checks': [],
                'level3_total_checks': []
            },
            'completeness_score': 0.0
        }

        try:
            tolerance_rate = 0.01  # 1%容差

            # ========== 层级1：小计验证（暂不实现，因为需要所有明细项目） ==========
            # 现金流量表的小计通常是多个项目的加总，需要识别所有明细项目才能验证

            # ========== 层级2：净额验证 ==========
            logger.info("开始层级2验证：各活动净额")

            # 2.1 经营活动净额 = 流入小计 - 流出小计
            operating_inflow = self._get_numeric_value(
                parsed_data.get('operating_activities', {}).get('operating_inflow_subtotal', {}).get('current_period')
            )
            operating_outflow = self._get_numeric_value(
                parsed_data.get('operating_activities', {}).get('operating_outflow_subtotal', {}).get('current_period')
            )
            operating_net = self._get_numeric_value(
                parsed_data.get('operating_activities', {}).get('operating_net_cash_flow', {}).get('current_period')
            )

            if all(v is not None for v in [operating_inflow, operating_outflow, operating_net]):
                calculated = operating_inflow - operating_outflow
                difference = abs(calculated - operating_net)
                tolerance = max(abs(calculated), abs(operating_net)) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '经营活动净额',
                    'formula': '经营活动流入小计 - 经营活动流出小计',
                    'calculated': float(calculated),
                    'reported': float(operating_net),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"经营活动净额验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={operating_net:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_net_flow_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # 2.2 投资活动净额 = 流入小计 - 流出小计
            investing_inflow = self._get_numeric_value(
                parsed_data.get('investing_activities', {}).get('investing_inflow_subtotal', {}).get('current_period')
            )
            investing_outflow = self._get_numeric_value(
                parsed_data.get('investing_activities', {}).get('investing_outflow_subtotal', {}).get('current_period')
            )
            investing_net = self._get_numeric_value(
                parsed_data.get('investing_activities', {}).get('investing_net_cash_flow', {}).get('current_period')
            )

            if all(v is not None for v in [investing_inflow, investing_outflow, investing_net]):
                calculated = investing_inflow - investing_outflow
                difference = abs(calculated - investing_net)
                tolerance = max(abs(calculated), abs(investing_net)) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '投资活动净额',
                    'formula': '投资活动流入小计 - 投资活动流出小计',
                    'calculated': float(calculated),
                    'reported': float(investing_net),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"投资活动净额验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={investing_net:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_net_flow_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # 2.3 筹资活动净额 = 流入小计 - 流出小计
            financing_inflow = self._get_numeric_value(
                parsed_data.get('financing_activities', {}).get('financing_inflow_subtotal', {}).get('current_period')
            )
            financing_outflow = self._get_numeric_value(
                parsed_data.get('financing_activities', {}).get('financing_outflow_subtotal', {}).get('current_period')
            )
            financing_net = self._get_numeric_value(
                parsed_data.get('financing_activities', {}).get('financing_net_cash_flow', {}).get('current_period')
            )

            if all(v is not None for v in [financing_inflow, financing_outflow, financing_net]):
                calculated = financing_inflow - financing_outflow
                difference = abs(calculated - financing_net)
                tolerance = max(abs(calculated), abs(financing_net)) * tolerance_rate
                passed = difference <= tolerance

                level2_result = {
                    'name': '筹资活动净额',
                    'formula': '筹资活动流入小计 - 筹资活动流出小计',
                    'calculated': float(calculated),
                    'reported': float(financing_net),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"筹资活动净额验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={financing_net:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level2_net_flow_checks'].append(level2_result)
                if not passed:
                    validation_result['errors'].append(level2_result['message'])
                    validation_result['is_valid'] = False

            # ========== 层级3：现金净增加额验证 ==========
            logger.info("开始层级3验证：现金净增加额")

            # 3.1 现金净增加额 = 经营活动净额 + 投资活动净额 + 筹资活动净额 + 汇率影响
            exchange_effect = self._get_numeric_value(
                parsed_data.get('other_items', {}).get('exchange_rate_effect', {}).get('current_period')
            )
            net_increase = self._get_numeric_value(
                parsed_data.get('other_items', {}).get('net_increase_cash', {}).get('current_period')
            )

            if all(v is not None for v in [operating_net, investing_net, financing_net, net_increase]):
                calculated = operating_net + investing_net + financing_net
                if exchange_effect is not None:
                    calculated += exchange_effect

                difference = abs(calculated - net_increase)
                tolerance = max(abs(calculated), abs(net_increase)) * tolerance_rate
                passed = difference <= tolerance

                level3_result = {
                    'name': '现金净增加额',
                    'formula': '经营活动净额 + 投资活动净额 + 筹资活动净额 + 汇率影响',
                    'calculated': float(calculated),
                    'reported': float(net_increase),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"现金净增加额验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={net_increase:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level3_total_checks'].append(level3_result)
                if not passed:
                    validation_result['errors'].append(level3_result['message'])
                    validation_result['is_valid'] = False

            # 3.2 期末余额 = 期初余额 + 现金净增加额
            beginning_balance = self._get_numeric_value(
                parsed_data.get('other_items', {}).get('beginning_cash_balance', {}).get('current_period')
            )
            ending_balance = self._get_numeric_value(
                parsed_data.get('other_items', {}).get('ending_cash_balance', {}).get('current_period')
            )

            if all(v is not None for v in [beginning_balance, net_increase, ending_balance]):
                calculated = beginning_balance + net_increase
                difference = abs(calculated - ending_balance)
                tolerance = max(abs(calculated), abs(ending_balance)) * tolerance_rate
                passed = difference <= tolerance

                level3_result = {
                    'name': '期末余额',
                    'formula': '期初余额 + 现金净增加额',
                    'calculated': float(calculated),
                    'reported': float(ending_balance),
                    'difference': float(difference),
                    'tolerance': float(tolerance),
                    'passed': passed,
                    'message': f"期末余额验证{'通过' if passed else '失败'}：计算值={calculated:,.2f}, 报表值={ending_balance:,.2f}, 差额={difference:,.2f}"
                }
                validation_result['balance_check']['level3_total_checks'].append(level3_result)
                if not passed:
                    validation_result['errors'].append(level3_result['message'])
                    validation_result['is_valid'] = False

            # ========== 完整性检查 ==========
            essential_items = [
                'operating_net_cash_flow', 'investing_net_cash_flow', 'financing_net_cash_flow',
                'net_increase_cash', 'ending_cash_balance'
            ]

            found_items = 0
            missing_items = []
            all_items = {}
            all_items.update(parsed_data.get('operating_activities', {}))
            all_items.update(parsed_data.get('investing_activities', {}))
            all_items.update(parsed_data.get('financing_activities', {}))
            all_items.update(parsed_data.get('other_items', {}))

            for item in essential_items:
                if item in all_items:
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
