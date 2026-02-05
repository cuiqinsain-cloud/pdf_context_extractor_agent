#!/usr/bin/env python3
"""
测试正则表达式匹配问题
"""
import re

# 当前的正则表达式
current_patterns = [
    r'2024年.*12月.*31日',
    r'2023年.*12月.*31日'
]

# 实际的表头文本（来自海天味业）
actual_texts = [
    '2024 年12月 31日',
    '2023 年12 月31日'
]

print("=" * 80)
print("测试当前正则表达式")
print("=" * 80)

for pattern in current_patterns:
    print(f"\n正则表达式: {pattern}")
    for text in actual_texts:
        match = re.search(pattern, text)
        print(f"  文本: '{text}' -> {'✓ 匹配' if match else '✗ 不匹配'}")

# 改进的正则表达式（允许空格）
improved_patterns = [
    r'2024\s*年.*12\s*月.*31\s*日',
    r'2023\s*年.*12\s*月.*31\s*日'
]

print("\n" + "=" * 80)
print("测试改进的正则表达式（允许空格）")
print("=" * 80)

for pattern in improved_patterns:
    print(f"\n正则表达式: {pattern}")
    for text in actual_texts:
        match = re.search(pattern, text)
        print(f"  文本: '{text}' -> {'✓ 匹配' if match else '✗ 不匹配'}")

# 测试其他常见格式
print("\n" + "=" * 80)
print("测试改进的正则表达式对其他格式的兼容性")
print("=" * 80)

other_formats = [
    '2024年12月31日',  # 无空格
    '2024年 12月 31日',  # 部分空格
    '2024年12月31日',  # 标准格式
]

pattern = r'2024\s*年.*12\s*月.*31\s*日'
print(f"\n正则表达式: {pattern}")
for text in other_formats:
    match = re.search(pattern, text)
    print(f"  文本: '{text}' -> {'✓ 匹配' if match else '✗ 不匹配'}")
