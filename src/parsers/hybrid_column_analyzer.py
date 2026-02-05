"""
混合列分析器
整合规则匹配和 LLM 智能识别
"""
import logging
from typing import Dict, Any, List
from src.parsers.column_analyzer import ColumnAnalyzer, ColumnType
from src.parsers.llm_client import LLMClient
from src.parsers.result_comparator import ResultComparator
from src.parsers.user_choice_handler import UserChoiceHandler
from src.parsers.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class HybridColumnAnalyzer:
    """混合列分析器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化混合分析器

        Args:
            config: 配置字典，如果为 None 则从配置文件加载
        """
        # 加载配置
        if config is None:
            config_loader = ConfigLoader()
            config = config_loader.load_config()

        self.config = config

        # 初始化组件
        self.rule_analyzer = ColumnAnalyzer()
        self.llm_settings = config.get('llm_settings', {})
        self.enable_llm = self.llm_settings.get('enable_llm', False)
        self.enable_comparison = self.llm_settings.get('enable_comparison', True)
        self.enable_user_choice = self.llm_settings.get('enable_user_choice', True)
        self.auto_accept_if_match = self.llm_settings.get('auto_accept_if_match', True)
        self.always_use_llm = self.llm_settings.get('always_use_llm', False)
        self.fallback_to_rules = self.llm_settings.get('fallback_to_rules', True)

        # 初始化 LLM 客户端
        if self.enable_llm:
            try:
                llm_api_config = config.get('llm_api', {})
                self.llm_client = LLMClient(llm_api_config)
                logger.info("LLM 客户端初始化成功")
            except Exception as e:
                logger.error(f"LLM 客户端初始化失败: {e}")
                self.llm_client = None
                if not self.fallback_to_rules:
                    raise
        else:
            self.llm_client = None
            logger.info("LLM 功能未启用")

        # 初始化对比器和用户选择处理器
        self.comparator = ResultComparator()
        self.choice_handler = UserChoiceHandler(
            save_choices=self.llm_settings.get('save_choices', True),
            choices_log_path=self.llm_settings.get('choices_log_path', 'logs/user_choices.json')
        )

        # 列模式缓存
        self.column_pattern_cache = None

    def analyze_row_structure(self, row: List[str],
                             use_cache: bool = True) -> Dict[ColumnType, int]:
        """
        分析单行的列结构（混合模式）

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

        # 执行混合分析
        result = self._analyze_with_hybrid(row)

        # 更新缓存
        if result:
            self.column_pattern_cache = result
            logger.info(f"更新列模式缓存: {result}")

        return result

    def _analyze_with_hybrid(self, row: List[str]) -> Dict[ColumnType, int]:
        """
        使用混合模式分析行结构

        Args:
            row: 行数据

        Returns:
            Dict[ColumnType, int]: 列类型到列索引的映射
        """
        # 步骤1：规则匹配
        rule_result = self.rule_analyzer.analyze_row_structure(row, use_cache=False)
        logger.info(f"规则匹配结果: {rule_result}")

        # 如果未启用 LLM，直接返回规则结果
        if not self.enable_llm or self.llm_client is None:
            return rule_result

        # 如果不是总是使用 LLM，且规则结果置信度高，可以跳过 LLM
        if not self.always_use_llm and self._is_rule_result_confident(rule_result, row):
            logger.info("规则匹配结果置信度高，跳过 LLM 调用")
            return rule_result

        # 步骤2：LLM 识别
        try:
            llm_response = self.llm_client.analyze_header(row)

            if not llm_response['success']:
                logger.warning(f"LLM 调用失败: {llm_response.get('error')}")
                if self.fallback_to_rules:
                    logger.info("回退到规则匹配结果")
                    return rule_result
                else:
                    return {}

            llm_result = llm_response['column_map']
            llm_confidence = llm_response['confidence']
            llm_reasoning = llm_response.get('reasoning', '')

            logger.info(f"LLM识别结果: {llm_result} (置信度: {llm_confidence})")

        except Exception as e:
            logger.error(f"LLM 调用异常: {e}")
            if self.fallback_to_rules:
                logger.info("回退到规则匹配结果")
                return rule_result
            else:
                return {}

        # 步骤3：结果对比
        if self.enable_comparison:
            comparison = self.comparator.compare(rule_result, llm_result, row)

            # 如果结果严格一致，自动使用规则结果
            if comparison['is_match']:
                if self.auto_accept_if_match:
                    logger.info("✓ 结果一致，自动使用规则结果")
                    return rule_result

            # 如果结果不一致，需要用户选择
            else:
                if self.enable_user_choice:
                    choice = self.choice_handler.prompt_user_choice(
                        comparison, llm_confidence, llm_reasoning
                    )

                    if choice == 'rules':
                        return rule_result
                    elif choice == 'llm':
                        # 将 LLM 结果转换为 ColumnType 键
                        return self._convert_llm_result_to_column_type(llm_result)
                    else:  # skip
                        logger.warning("用户选择跳过，返回空结果")
                        return {}
                else:
                    # 如果不启用用户选择，默认使用规则结果
                    logger.warning("结果不一致但未启用用户选择，默认使用规则结果")
                    return rule_result
        else:
            # 如果不启用对比，直接使用规则结果
            return rule_result

        return rule_result

    def _is_rule_result_confident(self, rule_result: Dict[ColumnType, int],
                                  row: List[str]) -> bool:
        """
        判断规则匹配结果是否置信度高

        Args:
            rule_result: 规则匹配结果
            row: 行数据

        Returns:
            bool: 是否置信度高
        """
        # 如果识别出了关键列（项目名称、本期、上期），认为置信度高
        required_columns = {
            ColumnType.ITEM_NAME,
            ColumnType.CURRENT_PERIOD,
            ColumnType.PREVIOUS_PERIOD
        }

        identified_columns = set(rule_result.keys())

        # 如果识别出所有关键列，认为置信度高
        if required_columns.issubset(identified_columns):
            return True

        return False

    def _convert_llm_result_to_column_type(self,
                                          llm_result: Dict[str, int]) -> Dict[ColumnType, int]:
        """
        将 LLM 结果转换为 ColumnType 键

        Args:
            llm_result: LLM 结果 {'column_type': 列索引}

        Returns:
            Dict[ColumnType, int]: 转换后的结果
        """
        type_mapping = {
            'item_name': ColumnType.ITEM_NAME,
            'current_period': ColumnType.CURRENT_PERIOD,
            'previous_period': ColumnType.PREVIOUS_PERIOD,
            'note': ColumnType.NOTE
        }

        converted = {}
        for key, value in llm_result.items():
            if key in type_mapping:
                converted[type_mapping[key]] = value
            else:
                logger.warning(f"未知的列类型: {key}")

        return converted

    def _validate_cached_pattern(self, row: List[str],
                                cached_pattern: Dict[ColumnType, int]) -> bool:
        """
        验证缓存的列模式是否仍然有效

        Args:
            row: 当前行数据
            cached_pattern: 缓存的列模式

        Returns:
            bool: 是否有效
        """
        # 检查列数是否变化
        max_col_idx = max(cached_pattern.values()) if cached_pattern else -1
        if max_col_idx >= len(row):
            logger.debug("列数变化，缓存失效")
            return False

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            'enable_llm': self.enable_llm,
            'enable_comparison': self.enable_comparison,
            'enable_user_choice': self.enable_user_choice
        }

        if self.enable_user_choice:
            choice_stats = self.choice_handler.get_choice_statistics()
            stats['user_choices'] = choice_stats

        return stats
