"""
合并利润表解析器
负责将提取的表格数据解析为标准化的利润表结构
"""
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from .column_analyzer import ColumnAnalyzer, ColumnType

logger = logging.getLogger(__name__)


class IncomeStatementParser:
    """合并利润表解析器"""

    def __init__(self):
        """初始化解析器"""
        # 初始化列结构分析器
        self.column_analyzer = ColumnAnalyzer()

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

        # 重置ColumnAnalyzer缓存，避免跨表格时使用错误的列结构
        self.column_analyzer.reset_cache()

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
            'ordered_items': []
        }

        if not table_data:
            logger.warning("表格数据为空")
            return result

        # 识别表头结构
        header_info = self._identify_header_structure(table_data)
        logger.info(f"识别到的表头结构: {header_info}")

        # 逐行解析数据
        for row_idx, row in enumerate(table_data):
            if not row or len(row) == 0:
                continue

            # 获取项目名称（通常在第一列）
            item_name = row[0].strip() if row[0] else ""
            item_name = item_name.replace('\n', '').replace('\r', '').strip()

            if not item_name:
                continue

            # 提取数值数据
            values = self._extract_values_from_row(row, header_info)

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

            # 检测合并利润表的结束标志
            if re.search(r'法定代表人|主管会计工作负责人|会计机构负责人', item_name):
                logger.info(f"检测到合并利润表结束标志于第{row_idx}行：{item_name}，停止解析")
                break

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
                   f"未匹配项目: {len(result['parsing_info']['unmatched_items'])}")

        return result

    def _identify_header_structure(self, table_data: List[List[str]]) -> Dict[str, int]:
        """
        识别表头结构，确定各列的含义
        使用 ColumnAnalyzer 进行动态列结构识别

        Args:
            table_data (List[List[str]]): 表格数据

        Returns:
            Dict[str, int]: 列索引映射
        """
        header_info = {
            'item_name_col': 0,
            'current_period_col': None,
            'previous_period_col': None,
            'note_col': None
        }

        if not table_data:
            return header_info

        # 使用 ColumnAnalyzer 分析前几行，找到表头
        # 利润表的表头可能在较后的位置（如果前面有资产负债表数据）
        # 所以需要检查更多行，并且优先选择包含"年度"关键字的表头
        best_header_info = None
        best_header_score = 0

        for row_idx, row in enumerate(table_data[:50]):  # 检查前50行
            if not row or len(row) < 2:
                continue

            # 使用 ColumnAnalyzer 分析行结构
            column_map = self.column_analyzer.analyze_row_structure(row, use_cache=False)

            # 如果成功识别出至少2个列类型（包括期末和期初），认为找到了表头
            has_current = ColumnType.CURRENT_PERIOD in column_map
            has_previous = ColumnType.PREVIOUS_PERIOD in column_map

            if has_current and has_previous:
                # 计算表头的质量分数
                score = 0

                # 检查是否包含"年度"关键字（利润表特征）
                row_str = ' '.join([str(cell) for cell in row if cell])
                if '年度' in row_str:
                    score += 10

                # 检查是否包含"项目"关键字
                if '项目' in row_str:
                    score += 5

                # 行号越靠后，分数越高（优先选择后面的表头）
                score += row_idx * 0.1

                if score > best_header_score:
                    best_header_score = score
                    best_header_info = {
                        'item_name_col': column_map.get(ColumnType.ITEM_NAME, 0),
                        'current_period_col': column_map.get(ColumnType.CURRENT_PERIOD),
                        'previous_period_col': column_map.get(ColumnType.PREVIOUS_PERIOD),
                        'note_col': column_map.get(ColumnType.NOTE)
                    }
                    logger.info(f"在第{row_idx}行找到候选表头（分数={score:.1f}）: {best_header_info}")

        if best_header_info:
            header_info = best_header_info
            logger.info(f"最终选择的表头结构: {header_info}")
        elif header_info['current_period_col'] is None:
            logger.warning("未能识别表头结构，将使用默认列索引")

        return header_info

    def _extract_values_from_row(self, row: List[str], header_info: Dict[str, int]) -> Dict[str, str]:
        """
        从行数据中提取数值
        使用 ColumnAnalyzer 进行动态列结构识别，支持跨页列数变化

        Args:
            row (List[str]): 行数据
            header_info (Dict[str, int]): 表头信息

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

            column_map = self.column_analyzer.analyze_row_structure(row)
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
