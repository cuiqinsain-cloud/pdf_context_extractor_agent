"""
用户选择处理器
当规则匹配和 LLM 识别结果不一致时，提示用户选择
"""
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class UserChoiceHandler:
    """用户选择处理器"""

    def __init__(self, save_choices: bool = True,
                 choices_log_path: str = "logs/user_choices.json"):
        """
        初始化处理器

        Args:
            save_choices: 是否保存用户选择历史
            choices_log_path: 选择历史日志文件路径
        """
        self.save_choices = save_choices
        self.choices_log_path = Path(choices_log_path)

        # 确保日志目录存在
        if self.save_choices:
            self.choices_log_path.parent.mkdir(parents=True, exist_ok=True)

    def prompt_user_choice(self,
                          comparison: Dict[str, Any],
                          llm_confidence: float,
                          llm_reasoning: str = "") -> str:
        """
        提示用户选择

        Args:
            comparison: 对比结果
            llm_confidence: LLM置信度
            llm_reasoning: LLM分析理由

        Returns:
            str: 用户选择 ('rules' 或 'llm' 或 'skip')
        """
        header_row = comparison['header_row']
        rule_result = comparison['rule_result']
        llm_result = comparison['llm_result']
        differences = comparison['differences']

        # 显示对比信息
        print("\n" + "=" * 80)
        print("⚠️  检测到规则匹配和LLM识别结果不一致，需要人为决策")
        print("=" * 80)

        print(f"\n📋 表头行（共{len(header_row)}列）:")
        for idx, cell in enumerate(header_row):
            print(f"  列{idx}: '{cell}'")

        print(f"\n🔧 规则匹配结果（识别出{len(rule_result)}列）:")
        self._print_result(rule_result, header_row)

        print(f"\n🤖 LLM识别结果（识别出{len(llm_result)}列，置信度: {llm_confidence:.2f}）:")
        self._print_result(llm_result, header_row)

        if llm_reasoning:
            print(f"\n💡 LLM分析理由:")
            print(f"  {llm_reasoning}")

        print(f"\n❌ 差异（共{len(differences)}处）:")
        for diff in differences:
            print(f"  - {diff['description']}")

        # 提示用户选择
        print("\n" + "=" * 80)
        print("请选择使用哪个结果:")
        print("  1. 使用规则匹配结果")
        print("  2. 使用LLM识别结果")
        print("  3. 跳过此表格（不处理）")
        print("=" * 80)

        while True:
            try:
                choice = input("\n请输入选择 (1/2/3): ").strip()

                if choice == '1':
                    selected = 'rules'
                    print("✓ 已选择：使用规则匹配结果")
                    break
                elif choice == '2':
                    selected = 'llm'
                    print("✓ 已选择：使用LLM识别结果")
                    break
                elif choice == '3':
                    selected = 'skip'
                    print("✓ 已选择：跳过此表格")
                    break
                else:
                    print("❌ 无效选择，请输入 1、2 或 3")

            except (KeyboardInterrupt, EOFError):
                print("\n\n⚠️  用户中断，默认跳过此表格")
                selected = 'skip'
                break

        # 保存用户选择
        if self.save_choices:
            self._save_choice(
                header_row, rule_result, llm_result,
                llm_confidence, llm_reasoning, selected
            )

        return selected

    def _print_result(self, result: Dict[str, int], header_row: List[str]):
        """
        打印识别结果

        Args:
            result: 识别结果
            header_row: 表头行数据
        """
        if not result:
            print("  （未识别出任何列）")
            return

        for col_type, col_idx in sorted(result.items(), key=lambda x: x[1]):
            cell_value = header_row[col_idx] if col_idx < len(header_row) else 'N/A'
            print(f"  - {col_type:20s}: 列{col_idx} = '{cell_value}'")

    def _save_choice(self,
                    header_row: List[str],
                    rule_result: Dict[str, int],
                    llm_result: Dict[str, int],
                    llm_confidence: float,
                    llm_reasoning: str,
                    selected: str):
        """
        保存用户选择到日志文件

        Args:
            header_row: 表头行数据
            rule_result: 规则匹配结果
            llm_result: LLM识别结果
            llm_confidence: LLM置信度
            llm_reasoning: LLM分析理由
            selected: 用户选择
        """
        try:
            # 读取现有日志
            if self.choices_log_path.exists():
                with open(self.choices_log_path, 'r', encoding='utf-8') as f:
                    choices_log = json.load(f)
            else:
                choices_log = []

            # 添加新记录
            record = {
                'timestamp': datetime.now().isoformat(),
                'header_row': header_row,
                'rule_result': rule_result,
                'llm_result': llm_result,
                'llm_confidence': llm_confidence,
                'llm_reasoning': llm_reasoning,
                'user_choice': selected
            }
            choices_log.append(record)

            # 保存日志
            with open(self.choices_log_path, 'w', encoding='utf-8') as f:
                json.dump(choices_log, f, ensure_ascii=False, indent=2)

            logger.info(f"用户选择已保存到: {self.choices_log_path}")

        except Exception as e:
            logger.error(f"保存用户选择失败: {e}")

    def get_choice_statistics(self) -> Dict[str, Any]:
        """
        获取用户选择统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.choices_log_path.exists():
            return {
                'total': 0,
                'rules_count': 0,
                'llm_count': 0,
                'skip_count': 0
            }

        try:
            with open(self.choices_log_path, 'r', encoding='utf-8') as f:
                choices_log = json.load(f)

            total = len(choices_log)
            rules_count = sum(1 for r in choices_log if r['user_choice'] == 'rules')
            llm_count = sum(1 for r in choices_log if r['user_choice'] == 'llm')
            skip_count = sum(1 for r in choices_log if r['user_choice'] == 'skip')

            return {
                'total': total,
                'rules_count': rules_count,
                'llm_count': llm_count,
                'skip_count': skip_count,
                'rules_percentage': rules_count / total * 100 if total > 0 else 0,
                'llm_percentage': llm_count / total * 100 if total > 0 else 0,
                'skip_percentage': skip_count / total * 100 if total > 0 else 0
            }

        except Exception as e:
            logger.error(f"读取用户选择统计失败: {e}")
            return {
                'total': 0,
                'error': str(e)
            }
