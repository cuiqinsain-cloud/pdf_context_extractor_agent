"""
财务报表注释提取器
负责从PDF中提取"合并财务报表项目注释"章节的内容
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class ContentExtractor:
    """内容提取辅助类"""

    @staticmethod
    def extract_text_between_titles(
        page_text: str,
        current_title: str,
        next_title: Optional[str] = None
    ) -> str:
        """
        提取两个标题之间的文本内容

        Args:
            page_text: 页面文本
            current_title: 当前标题
            next_title: 下一个标题（如果有）

        Returns:
            str: 提取的文本内容
        """
        lines = page_text.split('\n')
        content_lines = []
        in_content = False

        for line in lines:
            line_stripped = line.strip()

            # 找到当前标题，开始收集内容
            if current_title in line_stripped:
                in_content = True
                continue

            # 如果遇到下一个标题，停止收集
            if next_title and next_title in line_stripped:
                break

            # 收集内容
            if in_content and line_stripped:
                content_lines.append(line_stripped)

        return '\n'.join(content_lines)

    @staticmethod
    def extract_tables_from_page(page: Any) -> List[List[List[str]]]:
        """
        从页面中提取表格

        Args:
            page: PDF页面对象

        Returns:
            List[List[List[str]]]: 表格列表
        """
        try:
            tables = page.extract_tables()
            return tables if tables else []
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
            return []

    @staticmethod
    def is_table_related_to_title(
        table: List[List[str]],
        title: str,
        page_text: str
    ) -> bool:
        """
        判断表格是否与标题相关

        Args:
            table: 表格数据
            title: 标题文本
            page_text: 页面文本

        Returns:
            bool: 是否相关
        """
        # 简单实现：检查表格是否在标题附近
        # TODO: 更智能的关联判断
        return True


class NotesExtractor:
    """财务报表注释提取器"""

    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化注释提取器

        Args:
            llm_config: LLM配置
        """
        self.llm_client = LLMClient(llm_config)
        self.extracted_notes = []  # 存储已提取的注释
        self.last_note_number = 0  # 最后一个注释的序号

    def extract_notes_from_page(
        self,
        page: Any,
        page_num: int,
        previous_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从单页中提取注释内容

        Args:
            page: PDF页面对象
            page_num: 页码
            previous_context: 前一页的上下文信息

        Returns:
            Dict[str, Any]: 提取结果
                {
                    'page_num': int,
                    'notes': List[Dict],  # 本页提取的注释列表
                    'context': Dict,  # 传递给下一页的上下文
                    'success': bool,
                    'error': str  # 如果失败
                }
        """
        logger.info(f"开始提取第 {page_num} 页的注释内容")

        try:
            # 提取页面文本
            page_text = page.extract_text() or ""

            # 1. 使用LLM分析页面，提取标题
            titles = self._extract_titles_with_llm(
                page_text,
                page_num,
                previous_context
            )

            if not titles['success']:
                return {
                    'page_num': page_num,
                    'notes': [],
                    'context': previous_context or {},
                    'success': False,
                    'error': titles.get('error', 'Unknown error')
                }

            # 2. 对每个标题，提取其下的内容
            notes = []
            title_list = titles['titles']

            for i, title_info in enumerate(title_list):
                # 获取下一个标题（如果有）
                next_title_info = title_list[i + 1] if i + 1 < len(title_list) else None

                note = self._extract_note_content(
                    page,
                    page_text,
                    title_info,
                    next_title_info,
                    page_num
                )
                notes.append(note)

            # 3. 更新上下文
            context = self._build_context(notes, previous_context)

            # 4. 校验连续性
            is_continuous = self._validate_continuity(notes, previous_context)
            if not is_continuous:
                logger.warning(f"第 {page_num} 页的注释序号不连续")

            return {
                'page_num': page_num,
                'notes': notes,
                'context': context,
                'success': True,
                'is_continuous': is_continuous
            }

        except Exception as e:
            logger.error(f"提取第 {page_num} 页注释失败: {e}", exc_info=True)
            return {
                'page_num': page_num,
                'notes': [],
                'context': previous_context or {},
                'success': False,
                'error': str(e)
            }

    def _extract_titles_with_llm(
        self,
        page_text: str,
        page_num: int,
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        使用LLM提取页面中的注释标题

        Args:
            page_text: 页面文本
            page_num: 页码
            previous_context: 前一页的上下文

        Returns:
            Dict[str, Any]: 提取结果
                {
                    'success': bool,
                    'titles': List[Dict],  # 标题列表
                    'error': str  # 如果失败
                }
        """
        # 构建提示词
        system_prompt = self._build_title_extraction_system_prompt()
        user_prompt = self._build_title_extraction_user_prompt(
            page_text,
            page_num,
            previous_context
        )

        # 调用LLM
        try:
            result = self._call_llm_for_title_extraction(
                system_prompt,
                user_prompt
            )
            return result
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            return {
                'success': False,
                'titles': [],
                'error': str(e)
            }

    def _build_title_extraction_system_prompt(self) -> str:
        """构建标题提取的系统提示词"""
        return """你是一个专业的财务报表分析专家，擅长从中国A股上市公司年报的"合并财务报表项目注释"章节中提取标题结构。

你的任务是：
1. 识别页面中的所有注释标题（主标题和子标题）
2. 提取标题的序号、层级和文本内容
3. 判断标题的完整性和连续性

标题格式特征：
- 主标题格式：`数字、 标题名称`，如 "1、 货币资金"、"2、 交易性金融资产"
- 子标题格式：`(数字) 子标题名称` 或 `（数字） 子标题名称`，如 "(1). 应收票据分类列示"
- 标题序号是连续递增的

重要提示：
1. 注意区分标题和普通文本（如表格数据、说明文字等）
2. 标题通常独立成行，不包含大量数字
3. 需要识别标题的层级关系（主标题、子标题）
4. 如果标题跨页，需要标注出来

请仔细分析页面内容，准确提取所有标题。"""

    def _build_title_extraction_user_prompt(
        self,
        page_text: str,
        page_num: int,
        previous_context: Optional[Dict[str, Any]]
    ) -> str:
        """构建标题提取的用户提示词"""
        # 构建上下文信息
        context_info = ""
        if previous_context and 'last_title' in previous_context:
            last_title = previous_context['last_title']
            context_info = f"""
上一页的最后一个标题：
- 序号: {last_title.get('number', 'N/A')}
- 层级: {last_title.get('level', 'N/A')}
- 文本: {last_title.get('text', 'N/A')}
- 是否完整: {last_title.get('is_complete', True)}
"""

        # 限制页面内容长度，只取前2000字符
        # 并且只保留可能是标题的行（以数字或括号开头的行）
        lines = page_text.split('\n')
        filtered_lines = []
        for line in lines[:100]:  # 只看前100行
            line_stripped = line.strip()
            # 保留可能是标题的行
            if line_stripped and (
                line_stripped[0].isdigit() or
                (line_stripped.startswith('(') and len(line_stripped) > 2 and line_stripped[1].isdigit()) or
                (line_stripped.startswith('（') and len(line_stripped) > 2 and line_stripped[1].isdigit())
            ):
                filtered_lines.append(line_stripped)

        # 如果过滤后的行太少，就使用原始文本的前1500字符
        if len(filtered_lines) < 5:
            page_content = page_text[:1500]
        else:
            page_content = '\n'.join(filtered_lines[:30])  # 最多30行

        prompt = f"""请分析第 {page_num} 页的内容，提取所有注释标题。

{context_info}

页面内容（已过滤，只显示可能的标题行）：
{page_content}

请以JSON格式返回结果（不要包含任何其他文字说明）：
{{
  "titles": [
    {{
      "number": "1",
      "level": 1,
      "text": "货币资金",
      "full_text": "1、 货币资金",
      "position": 0,
      "is_complete": true,
      "has_content": true
    }}
  ],
  "has_continuation": false,
  "continuation_number": null,
  "reasoning": "简要分析理由"
}}

注意：
1. 准确识别标题的序号和层级
2. 主标题格式：数字、 标题名称（如"1、 货币资金"）
3. 子标题格式：(数字) 或 （数字） 开头
4. 按照在页面中出现的顺序排列标题"""

        return prompt

    def _call_llm_for_title_extraction(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """
        调用LLM进行标题提取

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            Dict[str, Any]: LLM返回结果
        """
        # 使用LLMClient的通用调用方法
        result = self.llm_client.call_llm(user_prompt, system_prompt)

        if result['success']:
            # 解析返回的JSON
            try:
                content = result.get('content', '')

                # 移除可能的 markdown 代码块标记
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                elif content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()

                data = json.loads(content)
                return {
                    'success': True,
                    'titles': data.get('titles', []),
                    'has_continuation': data.get('has_continuation', False),
                    'continuation_number': data.get('continuation_number'),
                    'reasoning': data.get('reasoning', '')
                }
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始内容: {content}")
                return {
                    'success': False,
                    'titles': [],
                    'error': f'JSON parse error: {e}'
                }
        else:
            return {
                'success': False,
                'titles': [],
                'error': result.get('error', 'Unknown error')
            }

    def _extract_note_content(
        self,
        page: Any,
        page_text: str,
        title_info: Dict[str, Any],
        next_title_info: Optional[Dict[str, Any]],
        page_num: int
    ) -> Dict[str, Any]:
        """
        提取注释标题下的内容

        Args:
            page: PDF页面对象
            page_text: 页面文本
            title_info: 标题信息
            next_title_info: 下一个标题信息（如果有）
            page_num: 页码

        Returns:
            Dict[str, Any]: 注释内容
        """
        current_title = title_info.get('full_text', '')
        next_title = next_title_info.get('full_text') if next_title_info else None

        # 1. 提取文本内容
        text_content = ContentExtractor.extract_text_between_titles(
            page_text,
            current_title,
            next_title
        )

        # 2. 提取表格
        tables = ContentExtractor.extract_tables_from_page(page)

        # 3. 筛选与当前标题相关的表格
        related_tables = []
        for table in tables:
            if ContentExtractor.is_table_related_to_title(table, current_title, page_text):
                related_tables.append(table)

        # 4. 构建结果
        return {
            'number': title_info.get('number'),
            'level': title_info.get('level'),
            'title': title_info.get('text'),
            'full_title': title_info.get('full_text'),
            'page_num': page_num,
            'content': {
                'text': text_content,
                'tables': related_tables,
                'table_count': len(related_tables)
            },
            'has_table': len(related_tables) > 0,
            'is_complete': title_info.get('is_complete', True)
        }

    def _build_context(
        self,
        notes: List[Dict[str, Any]],
        previous_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        构建传递给下一页的上下文

        Args:
            notes: 本页提取的注释列表
            previous_context: 前一页的上下文

        Returns:
            Dict[str, Any]: 新的上下文
        """
        context = previous_context.copy() if previous_context else {}

        if notes:
            # 记录最后一个标题
            last_note = notes[-1]
            context['last_title'] = {
                'number': last_note.get('number'),
                'level': last_note.get('level'),
                'text': last_note.get('title'),
                'is_complete': last_note.get('is_complete', True)
            }

            # 更新已提取的注释数量
            context['total_notes'] = context.get('total_notes', 0) + len(notes)

        return context

    def _validate_continuity(
        self,
        notes: List[Dict[str, Any]],
        previous_context: Optional[Dict[str, Any]]
    ) -> bool:
        """
        校验注释序号的连续性

        Args:
            notes: 本页提取的注释列表
            previous_context: 前一页的上下文

        Returns:
            bool: 是否连续
        """
        if not notes:
            return True

        # 获取上一页的最后一个序号
        expected_number = 1
        if previous_context and 'last_title' in previous_context:
            last_number = previous_context['last_title'].get('number', '0')
            try:
                expected_number = int(last_number) + 1
            except ValueError:
                logger.warning(f"无法解析上一页的序号: {last_number}")

        # 检查第一个注释的序号
        first_note = notes[0]
        first_number = first_note.get('number', '0')

        try:
            actual_number = int(first_number)
            return actual_number == expected_number
        except ValueError:
            logger.warning(f"无法解析当前页的序号: {first_number}")
            return False

    def extract_notes_from_pages(
        self,
        pages: List[Any],
        start_page_num: int
    ) -> Dict[str, Any]:
        """
        从多个页面中提取注释

        Args:
            pages: 页面对象列表
            start_page_num: 起始页码

        Returns:
            Dict[str, Any]: 提取结果
        """
        all_notes = []
        context = None
        errors = []

        for i, page in enumerate(pages):
            page_num = start_page_num + i

            result = self.extract_notes_from_page(
                page,
                page_num,
                context
            )

            if result['success']:
                all_notes.extend(result['notes'])
                context = result['context']

                if not result.get('is_continuous', True):
                    errors.append(f"第 {page_num} 页序号不连续")
            else:
                errors.append(f"第 {page_num} 页提取失败: {result.get('error')}")

        return {
            'success': len(errors) == 0,
            'notes': all_notes,
            'total_pages': len(pages),
            'total_notes': len(all_notes),
            'errors': errors
        }
