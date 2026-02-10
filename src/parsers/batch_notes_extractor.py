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
                    # 按页面分组注释
                    notes_by_page = {}
                    for note_info in batch_result['notes']:
                        page_num = note_info['page_num']
                        if page_num not in notes_by_page:
                            notes_by_page[page_num] = []
                        notes_by_page[page_num].append(note_info)

                    # 提取内容（传入同一页面的所有注释）
                    for page_num, page_notes in notes_by_page.items():
                        page_idx = page_num - start_page_num
                        page = pages[page_idx]

                        # 提取该页面所有注释的内容
                        extracted_notes = self._extract_page_notes_content(
                            page,
                            page_notes
                        )
                        all_notes.extend(extracted_notes)
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

    def _extract_page_notes_content(
        self,
        page: Any,
        page_notes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        提取一个页面上所有注释的内容（基于位置的智能分配）

        Args:
            page: PDF页面对象
            page_notes: 该页面上的所有注释信息

        Returns:
            List[Dict[str, Any]]: 提取的注释列表
        """
        # 分离一级和二级标题
        level1_notes = [n for n in page_notes if n['level'] == 1]
        level2_notes = [n for n in page_notes if n['level'] == 2]

        # 按页面上的位置排序一级标题（从上到下）
        sorted_level1 = sorted(level1_notes, key=lambda n: self._find_title_position(page, n['full_title']))

        # 提取页面上所有表格及其位置
        tables_with_positions = self._extract_tables_with_positions(page)

        # 为每个一级注释分配表格
        result_notes = []

        for i, note_info in enumerate(sorted_level1):
            # 获取当前一级注释的位置
            current_pos = self._find_title_position(page, note_info['full_title'])

            # 获取下一个一级注释的位置（如果存在）
            next_level1_pos = None
            if i < len(sorted_level1) - 1:
                next_level1_pos = self._find_title_position(page, sorted_level1[i + 1]['full_title'])

            # 查找属于当前一级注释的二级标题
            # 二级标题的编号应该以一级标题的编号开头（但LLM可能没有正确设置）
            # 所以我们使用位置来判断
            note_level2_children = []
            for level2_note in level2_notes:
                level2_pos = self._find_title_position(page, level2_note['full_title'])
                logger.debug(f"检查二级标题: {level2_note['full_title'][:30]} 位置: {level2_pos:.1f}")
                # 二级标题必须在当前一级标题之后
                if level2_pos < current_pos:
                    logger.debug(f"  -> 跳过（在一级标题之前）")
                    continue
                # 如果有下一个一级标题，二级标题必须在它之前
                if next_level1_pos is not None and level2_pos >= next_level1_pos:
                    logger.debug(f"  -> 跳过（在下一个一级标题之后）")
                    continue
                logger.debug(f"  -> 接受（属于当前一级标题）")
                note_level2_children.append((level2_note, level2_pos))

            # 按位置排序二级标题
            note_level2_children.sort(key=lambda x: x[1])

            # 为一级标题和其二级子项分配表格
            # 如果有二级子项，表格应该分配给子项而不是父项
            if note_level2_children:
                # 一级标题本身不分配表格（表格属于子项）
                text_content = self._extract_note_text(page, note_info, note_level2_children[0][1] if note_level2_children else next_level1_pos)

                note = {
                    'number': note_info.get('number'),
                    'level': note_info.get('level'),
                    'title': note_info.get('title'),
                    'full_title': note_info.get('full_title'),
                    'page_num': note_info.get('page_num'),
                    'content': {
                        'text': text_content,
                        'tables': [],  # 一级标题不包含表格
                        'table_count': 0
                    },
                    'has_table': False,
                    'is_complete': True
                }
                result_notes.append(note)

                # 为每个二级子项分配表格
                for j, (level2_note, level2_pos) in enumerate(note_level2_children):
                    # 获取下一个二级标题的位置
                    next_level2_pos = None
                    if j < len(note_level2_children) - 1:
                        next_level2_pos = note_level2_children[j + 1][1]
                    else:
                        # 最后一个二级标题，边界是下一个一级标题
                        next_level2_pos = next_level1_pos

                    logger.debug(f"为二级标题分配表格: {level2_note['full_title'][:30]}")
                    logger.debug(f"  位置范围: {level2_pos:.1f} - {next_level2_pos if next_level2_pos else 'None'}")

                    # 分配表格
                    level2_tables = self._assign_tables_to_note(
                        tables_with_positions,
                        level2_pos,
                        next_level2_pos
                    )

                    logger.debug(f"  分配到 {len(level2_tables)} 个表格")

                    # 提取文本
                    level2_text = self._extract_note_text(page, level2_note, next_level2_pos)

                    level2_result = {
                        'number': level2_note.get('number'),
                        'level': level2_note.get('level'),
                        'title': level2_note.get('title'),
                        'full_title': level2_note.get('full_title'),
                        'page_num': level2_note.get('page_num'),
                        'content': {
                            'text': level2_text,
                            'tables': level2_tables,
                            'table_count': len(level2_tables)
                        },
                        'has_table': len(level2_tables) > 0,
                        'is_complete': True
                    }
                    result_notes.append(level2_result)

            else:
                # 没有二级子项，直接为一级标题分配表格
                note_tables = self._assign_tables_to_note(
                    tables_with_positions,
                    current_pos,
                    next_level1_pos
                )

                text_content = self._extract_note_text(page, note_info, next_level1_pos)

                note = {
                    'number': note_info.get('number'),
                    'level': note_info.get('level'),
                    'title': note_info.get('title'),
                    'full_title': note_info.get('full_title'),
                    'page_num': note_info.get('page_num'),
                    'content': {
                        'text': text_content,
                        'tables': note_tables,
                        'table_count': len(note_tables)
                    },
                    'has_table': len(note_tables) > 0,
                    'is_complete': True
                }
                result_notes.append(note)

        return result_notes

    def _find_title_position(self, page: Any, title: str) -> float:
        """
        查找标题在页面上的Y坐标位置

        Args:
            page: PDF页面对象
            title: 标题文本

        Returns:
            float: Y坐标（从页面顶部开始，越大越靠下）
        """
        try:
            # 提取页面文本
            page_text = page.extract_text() or ""

            # 清理标题用于搜索（移除多余空格和换行）
            clean_title = ' '.join(title.split())

            # 使用pdfplumber的search方法查找文本位置
            # 提取标题的关键部分用于搜索
            # 对于 "(1). 应收票据分类列示"，搜索 "(1)"
            # 对于 "4、 应收票据"，搜索 "4、"

            search_text = None
            if title.startswith('(') or title.startswith('（'):
                # 二级标题，提取括号部分
                # 例如: "(1). 应收票据分类列示" -> "(1)"
                end_paren = title.find(')') if ')'  in title else title.find('）')
                if end_paren > 0:
                    search_text = title[:end_paren+1]
            else:
                # 一级标题，提取编号部分
                # 例如: "4、 应收票据" -> "4、"
                parts = title.split()
                if parts:
                    search_text = parts[0]

            if not search_text:
                search_text = title[:10]  # 使用前10个字符

            # 遍历页面的words来查找标题位置
            words = page.extract_words()
            for word in words:
                word_text = word['text']
                # 检查是否匹配搜索文本
                if search_text in word_text:
                    # 返回单词的顶部Y坐标
                    logger.debug(f"找到标题 '{title[:30]}' 在位置 {word['top']:.1f}")
                    return word['top']

            # 如果还是没找到，尝试在文本中查找
            if clean_title in page_text:
                # 估算位置
                lines = page_text.split('\n')
                page_height = page.height
                line_height = page_height / max(len(lines), 1)

                for i, line in enumerate(lines):
                    if search_text in line or clean_title in line:
                        estimated_pos = i * line_height
                        logger.debug(f"估算标题 '{title[:30]}' 位置为 {estimated_pos:.1f}")
                        return estimated_pos

            logger.warning(f"未找到标题位置: {title}")
            return 0

        except Exception as e:
            logger.error(f"查找标题位置失败: {e}")
            return 0

    def _extract_tables_with_positions(self, page: Any) -> List[Dict[str, Any]]:
        """
        提取页面上所有表格及其位置信息

        Args:
            page: PDF页面对象

        Returns:
            List[Dict[str, Any]]: 表格列表，每个包含data和position
        """
        tables_with_pos = []

        try:
            # 使用pdfplumber的find_tables获取表格对象
            table_objects = page.find_tables()

            for table_obj in table_objects:
                # 提取表格数据
                table_data = table_obj.extract()

                # 获取表格的边界框
                bbox = table_obj.bbox  # (x0, top, x1, bottom)

                tables_with_pos.append({
                    'data': table_data,
                    'top': bbox[1],  # 表格顶部Y坐标
                    'bottom': bbox[3]  # 表格底部Y坐标
                })

            logger.debug(f"页面上找到 {len(tables_with_pos)} 个表格")

        except Exception as e:
            logger.error(f"提取表格位置失败: {e}")

        return tables_with_pos

    def _assign_tables_to_note(
        self,
        tables_with_positions: List[Dict[str, Any]],
        note_position: float,
        next_note_position: Optional[float]
    ) -> List[List]:
        """
        根据位置将表格分配给注释

        Args:
            tables_with_positions: 表格及其位置信息
            note_position: 当前注释的Y坐标
            next_note_position: 下一个注释的Y坐标（如果存在）

        Returns:
            List[List]: 属于当前注释的表格数据列表
        """
        assigned_tables = []

        for table_info in tables_with_positions:
            table_top = table_info['top']
            table_bottom = table_info['bottom']

            # 表格必须在当前注释之后
            if table_top < note_position:
                continue

            # 如果有下一个注释，表格必须在下一个注释之前
            if next_note_position is not None:
                # 表格的顶部必须在下一个注释之前
                if table_top >= next_note_position:
                    continue

            # 这个表格属于当前注释
            assigned_tables.append(table_info['data'])
            logger.debug(f"分配表格: 位置 {table_top:.1f} (注释: {note_position:.1f}, 下一个: {next_note_position})")

        return assigned_tables

    def _extract_note_text(
        self,
        page: Any,
        note_info: Dict[str, Any],
        next_note_position: Optional[float]
    ) -> str:
        """
        提取注释的文本内容

        Args:
            page: PDF页面对象
            note_info: 注释信息
            next_note_position: 下一个注释的位置

        Returns:
            str: 文本内容
        """
        try:
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

            return '\n'.join(content_lines)

        except Exception as e:
            logger.error(f"提取文本内容失败: {e}")
            return ""

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
