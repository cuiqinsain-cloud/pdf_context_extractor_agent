"""
PDF读取模块
负责PDF文件的读取和指定页面内容提取
"""
import pdfplumber
from typing import List, Dict, Optional, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFReader:
    """PDF文件读取器"""

    def __init__(self, pdf_path: str):
        """
        初始化PDF读取器

        Args:
            pdf_path (str): PDF文件路径
        """
        self.pdf_path = pdf_path
        self.pdf = None

    def __enter__(self):
        """上下文管理器入口"""
        self.pdf = pdfplumber.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.pdf:
            self.pdf.close()

    def get_pages(self, page_range: Tuple[int, int]) -> List:
        """
        获取指定页面范围的页面对象

        Args:
            page_range (Tuple[int, int]): 页面范围 (start, end)，从1开始计数

        Returns:
            List: 页面对象列表
        """
        start_page, end_page = page_range
        if not self.pdf:
            raise RuntimeError("PDF未打开，请在with语句中使用")

        # 转换为0基索引
        start_idx = start_page - 1
        end_idx = end_page - 1

        if start_idx < 0 or end_idx >= len(self.pdf.pages):
            raise ValueError(f"页面范围超出PDF总页数 {len(self.pdf.pages)}")

        logger.info(f"提取页面范围: {start_page}-{end_page}")
        return self.pdf.pages[start_idx:end_idx + 1]

    def extract_page_text(self, page_num: int) -> str:
        """
        提取单页文本内容

        Args:
            page_num (int): 页码（从1开始）

        Returns:
            str: 页面文本内容
        """
        if not self.pdf:
            raise RuntimeError("PDF未打开，请在with语句中使用")

        page_idx = page_num - 1
        if page_idx < 0 or page_idx >= len(self.pdf.pages):
            raise ValueError(f"页码 {page_num} 超出范围")

        page = self.pdf.pages[page_idx]
        return page.extract_text() or ""

    def extract_page_tables(self, page_num: int) -> List[List[List[str]]]:
        """
        提取单页表格内容

        Args:
            page_num (int): 页码（从1开始）

        Returns:
            List[List[List[str]]]: 页面表格列表
        """
        if not self.pdf:
            raise RuntimeError("PDF未打开，请在with语句中使用")

        page_idx = page_num - 1
        if page_idx < 0 or page_idx >= len(self.pdf.pages):
            raise ValueError(f"页码 {page_num} 超出范围")

        page = self.pdf.pages[page_idx]
        tables = page.extract_tables()
        return tables if tables else []

    def get_total_pages(self) -> int:
        """
        获取PDF总页数

        Returns:
            int: 总页数
        """
        if not self.pdf:
            raise RuntimeError("PDF未打开，请在with语句中使用")
        return len(self.pdf.pages)

    def get_page_info(self, page_num: int) -> Dict:
        """
        获取页面基本信息

        Args:
            page_num (int): 页码（从1开始）

        Returns:
            Dict: 页面信息
        """
        if not self.pdf:
            raise RuntimeError("PDF未打开，请在with语句中使用")

        page_idx = page_num - 1
        if page_idx < 0 or page_idx >= len(self.pdf.pages):
            raise ValueError(f"页码 {page_num} 超出范围")

        page = self.pdf.pages[page_idx]
        return {
            'page_number': page_num,
            'width': page.width,
            'height': page.height,
            'rotation': page.rotation
        }


def test_pdf_reader(pdf_path: str, page_range: Tuple[int, int]):
    """
    测试PDF读取器功能

    Args:
        pdf_path (str): PDF文件路径
        page_range (Tuple[int, int]): 测试页面范围
    """
    try:
        with PDFReader(pdf_path) as reader:
            logger.info(f"PDF总页数: {reader.get_total_pages()}")

            # 测试页面信息提取
            for page_num in range(page_range[0], page_range[1] + 1):
                info = reader.get_page_info(page_num)
                logger.info(f"页面 {page_num} 信息: {info}")

                # 测试文本提取
                text = reader.extract_page_text(page_num)
                logger.info(f"页面 {page_num} 文本长度: {len(text)}")

                # 测试表格提取
                tables = reader.extract_page_tables(page_num)
                logger.info(f"页面 {page_num} 表格数量: {len(tables)}")

    except Exception as e:
        logger.error(f"PDF读取测试失败: {e}")


if __name__ == "__main__":
    # 示例用法
    pdf_path = "tests/sample_pdfs/sample.pdf"
    test_pdf_reader(pdf_path, (126, 128))