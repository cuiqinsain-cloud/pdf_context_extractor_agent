"""
优化版注释提取器 - 批量处理
通过批量处理多页内容，减少LLM调用次数，提升效率
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class BatchNotesExtractor:
    """批量注释提取器 - 优化版"""

    def __init__(self, llm_config: Dict[str, Any], batch_size: int = 5):
        """
        初始化批量提取器

        Args:
            llm_config: LLM配置
            batch_size: 批量处理的页数（默认5页）
        """
        self.llm_client = LLMClient(llm_config)
        self.batch_size = batch_size

    def extract_notes_from_pages_batch(
        self,
        pages: List[Any],
        start_page_num: int
    ) -> Dict[str, Any]:
        """
        批量提取注释（优化版）

        Args:
            pages: 页面对象列表
            start_page_num: 起始页码

        Returns:
            Dict[str, Any]: 提取结果
        """
        all_notes = []
        errors = []
        total_pages = len(pages)

        # 分批处理
        for batch_start in range(0, total_pages, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_pages)
            batch_pages = pages[batch_start:batch_end]
            batch_page_nums = list(range(
                start_page_num + batch_start,
                start_page_num + batch_end
            ))

            logger.info(
                f"处理批次: 第 {batch_page_nums[0]} - {batch_page_nums[-1]} 页 "
                f"({len(batch_pages)} 页)"
            )

            try:
                # 批量提取标题
                batch_result = self._extract_batch_titles(
                    batch_pages,
                    batch_page_nums
                )

                if batch_result['success']:
                    # 提取内容
                    for note_info in batch_result['notes']:
                        page_idx = note_info['page_num'] - start_page_num
                        page = pages[page_idx]

                        # 提取内容
                        note = self._extract_note_content(
                            page,
                            note_info
                        )
                        all_notes.append(note)
                else:
                    errors.append(
                        f"批次 {batch_page_nums[0]}-{batch_page_nums[-1]} "
                        f"提取失败: {batch_result.get('error')}"
                    )

            except Exception as e:
                logger.error(f"批次处理失败: {e}", exc_info=True)
                errors.append(
                    f"批次 {batch_page_nums[0]}-{batch_page_nums[-1]} "
                    f"处理异常: {str(e)}"
                )

        return {
            'success': len(errors) == 0,
            'notes': all_notes,
            'total_pages': total_pages,
            'total_notes': len(all_notes),
            'errors': errors
        }

    def _extract_batch_titles(
        self,
        pages: List[Any],
        page_nums: List[int]
    ) -> Dict[str, Any]:
        """
        批量提取多页的标题

        Args:
            pages: 页面对象列表
            page_nums: 页码列表

        Returns:
            Dict[str, Any]: 提取结果
        """
        # 收集所有页面的内容
        pages_content = []
        for i, page in enumerate(pages):
            page_num = page_nums[i]
            text = page.extract_text() or ""

            # 过滤标题行
            lines = text.split('\n')
            filtered_lines = []
            for line in lines[:100]:
                line_stripped = line.strip()
                if line_stripped and (
                    line_stripped[0].isdigit() or
                    (line_stripped.startswith('(') and len(line_stripped) > 2 and line_stripped[1].isdigit()) or
                    (line_stripped.startswith('（') and len(line_stripped) > 2 and line_stripped[1].isdigit())
                ):
                    filtered_lines.append(line_stripped)

            pages_content.append({
                'page_num': page_num,
                'content': '\n'.join(filtered_lines[:20]) if filtered_lines else text[:500]
            })

        # 构建批量提示词
        system_prompt = self._build_batch_system_prompt()
        user_prompt = self._build_batch_user_prompt(pages_content)

        # 调用LLM
        try:
            result = self.llm_client.call_llm(user_prompt, system_prompt)

            if result['success']:
                # 解析返回的JSON
                content = result.get('content', '')

                # 移除markdown代码块标记
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
                    'notes': data.get('notes', []),
                    'reasoning': data.get('reasoning', '')
                }
            else:
                return {
                    'success': False,
                    'notes': [],
                    'error': result.get('error', 'Unknown error')
                }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始内容: {content}")
            return {
                'success': False,
                'notes': [],
                'error': f'JSON parse error: {e}'
            }
        except Exception as e:
            logger.error(f"批量提取失败: {e}", exc_info=True)
            return {
                'success': False,
                'notes': [],
                'error': str(e)
            }

    def _build_batch_system_prompt(self) -> str:
        """构建批量处理的系统提示词"""
        return """你是一个专业的财务报表分析专家，擅长从中国A股上市公司年报的"合并财务报表项目注释"章节中提取标题结构。

你的任务是：
1. 分析多个页面的内容，识别所有注释标题
2. 提取标题的序号、层级、文本内容和所在页码
3. 保持标题的连续性和完整性

标题格式特征：
- 主标题：数字、 标题名称（如"1、 货币资金"）
- 子标题：(数字) 或 （数字） 开头（如"(1). 应收票据分类列示"）

重要提示：
1. 准确识别每个标题所在的页码
2. 标题序号通常是连续递增的
3. 区分标题和普通文本（表格数据、说明文字等）"""

    def _build_batch_user_prompt(
        self,
        pages_content: List[Dict[str, Any]]
    ) -> str:
        """构建批量处理的用户提示词"""
        # 构建页面内容描述
        pages_desc = []
        for page_info in pages_content:
            pages_desc.append(
                f"=== 第 {page_info['page_num']} 页 ===\n"
                f"{page_info['content']}\n"
            )

        pages_text = '\n'.join(pages_desc)

        prompt = f"""请分析以下 {len(pages_content)} 个页面的内容，提取所有注释标题。

{pages_text}

请以JSON格式返回结果（不要包含任何其他文字说明）：
{{
  "notes": [
    {{
      "number": "1",
      "level": 1,
      "title": "货币资金",
      "full_title": "1、 货币资金",
      "page_num": 125
    }},
    {{
      "number": "1",
      "level": 2,
      "title": "应收票据分类列示",
      "full_title": "(1). 应收票据分类列示",
      "page_num": 126
    }}
  ],
  "reasoning": "简要分析理由"
}}

注意：
1. 准确标注每个标题所在的页码
2. 按照页码和出现顺序排列
3. 主标题level=1，子标题level=2"""

        return prompt

    def _extract_note_content(
        self,
        page: Any,
        note_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提取注释内容（简化版）

        Args:
            page: PDF页面对象
            note_info: 标题信息

        Returns:
            Dict[str, Any]: 注释内容
        """
        # 提取表格
        try:
            tables = page.extract_tables()
            tables = tables if tables else []
        except Exception as e:
            logger.error(f"提取表格失败: {e}")
            tables = []

        # 提取文本
        page_text = page.extract_text() or ""
        current_title = note_info.get('full_title', '')

        # 简单提取：标题后的内容
        lines = page_text.split('\n')
        content_lines = []
        found_title = False

        for line in lines:
            if current_title in line:
                found_title = True
                continue
            if found_title and line.strip():
                content_lines.append(line.strip())
                if len(content_lines) >= 10:  # 只取前10行
                    break

        text_content = '\n'.join(content_lines)

        return {
            'number': note_info.get('number'),
            'level': note_info.get('level'),
            'title': note_info.get('title'),
            'full_title': note_info.get('full_title'),
            'page_num': note_info.get('page_num'),
            'content': {
                'text': text_content,
                'tables': tables,
                'table_count': len(tables)
            },
            'has_table': len(tables) > 0,
            'is_complete': True
        }
