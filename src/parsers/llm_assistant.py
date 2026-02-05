"""
LLM辅助模块
用于处理不确定的表头识别和列结构分析
"""
import logging
from typing import List, Dict, Optional, Any
import json

logger = logging.getLogger(__name__)


class LLMAssistant:
    """LLM辅助分析器"""

    def __init__(self, enable_llm: bool = False):
        """
        初始化LLM辅助器

        Args:
            enable_llm: 是否启用LLM辅助（默认关闭，避免额外成本）
        """
        self.enable_llm = enable_llm
        self.confidence_threshold = 0.7  # 置信度阈值，低于此值时调用LLM

    def analyze_header_with_llm(self, header_row: List[str]) -> Dict[str, Any]:
        """
        使用LLM分析表头结构

        Args:
            header_row: 表头行数据

        Returns:
            Dict[str, Any]: 分析结果，包含列类型映射和置信度
        """
        if not self.enable_llm:
            logger.debug("LLM辅助未启用")
            return {'column_map': {}, 'confidence': 0.0, 'used_llm': False}

        logger.info(f"调用LLM分析表头: {header_row}")

        # 构建提示词
        prompt = self._build_header_analysis_prompt(header_row)

        # 调用LLM（这里需要集成实际的LLM API）
        try:
            result = self._call_llm(prompt)
            return {
                'column_map': result.get('column_map', {}),
                'confidence': result.get('confidence', 0.0),
                'used_llm': True,
                'reasoning': result.get('reasoning', '')
            }
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return {'column_map': {}, 'confidence': 0.0, 'used_llm': False, 'error': str(e)}

    def _build_header_analysis_prompt(self, header_row: List[str]) -> str:
        """
        构建表头分析的提示词

        Args:
            header_row: 表头行数据

        Returns:
            str: 提示词
        """
        prompt = f"""
你是一个财务报表分析专家。请分析以下表头行，识别每一列的类型。

表头行数据：
{json.dumps(header_row, ensure_ascii=False, indent=2)}

列类型包括：
- item_name: 项目名称/科目
- current_period: 期末/本期末/本年末
- previous_period: 期初/上期末/上年末
- note: 附注/注释
- unknown: 未知

请返回JSON格式的结果：
{{
    "column_map": {{
        "item_name": 列索引,
        "current_period": 列索引,
        "previous_period": 列索引,
        "note": 列索引
    }},
    "confidence": 0.0-1.0之间的置信度,
    "reasoning": "分析理由"
}}

注意：
1. 列索引从0开始
2. 如果某个列类型不存在，不要包含在column_map中
3. 期末列通常在期初列之前
4. 项目名称列通常是第一列
"""
        return prompt

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        调用LLM API

        Args:
            prompt: 提示词

        Returns:
            Dict[str, Any]: LLM返回结果
        """
        # TODO: 集成实际的LLM API
        # 这里可以使用 Anthropic API、OpenAI API 等

        # 示例实现（需要替换为实际API调用）
        logger.warning("LLM API未实现，返回空结果")

        # 伪代码示例：
        # import anthropic
        # client = anthropic.Anthropic(api_key="your-api-key")
        # message = client.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     max_tokens=1024,
        #     messages=[{"role": "user", "content": prompt}]
        # )
        # response_text = message.content[0].text
        # return json.loads(response_text)

        return {
            'column_map': {},
            'confidence': 0.0,
            'reasoning': 'LLM API未实现'
        }

    def validate_column_mapping(self, row: List[str],
                               column_map: Dict[str, int],
                               confidence: float) -> bool:
        """
        验证列映射的合理性

        Args:
            row: 行数据
            column_map: 列映射
            confidence: 置信度

        Returns:
            bool: 是否通过验证
        """
        # 验证1：置信度检查
        if confidence < self.confidence_threshold:
            logger.warning(f"置信度过低: {confidence} < {self.confidence_threshold}")
            return False

        # 验证2：列索引范围检查
        for col_type, col_idx in column_map.items():
            if col_idx < 0 or col_idx >= len(row):
                logger.warning(f"列索引超出范围: {col_type}={col_idx}, 行长度={len(row)}")
                return False

        # 验证3：逻辑检查
        if 'current_period' in column_map and 'previous_period' in column_map:
            if column_map['current_period'] > column_map['previous_period']:
                logger.warning("期末列在期初列之后，可能有误")
                return False

        return True

    def suggest_keywords(self, cell_text: str, column_type: str) -> List[str]:
        """
        建议新的关键字（用于扩展关键字库）

        Args:
            cell_text: 单元格文本
            column_type: 列类型

        Returns:
            List[str]: 建议的关键字列表
        """
        if not self.enable_llm:
            return []

        logger.info(f"请求LLM建议关键字: 文本='{cell_text}', 类型={column_type}")

        prompt = f"""
你是一个财务报表分析专家。请为以下单元格文本建议可以用于识别"{column_type}"列的关键字。

单元格文本: "{cell_text}"
列类型: {column_type}

请返回JSON格式的关键字列表（正则表达式格式）：
{{
    "keywords": ["关键字1", "关键字2", ...]
}}

要求：
1. 关键字应该是正则表达式格式
2. 关键字应该具有一定的通用性
3. 最多返回3个关键字
"""

        try:
            result = self._call_llm(prompt)
            keywords = result.get('keywords', [])
            logger.info(f"LLM建议的关键字: {keywords}")
            return keywords
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return []


class KeywordLibrary:
    """关键字库管理器"""

    def __init__(self, library_path: Optional[str] = None):
        """
        初始化关键字库

        Args:
            library_path: 关键字库文件路径（JSON格式）
        """
        self.library_path = library_path
        self.keywords = self._load_library()

    def _load_library(self) -> Dict[str, List[str]]:
        """
        加载关键字库

        Returns:
            Dict[str, List[str]]: 关键字库
        """
        # 默认关键字库
        default_keywords = {
            'item_name': [
                r'项目', r'科目', r'会计科目', r'资产', r'负债', r'所有者权益'
            ],
            'current_period': [
                r'期末', r'本期末', r'本年末', r'本期', r'2024年.*期末',
                r'2024年.*12月.*31日', r'当期', r'本年', r'年末余额'
            ],
            'previous_period': [
                r'期初', r'上期末', r'上年末', r'上期', r'2023年.*期末',
                r'2023年.*12月.*31日', r'上年', r'年初余额'
            ],
            'note': [
                r'附注', r'注释', r'注', r'备注'
            ]
        }

        # 如果有自定义库文件，加载并合并
        if self.library_path:
            try:
                import json
                with open(self.library_path, 'r', encoding='utf-8') as f:
                    custom_keywords = json.load(f)
                    # 合并关键字
                    for key, values in custom_keywords.items():
                        if key in default_keywords:
                            default_keywords[key].extend(values)
                        else:
                            default_keywords[key] = values
                logger.info(f"加载自定义关键字库: {self.library_path}")
            except Exception as e:
                logger.warning(f"加载自定义关键字库失败: {e}")

        return default_keywords

    def add_keyword(self, column_type: str, keyword: str):
        """
        添加新关键字

        Args:
            column_type: 列类型
            keyword: 关键字（正则表达式）
        """
        if column_type not in self.keywords:
            self.keywords[column_type] = []

        if keyword not in self.keywords[column_type]:
            self.keywords[column_type].append(keyword)
            logger.info(f"添加新关键字: {column_type} -> {keyword}")

    def save_library(self):
        """保存关键字库到文件"""
        if not self.library_path:
            logger.warning("未指定关键字库文件路径，无法保存")
            return

        try:
            import json
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
            logger.info(f"关键字库已保存: {self.library_path}")
        except Exception as e:
            logger.error(f"保存关键字库失败: {e}")

    def get_keywords(self, column_type: str) -> List[str]:
        """
        获取指定列类型的关键字

        Args:
            column_type: 列类型

        Returns:
            List[str]: 关键字列表
        """
        return self.keywords.get(column_type, [])
